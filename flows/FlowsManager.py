"""
FlowsManager.py
---------

Copyright 2016-2024 Davide Mastromatteo
License: GPL 2.0
"""

import argparse
import asyncio
import datetime
import logging
import json

import zmq

from flows.ConfigManager import ConfigManager
from flows.FlowsLogger import FlowsLogger
from flows.MessageDispatcher import MessageDispatcher
from flows.Actions.Action import Action

__author__: str = "Davide Mastromatteo"
__copyright__: str = "Copyright 2024, Davide Mastromatteo"
__credits__: list = [""]
__license__: str = "GPL-2.0"
__version__: str = "3.0 beta1"
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

        # For auto throttling feature
        self.last_queue_check_count = 0
        self.last_queue_check_date = datetime.datetime.now()
        self.last_stats_check_date = datetime.datetime.now()

        # Set up of other objects needed by the manager
        self.logger = FlowsLogger.default_instance().get_logger()
        self.config_manager = ConfigManager.default_instance()
        self.message_dispatcher = MessageDispatcher.default_instance()

        # Preliminary set up of the parameters and the socket
        self._set_command_line_arguments(self._parse_input_parameters())
        self._set_subscriber_socket()

    def _set_subscriber_socket(self):
        """
        Set up the SUB ZMQ socket
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(self.config_manager.subscriber_socket_address)

        # filter the multipart messages with a "*" in part 1
        self.socket.setsockopt(zmq.SUBSCRIBE, bytes("*", "utf-8"))

    def _set_command_line_arguments(self, args):
        """
        Set internal configuration variables according to
        the input parameters
        """
        self.logger.debug("setting command line arguments")

        if args.VERBOSE:
            FlowsLogger.default_instance().reconfigure_log_level(logging.INFO)
            self.logger.info("verbose mode active")

        if args.STATS > 0:
            self.logger.debug(f"stats requested every {args.STATS} seconds")
            self.config_manager.show_stats = True
            self.config_manager.stats_timeout = args.STATS

        # if args.INTERVAL > 0:
        #     self.logger.debug(f"setting sleep interval to {args.INTERVAL} milliseconds")
        #     self.config_manager.sleep_interval = float(args.INTERVAL) / 1000

        if args.TRACE:
            self.config_manager.tracing_mode = True
            FlowsLogger.default_instance().reconfigure_log_level(logging.DEBUG)
            self.logger.debug("tracing mode active")

        # if args.MESSAGEINTERVAL is not None and args.MESSAGEINTERVAL > 0:
        #     self.logger.debug(
        #         f"setting message fetcher sleep interval to {args.MESSAGEINTERVAL/10} milliseconds"
        #     )
        #     self.config_manager.message_fetcher_sleep_interval = (
        #         float(args.MESSAGEINTERVAL) / 10000
        #     )
        #     self.config_manager.fixed_message_fetcher_interval = True

        self.logger.debug(f"recipes to be parsed: {args.FILENAME}")
        self.config_manager.recipes = args.FILENAME

    def start(self):
        """
        Start all the processes
        """
        self.logger.info("starting the flow manager")
        self._start_actions()
        self._start_message_fetcher()
        self.logger.debug("flow manager started")

    def stop(self):
        """
        Stop all the processes
        """
        self.logger.info("stopping the flow manager")
        self._stop_actions()
        self.isrunning = False  # stop the message fetcher
        self.logger.debug("flow manager stopped")

    def restart(self):
        """
        Restart all the processes
        """
        self.logger.info("restarting the flow manager")
        self._stop_actions()  # stop the old actions
        self.actions = []  # clear the action list
        self._start_actions()  # start the configured actions
        self.logger.debug("flow manager restarted")

    def _start_actions(self):
        """
        Start all the actions for the recipes
        """
        self.logger.info("starting actions")

        for recipe in self.config_manager.recipes:
            self.config_manager.read_recipe(recipe)

        list(
            map(
                lambda section: self._start_action_for_section(section),
                self.config_manager.sections,
            )
        )

    def _start_action_for_section(self, section):
        """
        Start all the actions for a particular section
        """
        if section == "configuration":
            return

        self.logger.debug("starting actions for section " + section)

        # read the configuration of the action
        action_configuration = self.config_manager.sections[section]

        if len(action_configuration) == 0:
            self.logger.warn(f"section {section} has no configuration, skipping")
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
            self.logger.warn(
                f"can't find a type for action {section}, the action will be skipped"
            )
            return

        self.actions.append(my_action)

        self.logger.debug("updating the subscriptions table")
        for my_input in my_action.monitored_input:
            self.subscriptions.setdefault(my_input, []).append(my_action)

    def _stop_actions(self):
        """
        Stop all the actions
        """
        self.logger.info("stopping actions")

        list(map(lambda x: x.stop(), self.actions))

        self.logger.info("actions stopped")

    # def _perform_system_check(self):
    #     """
    #     Perform a system check to define if we need to throttle to handle
    #     all the incoming messages
    #     """
    #     if self.config_manager.tracing_mode:
    #         self.logger.debug("performing a system check")

    #     now = datetime.datetime.now()
    #     sent = self.message_dispatcher.dispatched
    #     received = self.fetched
    #     queue_length = sent - received
    #     message_sleep_interval = self.config_manager.message_fetcher_sleep_interval

    #     if self.config_manager.show_stats:
    #         if (
    #             now - self.last_stats_check_date
    #         ).total_seconds() > self.config_manager.stats_timeout:
    #             self.last_stats_check_date = now
    #             stats_string = f"showing stats\n--- [STATS] ---\nMessage Sent: {sent}\nMessage Received: {received}\nMessage Sleep Interval = {message_sleep_interval}\nQueue length = {queue_length}\n--- [ END ] ---"
    #             self.logger.info(stats_string)

    #     # if we are accumulating messages, or we have processed at least 5000 messages
    #     # since last check, we need to speed up the process
    #     messages_limit_reached = (
    #         sent - self.last_queue_check_count
    #         > self.config_manager.messages_dispatched_for_system_check
    #     )
    #     queue_limit_reached = (
    #         queue_length > self.config_manager.queue_length_for_system_check
    #     )
    #     time_limit_since_last_check_is_over = (
    #         now - self.last_queue_check_date
    #     ).total_seconds() > self.config_manager.seconds_between_queue_check

    #     if not self.config_manager.fixed_message_fetcher_interval:
    #         if (messages_limit_reached) or (
    #             queue_limit_reached and time_limit_since_last_check_is_over
    #         ):
    #             cause = (
    #                 "messages limit reached"
    #                 if messages_limit_reached
    #                 else "queue limit reached"
    #             )
    #             self.logger.debug(f"triggering the throttle function due to {cause}")
    #             # self._adapt_sleep_interval(sent, received, queue_length, now)

    def _deliver_message(self, msg):
        """
        Deliver the message to the subscripted actions
        """
        my_subscribed_actions = self.subscriptions.get(msg["sender"], [])
        for action in my_subscribed_actions:
            if self.config_manager.tracing_mode:
                self.logger.debug(f"delivering message to {action.name}")

            action.on_input_received(msg)

    def _fetch_messages(self):
        """
        Get an input message from the socket
        """
        try:
            [_, msg] = self.socket.recv_multipart(flags=zmq.NOBLOCK)
            if self.config_manager.tracing_mode:
                self.logger.debug("fetched a new message")

            self.fetched = self.fetched + 1
            # obj = pickle.loads(msg)
            obj = json.loads(msg)
            self._deliver_message(obj)
            return obj
        except zmq.error.Again:
            return None
        except Exception as new_exception:
            self.logger.error(new_exception)
            raise new_exception

    async def message_fetcher_coroutine(self, loop):
        """
        Register callback for message fetcher coroutines
        """
        self.logger.debug("registering callbacks for message fetcher coroutine")
        self.isrunning = True
        while self.isrunning:
            loop.call_soon(self._fetch_messages)
            # loop.call_soon(self._perform_system_check)
            await asyncio.sleep(self.config_manager.message_fetcher_sleep_interval)

        self.logger.debug("message fetcher stopped")

    def _start_message_fetcher(self):
        """
        Start the message fetcher (called from coroutine)
        """
        self.logger.debug("starting the message fetcher")
        event_loop = asyncio.get_event_loop()
        try:
            self.logger.debug("entering event loop for message fetcher coroutine")
            event_loop.run_until_complete(self.message_fetcher_coroutine(event_loop))
        finally:
            self.logger.debug("closing the event loop")
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
        self.logger.debug("define and parsing command line arguments")
        parser = argparse.ArgumentParser(
            description="A workflow engine for Pythonistas",
            formatter_class=argparse.RawTextHelpFormatter,
        )
        parser.add_argument("FILENAME", nargs="+", help="name of the recipe file(s)")

        # parser.add_argument(
        #     "-i",
        #     "--INTERVAL",
        #     type=int,
        #     default=500,
        #     metavar=("MS"),
        #     help="perform a cycle each [MS] milliseconds. (default = 500)",
        # )

        # parser.add_argument(
        #     "-m",
        #     "--MESSAGEINTERVAL",
        #     type=int,
        #     metavar=("X"),
        #     help="dequeue a message each [X] tenth of milliseconds. (default = auto)",
        # )

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
