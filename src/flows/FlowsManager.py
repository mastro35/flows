"""
FlowsManager.py
---------

Copyright 2016-2024 Davide Mastromatteo
License: GPL 2.0
"""

import argparse
import datetime
import json
import logging
import time
import threading
import zmq
from flows.ConfigManager import ConfigManager
from flows.FlowsLogger import FlowsLogger
from flows.MessageDispatcher import MessageDispatcher
from flows.Actions.Action import Action
from importlib.metadata import version

__author__: str = "Davide Mastromatteo"
__copyright__: str = "Copyright 2024, Davide Mastromatteo"
__credits__: list = [""]
__license__: str = "GPL-2.0"
__version__: str = version("flows")
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
        self.__set_command_line_arguments(self.__parse_input_parameters())
        self.__set_subscriber_socket()

    def __set_subscriber_socket(self) -> None:
        """
        Set up the SUB ZMQ socket
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(self.config_manager.subscriber_socket_address)

        # set a timeout of 1000ms
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)

        # filter the multipart messages with a "*" in part 1
        self.socket.setsockopt(zmq.SUBSCRIBE, bytes("*", "utf-8"))

    def __set_command_line_arguments(self, args) -> None:
        """
        Set internal configuration variables according to
        the input parameters
        """
        self.logger.debug("setting command line arguments")

        if args.VERBOSE:
            FlowsLogger.default_instance().reconfigure_log_level(logging.INFO)
            self.logger.info("verbose mode active")

        if args.TRACE:
            self.config_manager.tracing_mode = True
            FlowsLogger.default_instance().reconfigure_log_level(logging.DEBUG)
            self.logger.debug("tracing mode active")

        self.logger.debug(f"recipes to be parsed: {args.FILENAME}")
        self.config_manager.recipes = args.FILENAME

    def start(self) -> None:
        """
        Start all the processes
        """
        self.logger.info("starting the flow manager")
        self.isrunning = True
        self.__start_actions()
        self.fetcher_thread = threading.Thread(
            target=self.__run_message_fetcher, daemon=True
        )
        self.fetcher_thread.start()
        self.logger.debug("flow manager started")

        try:
            while self.isrunning:
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user.")
            self.stop()

    def stop(self) -> None:
        """
        Stop all the processes
        """
        self.logger.info("stopping the flow manager")
        self.isrunning = False  # stop the message fetcher
        self.__stop_actions()
        self.logger.debug("flow manager stopped")

    def restart(self) -> None:
        """
        Restart all the processes
        """
        self.logger.info("restarting the flow manager")
        self.stop()
        self.actions = []  # clear the action list
        time.sleep(3)
        self.start()
        self.logger.debug("flow manager restarted")

    def __start_actions(self) -> None:
        """
        Start all the actions for the recipes
        """
        self.logger.info("starting actions")

        for recipe in self.config_manager.recipes:
            self.config_manager.read_recipe(recipe)

            for section in self.config_manager.sections:
                self.__start_action_for_section(section)

    def __start_action_for_section(self, section):
        """

        Start all the actions for a particular section
        """
        if section == "configuration":
            return

        self.logger.debug("starting actions for section " + section)

        # read the configuration of the action
        action_configuration = self.config_manager.sections[section]

        if len(action_configuration) == 0:
            self.logger.warning(f"section {section} has no configuration, skipping")
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
            self.logger.warning(
                f"can't find a type for action {section}, the action will be skipped"
            )
            return

        self.actions.append(my_action)
        my_action.start()

        self.logger.debug("updating the subscriptions table")
        for my_input in my_action.monitored_input:
            self.subscriptions.setdefault(my_input, []).append(my_action)

    def __stop_actions(self) -> None:
        """
        Stop all the actions
        """
        self.logger.info("stopping actions")

        for action in self.actions:
            action.stop()
            action.join(1)

        self.logger.info("actions stopped")

    def __deliver_message(self, msg):
        """
        Deliver the message to the subscripted actions
        """
        my_subscribed_actions = self.subscriptions.get(msg["sender"], [])
        for action in my_subscribed_actions:
            if self.config_manager.tracing_mode:
                self.logger.debug(f"delivering message to {action.name}")

            # action.on_input_received(msg)
            action.message_queue.put(msg)

    def __fetch_messages(self):
        """
        Get an input message from the socket
        """
        try:
            [_, msg] = self.socket.recv_multipart()  # flags=zmq.NOBLOCK

            if self.config_manager.tracing_mode:
                self.logger.debug("fetched a new message")

            self.fetched = self.fetched + 1
            obj = json.loads(msg)
            self.__deliver_message(obj)
            return obj

        except zmq.error.Again:
            return None

        except Exception as new_exception:
            self.logger.error(new_exception)
            raise new_exception

    def __run_message_fetcher(self):
        """
        Loop che gira in un thread separato,
        riceve messaggi ZMQ e li mette nelle code delle azioni.
        """
        self.logger.debug("ZMQ Message Fetcher thread started.")
        try:
            while self.isrunning:
                try:
                    self.__fetch_messages()
                except zmq.ZMQError as e:
                    self.logger.error(f"ZMQ error in fetcher thread: {e}")
                    time.sleep(self.config_manager.message_fetcher_sleep_interval)
                except Exception as e:
                    self.logger.error(f"Error in message fetcher: {e}")

        except Exception as e:
            self.logger.critical(f"Message fetcher thread failed critically: {e}")

    def __parse_input_parameters(self):
        """
        Set the configuration for the Logger
        """
        self.logger.debug("define and parsing command line arguments")
        parser = argparse.ArgumentParser(
            description="A workflow engine for Pythonistas",
            formatter_class=argparse.RawTextHelpFormatter,
        )
        parser.add_argument("FILENAME", nargs="+", help="name of the recipe file(s)")

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
