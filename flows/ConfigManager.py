"""
ConfigManager.py
Handle the configuration for flows
----------------------------------

Copyright 2016-2024 Davide Mastromatteo
License: GPL-2.0
"""

import configparser
import os
import random
import threading

from flows.FlowsLogger import FlowsLogger


class ConfigManager:
    """
    ConfigManager class
    Handle the configuration settings
    """

    config_file = ""

    sections = {}
    _instance = None
    subscriber_socket_address = ""
    publisher_socket_address = ""
    sleep_interval = 0.5  # -i parameter
    message_fetcher_sleep_interval = 0.5  # no parameter: auto throttle
    queue_length_for_system_check = 100
    messages_dispatched_for_system_check = 5000
    seconds_between_queue_check = 60
    recipes = []  # parameters from command line
    show_stats = False  # -s <> 0 parameter
    tracing_mode: bool = False  # -t parameter
    stats_timeout = 60  # -s parameter
    fixed_message_fetcher_interval = False  # -m parameter

    logger = FlowsLogger.default_instance().get_logger()

    _instance = None
    _instance_lock = threading.Lock()

    @classmethod
    def default_instance(cls):
        """
        For use like a singleton, return the existing instance
        of the object or a new instance
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = ConfigManager()

        return cls._instance

    def read_recipe(self, filename):
        """
        Read a recipe file from disk
        """
        self.logger.debug(f"reading recipe {filename}")

        if not os.path.isfile(filename):
            self.logger.error(filename + " recipe not found, skipping")
            return

        config = configparser.ConfigParser(allow_no_value=True, delimiters="=")
        config.read(filename)

        for section in config.sections():
            self.sections[section] = config[section]

        self.logger.debug("Read recipe " + filename)

    def set_socket_address(self):
        """
        Set a random port to be used by zmq
        """
        self.logger.debug("defining socket addresses for zmq")
        random.seed()
        default_port = random.randrange(5001, 5999)

        internal_0mq_address = "tcp://127.0.0.1"
        internal_0mq_port_subscriber = str(default_port)
        internal_0mq_port_publisher = str(default_port)

        self.logger.info(
            str.format(
                f"zmq subsystem subscriber on {internal_0mq_port_subscriber} port"
            )
        )

        self.logger.info(
            str.format(f"zmq subsystem publisher on {internal_0mq_port_publisher} port")
        )

        self.subscriber_socket_address = (
            f"{internal_0mq_address}:{internal_0mq_port_subscriber}"
        )

        self.publisher_socket_address = (
            f"{internal_0mq_address}:{internal_0mq_port_publisher}"
        )

    def get_section(self, section_name):
        """
        Get the value of a single section of the configuration file
        """
        try:
            section_content = self.sections[section_name]
            return section_content
        except IndexError:
            return []
