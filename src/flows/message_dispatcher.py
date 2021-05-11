#!/usr/bin/env python3

"""
MessageDispatcher.py
Class to handle the dispatching of messages
-----------------------------------------------

Copyright 2016-2021 Davide Mastromatteo
License: Apache-2.0
"""

import datetime
import json
import threading

import flows_logger
import config_manager

import global_module as Global


class MessageDispatcher:
    """
    MessageDispatcher class
    Messages broadcaster
    """
    # singleton variables
    _instance = None
    _instance_lock = threading.Lock()

    LOGGER = flows_logger.FlowsLogger.default_instance().get_logger()
    CONFIG_MANAGER = config_manager.ConfigManager()

    @classmethod
    def default_instance(cls):
        """
        For use like a singleton, return the existing instance of the object
        or a new instance
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = MessageDispatcher()

        return cls._instance

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.LOGGER.debug("initializing the message dispatcher")

        self.dispatched = 0
        self.last_stat = datetime.datetime.now()

    def send_message(self, message, queue):
        """
        Dispatch a message using 0mq
        """

        with self._instance_lock:
            if message is None:
                self.LOGGER.error("can't deliver a null messages")
                return

            if message["sender"] is None:
                self.LOGGER.error(f"can't deliver anonymous messages")
                return

            if message["target"] is None:
                self.LOGGER.error(
                    f"can't deliver message: recipient not specified")
                return

            if message["message"] is None:
                self.LOGGER.error(f"can't deliver message with no body")
                return
            
            json_dump = json.dumps(message)
            queue.put.remote(json_dump)

            if self.CONFIG_MANAGER.tracing_mode:
                self.LOGGER.debug(f"{message} dispatched")

            self.dispatched = self.dispatched + 1
