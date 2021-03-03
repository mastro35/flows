#!/usr/bin/env python3

"""
FlowsWorker.py
---------

Copyright 2016-2017 Davide Mastromatteo
License: Apache-2.0
"""

import asyncio
import json
import threading
from threading import Thread

import zmq

import global_module as Global
import message_dispatcher
from Actions.action import Basic_Action

__author__ = "Davide Mastromatteo"
__copyright__ = "Copyright 2016, Davide Mastromatteo"
__credits__ = [""]
__license__ = "Apache-2.0"
__version__ = Global.VERSION
__maintainer__ = "Davide Mastromatteo"
__email__ = "mastro35@gmail.com"
__status__ = "Production/Stable"


class FlowsWorker(Thread):
    """Class that represent a single worker thread"""
    _instance_lock = threading.Lock()

    def __init__(self):
        super().__init__()

        # Set the worker as a daemon
        self.daemon = True
        self.is_running = True

        # self.MESSAGE_DISPATCHER = MessageDispatcher.MessageDispatcher.default_instance()
        self.message_dispatcher = message_dispatcher.MessageDispatcher.default_instance()

        self.actions: [Basic_Action] = []
        self.subscriptions: {} = {}
        self.fetched = 0

        self._start_actions()

        # Define the PULL socket
        self.receivesocket = Global.ZMQ_CONTEXT.socket(zmq.PULL) # pylint: disable=E1101
        self.receivesocket.connect("tcp://localhost:5557")

        self.loop = asyncio.new_event_loop()
        # Start the worker (as a thread, the run method will be executed)
        self.start()

    def run(self):
        """
        Starts the worker
        """
        # self._start_message_fetcher()
        Global.LOGGER.debug(f"WORK: worker is running...")

        # Start the asyncronous message fetcher
        self.loop.run_until_complete(self._start_async_message_fetcher())

    def stop(self):
        """
        Stop the worker
        """
        self._stop_actions()
        self.is_running = False
#        self.loop.close()

    async def _start_async_message_fetcher(self):
        """
        Start the message fetcher (called from coroutine)
        """
        Global.LOGGER.info('WORK: starting the message fetcher')
        while self.is_running:
            asyncio.ensure_future(self._fetch_messages(), loop=self.loop)
            await asyncio.sleep(Global.CONFIG_MANAGER.message_fetcher_sleep_interval)

    async def _fetch_messages(self):
        """
        Get an input message from the socket
        """
        try:
            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug("WORK: trying fetching messages")

            jmsg = self.receivesocket.recv_string(flags=zmq.NOBLOCK) # pylint: disable=E1101
            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug("WORK: this worker has fetched a new message")

            self.fetched = self.fetched + 1
            msg = json.loads(jmsg)
            self._deliver_message_to_actions(msg)
            return
        except zmq.error.Again:
            return None
        except Exception as new_exception:
            Global.LOGGER.error(new_exception)
            raise new_exception

    def _deliver_message_to_actions(self, msg):
        """
        Deliver the message to the subscripted actions
        """
        my_subscribed_actions = self.subscriptions.get(msg["sender"], [])
        for action in my_subscribed_actions:
            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug(f"WORK: delivering message to {action.name}")
            try:
                action.on_input_received(msg)
            except Exception as e:
                action.on_input_received(str(msg["message"]))

    def _start_actions(self):
        """
        Start all the actions for the recipes
        """
        Global.LOGGER.info("starting actions")

        for recipe in Global.CONFIG_MANAGER.recipes:
            Global.CONFIG_MANAGER.read_recipe(recipe)

        _ = [self._start_action_for_section(section)
             for section in Global.CONFIG_MANAGER.sections]

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

        if not action_configuration:
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

        my_action = Basic_Action.create_action_for_code(action_type,
                                                  section,
                                                  action_configuration,
                                                  self,
                                                  list(new_managed_input))

        if not my_action:
            Global.LOGGER.warn(f"WORK: can't find a type for action {section}, \
                               the action will be skipped")
            return

        if isinstance(my_action, Thread):
            Global.LOGGER.debug(f"WORK: starting action {section} as a separated thread")
            # invokes the "start" method of the Thread class in the standard library
            my_action.start()
        else:
            Global.LOGGER.debug(f"WORK: starting action {section} in asyncronous")
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(my_action.run(), loop=loop)

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

        # list(map(lambda x: x.stop(), self.actions))
        _ = [action.stop for action in self.actions]

        Global.LOGGER.info("WORK: actions stopped")
