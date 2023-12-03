"""
MessageDispatcher.py
Class to handle the dispatching of zmq messages
-----------------------------------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
"""

import datetime
import pickle
import sys
import threading
import time

import zmq

from flows.ConfigManager import ConfigManager
from flows.FlowsLogger import FlowsLogger


class MessageDispatcher:
    """
    MessageDispatcher class
    Messages broadcaster
    """

    # singleton variables
    _instance = None
    _instance_lock = threading.Lock()
    LOGGER = FlowsLogger.default_instance().get_logger()
    CONFIG_MANAGER = ConfigManager.default_instance()

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
        self.context = None
        self.socket = None

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)

        self.LOGGER.debug("configuring the socket address for messaging subsystem")
        for attempt in range(0, 6):
            try:
                self.CONFIG_MANAGER.set_socket_address()
                self.socket.bind(self.CONFIG_MANAGER.publisher_socket_address)
                break
            except zmq.error.ZMQError:
                if attempt == 5:
                    self.LOGGER.error(
                        """Can't find a suitable tcp port to connect.
                        The execution will be terminated"""
                    )
                    sys.exit(8)

                self.LOGGER.warning(
                    str.format(
                        "error occured trying to connect to {0} ",
                        self.CONFIG_MANAGER.publisher_socket_address,
                    )
                )

                self.LOGGER.warning(str.format("retrying... ({0}/{1})", attempt + 1, 5))

                time.sleep(1)

        self.LOGGER.debug("message dispatcher initialized successfully")

    def send_message(self, message):
        """
        Dispatch a message using 0mq
        """
        with self._instance_lock:
            if message is None:
                self.LOGGER.error("can't deliver a null messages")
                return

            if message.sender is None:
                self.LOGGER.error(
                    f"can't deliver anonymous messages with body {message.body}"
                )
                return

            if message.receiver is None:
                self.LOGGER.error(
                    f"can't deliver message from {message.sender}: recipient not specified"
                )
                return

            if message.message is None:
                self.LOGGER.error(
                    f"can't deliver message with no body from {message.sender}"
                )
                return

            sender = "*" + message.sender + "*"
            self.socket.send_multipart([bytes(sender, "utf-8"), pickle.dumps(message)])

            if self.CONFIG_MANAGER.tracing_mode:
                self.LOGGER.debug(
                    "dispatched : "
                    + message.sender
                    + "-"
                    + message.message
                    + "-"
                    + message.receiver
                )

            self.dispatched = self.dispatched + 1
