"""
FlowsManager.py
---------

Copyright 2016-2017 Davide Mastromatteo
License: Apache-2.0
"""

import argparse
import asyncio
import datetime
import logging
import json

# import pickle
import zmq

from flows import ConfigManager
from flows import FlowsLogger
from flows import MessageDispatcher
from flows.Actions.Action import Action

__author__: str = "Davide Mastromatteo"
__copyright__: str = "Copyright 2016, Davide Mastromatteo"
__credits__: list = [""]
__license__: str = "Apache-2.0"
__version__: str = "1.2.5"
__maintainer__: str = "Davide Mastromatteo"
__email__: str = "mastro35@gmail.com"
__status__: str = "Production/Stable"


class FlowsManager:
    """
    FlowsManager: the mail class that create all the others object
    to run a Flow
    """

    def __init__(self) -> None:
        """
        Default Contrsuctor of the FlowsManager class
        """
        self.actions = []
        self.subscriptions = {}

        self.fetched = 0
        self.isrunning = False

        self.last_queue_check_count = 0
        self.last_queue_check_date = datetime.datetime.now()
        self.last_stats_check_date = datetime.datetime.now()

        self.LOGGER_INSTANCE = FlowsLogger.FlowsLogger.default_instance()
        self.LOGGER = FlowsLogger.FlowsLogger.default_instance().get_logger()
        self.CONFIG_MANAGER = ConfigManager.ConfigManager.default_instance()

        args = self._parse_input_parameters()
        self._set_command_line_arguments(args)

        self.MESSAGE_DISPATCHER = MessageDispatcher.MessageDispatcher.default_instance()

        self.LOGGER.debug("Initializing the message dispatcher")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(self.CONFIG_MANAGER.subscriber_socket_address)
        self.socket.setsockopt(zmq.SUBSCRIBE, bytes("*", "utf-8"))

    def _set_command_line_arguments(self, args):
        """
        Set internal configuration variables according to
        the input parameters
        """
        self.LOGGER.debug("setting command line arguments")

        if args.VERBOSE:
            self.LOGGER.debug("verbose mode active")
            self.CONFIG_MANAGER.log_level = logging.DEBUG
            self.LOGGER_INSTANCE.reconfigure_log_level()

        if args.STATS > 0:
            self.LOGGER.debug(f"stats requested every {args.STATS} seconds")
            self.CONFIG_MANAGER.show_stats = True
            self.CONFIG_MANAGER.stats_timeout = args.STATS

        if args.INTERVAL > 0:
            self.LOGGER.debug(f"setting sleep interval to {args.INTERVAL} milliseconds")
            self.CONFIG_MANAGER.sleep_interval = float(args.INTERVAL) / 1000

        if args.TRACE:
            self.LOGGER.debug("tracing mode active")
            self.CONFIG_MANAGER.tracing_mode = True
            self.CONFIG_MANAGER.log_level = logging.DEBUG
            self.LOGGER_INSTANCE.reconfigure_log_level()

        if args.MESSAGEINTERVAL is not None and args.MESSAGEINTERVAL > 0:
            self.LOGGER.debug(
                f"setting message fetcher sleep interval to {args.MESSAGEINTERVAL/10} milliseconds"
            )
            self.CONFIG_MANAGER.message_fetcher_sleep_interval = (
                float(args.MESSAGEINTERVAL) / 10000
            )
            self.CONFIG_MANAGER.fixed_message_fetcher_interval = True

        self.LOGGER.debug(f"recipes to be parsed: {args.FILENAME}")
        self.CONFIG_MANAGER.recipes = args.FILENAME

    def start(self):
        """
        Start all the processes
        """
        self.LOGGER.info("starting the flow manager")
        self._start_actions()
        self._start_message_fetcher()
        self.LOGGER.debug("flow manager started")

    def stop(self):
        """
        Stop all the processes
        """
        self.LOGGER.info("stopping the flow manager")
        self._stop_actions()
        self.isrunning = False
        self.LOGGER.debug("flow manager stopped")

    def restart(self):
        """
        Restart all the processes
        """
        self.LOGGER.info("restarting the flow manager")
        self._stop_actions()  # stop the old actions
        self.actions = []  # clear the action list
        self._start_actions()  # start the configured actions
        self.LOGGER.debug("flow manager restarted")

    def _start_actions(self):
        """
        Start all the actions for the recipes
        """
        self.LOGGER.info("starting actions")

        for recipe in self.CONFIG_MANAGER.recipes:
            self.CONFIG_MANAGER.read_recipe(recipe)

        list(
            map(
                lambda section: self._start_action_for_section(section),
                self.CONFIG_MANAGER.sections,
            )
        )

    def _start_action_for_section(self, section):
        """
        Start all the actions for a particular section
        """
        if section == "configuration":
            return

        self.LOGGER.debug("starting actions for section " + section)

        # read the configuration of the action
        action_configuration = self.CONFIG_MANAGER.sections[section]

        if len(action_configuration) == 0:
            self.LOGGER.warn(f"section {section} has no configuration, skipping")
            return

        action_type = None
        # action_input = None
        new_managed_input = []

        if "type" in action_configuration:
            action_type = action_configuration["type"]

        if "input" in action_configuration:
            action_input = action_configuration["input"]
            new_managed_input = (item.strip() for item in action_input.split(","))

        my_action = Action.create_action_for_code(
            action_type, section, action_configuration, list(new_managed_input)
        )

        if not my_action:
            self.LOGGER.warn(
                f"can't find a type for action {section}, the action will be skipped"
            )
            return

        self.actions.append(my_action)

        self.LOGGER.debug("updating the subscriptions table")
        for my_input in my_action.monitored_input:
            self.subscriptions.setdefault(my_input, []).append(my_action)

    def _stop_actions(self):
        """
        Stop all the actions
        """
        self.LOGGER.info("stopping actions")

        list(map(lambda x: x.stop(), self.actions))

        self.LOGGER.info("actions stopped")

    # def _perform_system_check(self):
    #     """
    #     Perform a system check to define if we need to throttle to handle
    #     all the incoming messages
    #     """
    #     if self.CONFIG_MANAGER.tracing_mode:
    #         self.LOGGER.debug("performing a system check")

    #     now = datetime.datetime.now()
    #     sent = self.MESSAGE_DISPATCHER.dispatched
    #     received = self.fetched
    #     queue_length = sent - received
    #     message_sleep_interval = self.CONFIG_MANAGER.message_fetcher_sleep_interval

    #     if self.CONFIG_MANAGER.show_stats:
    #         if (
    #             now - self.last_stats_check_date
    #         ).total_seconds() > self.CONFIG_MANAGER.stats_timeout:
    #             self.last_stats_check_date = now
    #             stats_string = f"showing stats\n--- [STATS] ---\nMessage Sent: {sent}\nMessage Received: {received}\nMessage Sleep Interval = {message_sleep_interval}\nQueue length = {queue_length}\n--- [ END ] ---"
    #             self.LOGGER.info(stats_string)

    #     # if we are accumulating messages, or we have processed at least 5000 messages
    #     # since last check, we need to speed up the process
    #     messages_limit_reached = (
    #         sent - self.last_queue_check_count
    #         > self.CONFIG_MANAGER.messages_dispatched_for_system_check
    #     )
    #     queue_limit_reached = (
    #         queue_length > self.CONFIG_MANAGER.queue_length_for_system_check
    #     )
    #     time_limit_since_last_check_is_over = (
    #         now - self.last_queue_check_date
    #     ).total_seconds() > self.CONFIG_MANAGER.seconds_between_queue_check

    #     if not self.CONFIG_MANAGER.fixed_message_fetcher_interval:
    #         if (messages_limit_reached) or (
    #             queue_limit_reached and time_limit_since_last_check_is_over
    #         ):
    #             cause = (
    #                 "messages limit reached"
    #                 if messages_limit_reached
    #                 else "queue limit reached"
    #             )
    #             self.LOGGER.debug(f"triggering the throttle function due to {cause}")
    #             # self._adapt_sleep_interval(sent, received, queue_length, now)
    def _deliver_message(self, msg):
        """
        Deliver the message to the subscripted actions
        """
        my_subscribed_actions = self.subscriptions.get(msg["sender"], [])
        for action in my_subscribed_actions:
            if self.CONFIG_MANAGER.tracing_mode:
                self.LOGGER.debug(f"delivering message to {action.name}")

            action.on_input_received(msg)

    def _fetch_messages(self):
        """
        Get an input message from the socket
        """
        try:
            [_, msg] = self.socket.recv_multipart(flags=zmq.NOBLOCK)
            if self.CONFIG_MANAGER.tracing_mode:
                self.LOGGER.debug("fetched a new message")

            self.fetched = self.fetched + 1
            # obj = pickle.loads(msg)
            obj = json.loads(msg)
            self._deliver_message(obj)
            return obj
        except zmq.error.Again:
            return None
        except Exception as new_exception:
            self.LOGGER.error(new_exception)
            raise new_exception

    async def message_fetcher_coroutine(self, loop):
        """
        Register callback for message fetcher coroutines
        """
        self.LOGGER.debug("registering callbacks for message fetcher coroutine")
        self.isrunning = True
        while self.isrunning:
            loop.call_soon(self._fetch_messages)
            # loop.call_soon(self._perform_system_check)
            await asyncio.sleep(self.CONFIG_MANAGER.message_fetcher_sleep_interval)

        self.LOGGER.debug("message fetcher stopped")

    def _start_message_fetcher(self):
        """
        Start the message fetcher (called from coroutine)
        """
        self.LOGGER.debug("starting the message fetcher")
        event_loop = asyncio.get_event_loop()
        try:
            self.LOGGER.debug("entering event loop for message fetcher coroutine")
            event_loop.run_until_complete(self.message_fetcher_coroutine(event_loop))
        finally:
            self.LOGGER.debug("closing the event loop")
            event_loop.close()

    # def _adapt_sleep_interval(self, sent, received, queue, now):
    #     """
    #     Adapt sleep time based on the number of the messages in queue
    #     """
    #     self.LOGGER.debug("adjusting sleep interval")

    #     dispatched_since_last_check = sent - self.last_queue_check_count
    #     seconds_since_last_check = (now - self.last_queue_check_date).total_seconds()

    #     self.LOGGER.debug(
    #         str(dispatched_since_last_check)
    #         + " dispatched in the last "
    #         + str(seconds_since_last_check)
    #     )
    #     sleep_time = (
    #         seconds_since_last_check / (dispatched_since_last_check + queue + 1)
    #     ) * 0.75

    #     if sleep_time > 0.5:
    #         sleep_time = 0.5

    #     if sleep_time < 0.0001:
    #         sleep_time = 0.0001

    #     self.last_queue_check_date = now
    #     self.last_queue_check_count = sent

    #     self.CONFIG_MANAGER.message_fetcher_sleep_interval = sleep_time

    #     sleep_interval_log_string = f"new sleep_interval = {sleep_time}"
    #     self.LOGGER.debug(sleep_interval_log_string)

    #     if self.CONFIG_MANAGER.show_stats:
    #         self.LOGGER.info(sleep_interval_log_string)

    def _parse_input_parameters(self):
        """
        Set the configuration for the Logger
        """
        self.LOGGER.debug("define and parsing command line arguments")
        parser = argparse.ArgumentParser(
            description="A workflow engine for Pythonistas",
            formatter_class=argparse.RawTextHelpFormatter,
        )
        parser.add_argument("FILENAME", nargs="+", help="name of the recipe file(s)")
        parser.add_argument(
            "-i",
            "--INTERVAL",
            type=int,
            default=500,
            metavar=("MS"),
            help="perform a cycle each [MS] milliseconds. (default = 500)",
        )

        parser.add_argument(
            "-m",
            "--MESSAGEINTERVAL",
            type=int,
            metavar=("X"),
            help="dequeue a message each [X] tenth of milliseconds. (default = auto)",
        )
        parser.add_argument(
            "-s",
            "--STATS",
            type=int,
            default=0,
            metavar=("SEC"),
            help="show stats each [SEC] seconds. (default = NO STATS)",
        )
        parser.add_argument(
            "-t",
            "--TRACE",
            action="store_true",
            help="enable super verbose output, only useful for tracing",
        )
        parser.add_argument(
            "-v", "--VERBOSE", action="store_true", help="enable verbose output"
        )
        parser.add_argument("-V", "--VERSION", action="version", version=__version__)

        args = parser.parse_args()
        return args
