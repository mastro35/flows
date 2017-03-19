'''
FlowsManager.py
---------

Copyright 2016-2017 Davide Mastromatteo
License: Apache-2.0
'''

import logging
import pickle
import time
import datetime
import asyncio
import argparse

import zmq

from flows import Global
from flows import ConfigManager
from flows import FlowsLogger
from flows import MessageDispatcher

from flows.Actions.Action import Action

__author__ = "Davide Mastromatteo"
__copyright__ = "Copyright 2016, Davide Mastromatteo"
__credits__ = [""]
__license__ = "Apache-2.0"
__version__ = Global.VERSION
__maintainer__ = "Davide Mastromatteo"
__email__ = "dave35@me.com"
__status__ = "Beta"


class FlowsManager:

    def __init__(self):
        self.actions = []
        self.subscriptions = {}

        self.fetched = 0
        self.isrunning = False

        self.last_queue_check_count = 0
        self.last_queue_check_date = datetime.datetime.now()

        Global.LOGGER_INSTANCE = FlowsLogger.FlowsLogger.default_instance()
        Global.LOGGER = FlowsLogger.FlowsLogger.default_instance().get_logger()
        Global.CONFIG_MANAGER = ConfigManager.ConfigManager.default_instance()
        Global.CONFIG_MANAGER.read_configuration()

        args = self._parse_input_parameters()
        self._set_command_line_arguments(args)

        Global.MESSAGE_DISPATCHER = MessageDispatcher.MessageDispatcher.default_instance()

        Global.LOGGER.debug("Initializing the message dispatcher")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(
            Global.CONFIG_MANAGER.subscriber_socket_address)
        self.socket.setsockopt(zmq.SUBSCRIBE, bytes('*', 'utf-8'))

    def _set_command_line_arguments(self, args):
        Global.CONFIG_MANAGER.recipes = (args.FILENAME)

        if args.VERBOSE:
            Global.CONFIG_MANAGER.log_level = logging.DEBUG
            Global.LOGGER_INSTANCE.reconfigure_log_level()

    def start(self):
        """ Start all the processes """
        self._start_actions()
        self._start_message_fetcher()
        # Global.MESSAGE_FETCHER.start()

    def stop(self):
        """ Stop all the processes """
        # Global.MESSAGE_FETCHER.stop()
        self._stop_actions()
        self.isrunning = False

    def restart(self):
        """ Restart all the processes """
        Global.LOGGER.info("restarting flows")
        self._stop_actions()    # stop the old actions
        self.actions = []       # clear the action list
        self._start_actions()   # start the configured actions

    def _start_actions(self):
        Global.LOGGER.info("starting actions")

        for recipe in Global.CONFIG_MANAGER.recipes:
            Global.CONFIG_MANAGER.read_recipe(recipe)

        list(map(lambda section: self._start_action_for_section(
            section), Global.CONFIG_MANAGER.sections))

    def _start_action_for_section(self, section):
        if section == "configuration":
            return

        Global.LOGGER.debug("starting actions for section " + section)

        # read the configuration of the action
        action_configuration = Global.CONFIG_MANAGER.sections[
            section]

        if len(action_configuration) > 0:
            action_type = None

            if "type" in action_configuration:
                action_type = action_configuration["type"]

            new_managed_input = []
            action_input = None

            if "input" in action_configuration:
                action_input = action_configuration["input"]
                new_managed_input = (item.strip()
                                     for item in action_input.split(","))

            my_action = Action.create_action_for_code(action_type,
                                                      section,
                                                      action_configuration,
                                                      list(new_managed_input))

            if my_action is not None:
                self.actions.append(my_action)
                for my_input in my_action.monitored_input:
                    self.subscriptions.setdefault(
                        my_input, []).append(my_action)
            else:
                Global.LOGGER.warn(
                    "Can't find a type for action " + section)
        else:
            Global.LOGGER.warn(
                "Unable to find the configuration for section " + section)

    def _stop_actions(self):
        """ Stop all the actions """
        Global.LOGGER.info("stopping actions")

        list(map(lambda x: x.stop(), self.actions))

        Global.LOGGER.info("actions stopped")
        time.sleep(1)

    # def _process_system_message(self, msg):
    #     # DAV - TO BE MOVED!!!
    #     if self.dispatched % 1000 == 0:
    #         Global.LOGGER.debug(str.format("zmq has dispatched {0} messages",
    #                                         self.dispatched))
    #         self.adapt_sleep_interval()

    def _perform_system_check(self):
        now = datetime.datetime.now()
        sent = Global.MESSAGE_DISPATCHER.dispatched
        received = self.fetched
        queue_length = sent - received

        # if sent - self.last_queue_check_count > 100:
        #     print ("sent "+ str(sent))
        #     print ("received "+ str(received))
        #     print ("queue "+ str(queue_length))

        # if we are accumulating messages, or we have processed at least 5000 messages
        # since last check, we need to speed up the process
        if (sent - self.last_queue_check_count > Global.CONFIG_MANAGER.messages_dispatched_for_system_check) or (
            queue_length > Global.CONFIG_MANAGER.queue_length_for_system_check and (
                now - self.last_queue_check_date).total_seconds() > Global.CONFIG_MANAGER.seconds_between_queue_check):
            Global.LOGGER.info(
                "calling the sleep interval adjust function. Queue length = " + str(queue_length))
            self._adapt_sleep_interval(sent, received, queue_length, now)

    def _deliver_message(self, msg):
        """
        Deliver the message to the subscripted actions
        """

        # if msg.sender = "__SYSTEM__":
        #     self._process_system_message(msg)
        #     return

        my_subscribed_actions = self.subscriptions.get(msg.sender, [])
        for action in my_subscribed_actions:
            action.on_input_received(msg)

    def _fetch_messages(self):
        """
        Get an input message from the socket
        """
        try:
            [_, msg] = self.socket.recv_multipart(
                flags=zmq.NOBLOCK)
            self.fetched = self.fetched + 1
            obj = pickle.loads(msg)
            self._deliver_message(obj)
            return obj

        except Exception as new_exception:
            if new_exception.errno == zmq.EAGAIN:
                return None
            else:
                raise new_exception

    async def message_fetcher_coroutine(self, loop):
        Global.LOGGER.debug(
            'registering callbacks for message fetcher coroutine')
        self.isrunning = True
        while self.isrunning:
            loop.call_soon(self._fetch_messages)
            loop.call_soon(self._perform_system_check)
            await asyncio.sleep(Global.CONFIG_MANAGER.message_fetcher_sleep_interval)

        Global.LOGGER.debug('message fetcher stopped')

    def _start_message_fetcher(self):
        event_loop = asyncio.get_event_loop()
        try:
            Global.LOGGER.debug(
                'entering event loop for message fetcher coroutine')
            event_loop.run_until_complete(
                self.message_fetcher_coroutine(event_loop))
        finally:
            Global.LOGGER.debug('closing the event loop')
            event_loop.close()

    def _adapt_sleep_interval(self, sent, received, queue, now):
        '''adapt sleep time based on the number of the messages in queue'''

        Global.LOGGER.debug("Adjusting sleep interval")

        dispatched_since_last_check = sent - self.last_queue_check_count
        seconds_since_last_check = (
            now - self.last_queue_check_date).total_seconds()

        Global.LOGGER.info(
            str(dispatched_since_last_check) + " in " + str(seconds_since_last_check))
        sleep_time = (seconds_since_last_check /
                      (dispatched_since_last_check + queue + 1)) * 0.75

        if sleep_time > 0.5:
            sleep_time = 0.5

        if sleep_time < 0.0001:
            sleep_time = 0.0001

        self.last_queue_check_date = now
        self.last_queue_check_count = sent

        Global.CONFIG_MANAGER.message_fetcher_sleep_interval = sleep_time
        Global.LOGGER.info(str.format("New sleep_interval = {0} ",
                                            sleep_time))


    def _parse_input_parameters(self):
        """Set the configuration for the Logger"""

        parser = argparse.ArgumentParser(
            description='A workflow engine for Pythonistas', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('FILENAME', nargs='+',
                            help='name of the recipe file(s)')
        parser.add_argument('-v', '--VERBOSE', action='store_true',
                            help='enable verbose output')
        parser.add_argument('-V', '--VERSION',
                            action="version", version=__version__)

        args = parser.parse_args()
        return args

