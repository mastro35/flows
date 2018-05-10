#!/usr/bin/env python3

"""
FlowsWorker.py
---------

Copyright 2016-2017 Davide Mastromatteo
License: Apache-2.0
"""

import asyncio
import pickle
import threading
from threading import Thread

import zmq

from flows import Global
from flows import MessageDispatcher
from flows.Actions.Action import Action

__author__ = "Davide Mastromatteo"
__copyright__ = "Copyright 2016, Davide Mastromatteo"
__credits__ = [""]
__license__ = "Apache-2.0"
__version__ = Global.VERSION
__maintainer__ = "Davide Mastromatteo"
__email__ = "dave35@me.com"
__status__ = "Production/Stable"


class FlowsWorker(Thread):
    _instance_lock = threading.Lock()

    def __init__(self):
        super().__init__()

        # Set the worker as a daemon
        self.daemon = True
        self.isrunning = False

        # self.MESSAGE_DISPATCHER = MessageDispatcher.MessageDispatcher.default_instance()
        self.MESSAGE_DISPATCHER = MessageDispatcher.MessageDispatcher.default_instance()

        self.actions = []
        self.subscriptions = {}
        self.fetched = 0

        self._start_actions()

        # Define the PULL socket
        self.receivesocket = Global.ZMQ_CONTEXT.socket(zmq.PULL)
        self.receivesocket.connect("tcp://localhost:5557")

        # Start the action (as a thread, the run method will be executed)
        self.start()

    def run(self):
        """
        Start the action
        """

        self._start_message_fetcher()

        Global.LOGGER.debug(f"WORK: worker is running...")

    def stop(self):
        self._stop_actions()
        self.isrunning = False

    def _start_message_fetcher(self):
        """
        Start the message fetcher (called from coroutine)
        """
        Global.LOGGER.info('WORK: starting the message fetcher')
        event_loop = asyncio.new_event_loop()

        try:
            Global.LOGGER.debug('WORK: entering event loop for message fetcher coroutine')
            event_loop.run_until_complete(self.message_fetcher_coroutine(event_loop))
        finally:
            Global.LOGGER.debug('WORK: closing the event loop')
            event_loop.close()

    async def message_fetcher_coroutine(self, loop):
        """
        Register callback for message fetcher coroutines
        """
        Global.LOGGER.debug('WORK: registering callbacks for message fetcher coroutine')
        self.isrunning = True
        while self.isrunning:
            loop.call_soon(self._fetch_messages)
            #            loop.call_soon(self._perform_system_check)
            await asyncio.sleep(Global.CONFIG_MANAGER.message_fetcher_sleep_interval)

        Global.LOGGER.debug('WORK: message fetcher stopped')

    def _fetch_messages(self):
        """
        Get an input message from the socket
        """
        try:
            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug("WORK: trying fetching messages")

            # [_, msg] = self.socket.recv_multipart(flags=zmq.NOBLOCK)
            msg = self.receivesocket.recv(flags=zmq.NOBLOCK)
            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug("WORK: this worker has fetched a new message")

            self.fetched = self.fetched + 1
            obj = pickle.loads(msg)
            self._deliver_message_to_actions(obj)
            return obj
        except zmq.error.Again:
            return None
        except Exception as new_exception:
            Global.LOGGER.error(new_exception)
            raise new_exception

    def _deliver_message_to_actions(self, msg):
        """
        Deliver the message to the subscripted actions
        """
        my_subscribed_actions = self.subscriptions.get(msg.sender, [])
        for action in my_subscribed_actions:
            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug(f"WORK: delivering message to {action.name}")
            action.on_input_received(msg)

    def _start_actions(self):
        """
        Start all the actions for the recipes
        """
        Global.LOGGER.info("starting actions")

        for recipe in Global.CONFIG_MANAGER.recipes:
            Global.CONFIG_MANAGER.read_recipe(recipe)

        list(map(lambda section: self._start_action_for_section(
            section), Global.CONFIG_MANAGER.sections))

    def _start_action_for_section(self, section):
        """
        Start all the actions for a particular section
        """
        if section == "configuration":
            return

        Global.LOGGER.debug("WORK: starting actions for section " + section)

        # read the configuration of the action
        action_configuration = Global.CONFIG_MANAGER.sections[
            section]

        if len(action_configuration) == 0:
            Global.LOGGER.warn(f"WORK: section {section} has no configuration, skipping")
            return

        action_type = None
        # action_input = None
        new_managed_input = []

        if "type" in action_configuration:
            action_type = action_configuration["type"]

        if "input" in action_configuration:
            action_input = action_configuration["input"]
            new_managed_input = (item.strip()
                                 for item in action_input.split(","))

        my_action = Action.create_action_for_code(action_type,
                                                  section,
                                                  action_configuration,
                                                  self,
                                                  list(new_managed_input))

        if not my_action:
            Global.LOGGER.warn(f"WORK: can't find a type for action {section}, the action will be skipped")
            return

        self.actions.append(my_action)

        Global.LOGGER.debug("WORK: updating the subscriptions table")
        for my_input in my_action.monitored_input:
            self.subscriptions.setdefault(
                my_input, []).append(my_action)

    def _stop_actions(self):
        """
        Stop all the actions
        """
        Global.LOGGER.info("WORK: stopping actions")

        list(map(lambda x: x.stop(), self.actions))

        Global.LOGGER.info("WORK: actions stopped")
