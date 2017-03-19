#!/usr/bin/env python

'''
ConfigManager.py
Handle the configuration for flows
----------------------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

import logging
import os
import threading
import configparser
import random
from flows import Global


def _get_configuration_file_path(app_name):
    """ get the path of the config file """
    environment_variable_path = str.format("{0}_CONF", app_name.upper)
    possible_paths = [os.curdir, os.path.expanduser("~"), "/etc/",
                      os.environ.get(environment_variable_path)]

    for loc in possible_paths:
        try:
            if loc is not None:
                config_file_name = os.path.join(loc, app_name + ".conf")
                if os.path.exists(config_file_name):
                    return config_file_name

        except IOError:
            return ""

    return ""


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
    sleep_interval = 0.5
    message_fetcher_sleep_interval = 0.5
    queue_length_for_system_check = 100
    messages_dispatched_for_system_check = 5000
    seconds_between_queue_check = 60
    log_level = logging.INFO
    recipes = []

    @staticmethod
    def default_instance():
        """For use like a singleton, return the existing instance
        of the object or a new instance"""
        if ConfigManager._instance is None:
            with threading.Lock():
                if ConfigManager._instance is None:
                    ConfigManager._instance = ConfigManager()

        return ConfigManager._instance

    def read_recipe(self, filename):
        '''read a recipe file from disk'''
        if not os.path.isfile(filename):
            Global.LOGGER.error(filename + " recipe not found, skipping")
            return

        config = configparser.ConfigParser(allow_no_value=True,
                                           delimiters="=")

        config.read(filename)

        for section in config.sections():
            self.sections[section] = config[section]

        Global.LOGGER.debug("Read recipe " + filename)

    def set_socket_address(self):
        """ set a random port to be used by zmq """
        random.seed()
        default_port = random.randrange(5001, 5999)

        # Set the socket address for 0mq
        internal_0mq_address = self.get_configuration_value(
            "internal_0mq_address",
            "tcp://127.0.0.1")

        internal_0mq_port_subscriber = self.get_configuration_value(
            "internal_0mq_port_subscriber", str(default_port))

        internal_0mq_port_publisher = self.get_configuration_value(
            "internal_0mq_port_publisher", str(default_port))

        Global.LOGGER.info(str.format(
            "zmq messages subsystem will use the {0} port for subscribers",
            internal_0mq_port_subscriber))

        Global.LOGGER.info(str.format(
            "zmq messages subsystem will use the {0} port for publishers",
            internal_0mq_port_publisher))

        self.subscriber_socket_address = str.format("{0}:{1}",
                                                    internal_0mq_address,
                                                    internal_0mq_port_subscriber)

        self.publisher_socket_address = str.format("{0}:{1}",
                                                   internal_0mq_address,
                                                   internal_0mq_port_publisher)

    def read_configuration(self):
        """ read the configuration file """
        self.config_file = _get_configuration_file_path('flows')
        Global.LOGGER.debug("Config File = " + self.config_file)

        config = configparser.ConfigParser(allow_no_value=True,
                                           delimiters="=")
        config.read(self.config_file)

        for section in config.sections():
            self.sections[section] = config[section]

    def get_section(self, section_name):
        """ get the value of a single section of the configuration file """
        try:
            section_content = self.sections[section_name]
            return section_content
        except IndexError:
            return []

    def get_configuration_value(self, key, default=""):
        """ get a single configuration value from the config file """
        config_value = default
        if "configuration" in self.sections:
            if key in self.sections["configuration"]:
                config_value = self.sections["configuration"][key]

        return config_value
