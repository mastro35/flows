#!/usr/bin/env python3

"""
ConfigManager.py
Handle the configuration for flows
----------------------------------

Copyright 2016-2021 Davide Mastromatteo
License: Apache-2.0
"""

import configparser
import logging
import os

import global_module as Global


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
    message_fetcher_sleep_interval = 0.1  # no parameter: auto throttle
    queue_length_for_system_check = 100
    messages_dispatched_for_system_check = 5000
    seconds_between_queue_check = 60
    log_level = logging.INFO  # -v parameter
    recipes = []  # parameters from command line
    show_stats = False  # -s <> 0 parameter
    tracing_mode = False  # -t parameter
    stats_timeout = 60  # -s parameter
    fixed_message_fetcher_interval = False  # -m parameter

    @staticmethod
    def default_instance():
        """
        For use like a singleton, return the existing instance
        of the object or a new instance
        """
        if ConfigManager._instance is None:
            # with threading.Lock():
                if ConfigManager._instance is None:
                    ConfigManager._instance = ConfigManager()

        return ConfigManager._instance

    def read_recipe(self, filename):
        """
        Read a recipe file from disk
        """
        Global.LOGGER.debug(f"reading recipe {filename}")
        if not os.path.isfile(filename):
            Global.LOGGER.error(filename + " recipe not found, skipping")
            return

        config = configparser.ConfigParser(allow_no_value=True,
                                           delimiters="=")

        config.read(filename)

        for section in config.sections():
            self.sections[section] = config[section]

        Global.LOGGER.debug("Read recipe " + filename)

    def get_section(self, section_name):
        """
        Get the value of a single section of the configuration file
        """
        try:
            section_content = self.sections[section_name]
            return section_content
        except IndexError:
            return []
