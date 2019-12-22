#!/usr/bin/env python3

"""
MessageDispatcher.py
Class to handle the dispatching of zmq messages
-----------------------------------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
"""

import datetime
import json
import threading

import zmq

from flows import global_module as Global


class MessageDispatcher:
    """
    MessageDispatcher class
    Messages broadcaster
    """
    # singleton variables
    _instance = None
    _instance_lock = threading.Lock()

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

        Global.LOGGER.debug("initializing the message dispatcher")

        self.dispatched = 0
        self.last_stat = datetime.datetime.now()
        self.context = None
        self.socket = None

        self.context = zmq.Context()
        self.socket = Global.ZMQ_CONTEXT.socket(zmq.PUSH) # pylint: disable=E1101
        self.socket.connect("tcp://localhost:5558")

        Global.LOGGER.debug(
            "configuring the socket address for messaging subsystem")

        #        for attempt in range(0, 6):
        #            try:
        #                Global.CONFIG_MANAGER.set_socket_address()
        #                self.socket.bind(
        #                    Global.CONFIG_MANAGER.publisher_socket_address)
        #                break
        #            except zmq.error.ZMQError:
        #                if attempt == 5:
        #                    Global.LOGGER.error(
        #                        """Can't find a suitable tcp port to connect.
        #                        The execution will be terminated""")
        #                    sys.exit(8)

        #                Global.LOGGER.warning(str.format(
        #                    "error occured trying to connect to {0} ",
        #                    Global.CONFIG_MANAGER.publisher_socket_address))

        #                Global.LOGGER.warning(str.format(
        #                    "retrying... ({0}/{1})", attempt + 1, 5))

        #                time.sleep(1)

        Global.LOGGER.debug("message dispatcher initialized successfully")

    def send_message(self, message):
        """
        Dispatch a message using 0mq
        """
        with self._instance_lock:
            if message is None:
                Global.LOGGER.error("can't deliver a null messages")
                return

            if message["sender"] is None:
                Global.LOGGER.error(f"can't deliver anonymous messages")
                return

            if message["target"] is None:
                Global.LOGGER.error(
                    f"can't deliver message: recipient not specified")
                return

            if message["message"] is None:
                Global.LOGGER.error(f"can't deliver message with no body")
                return

            self.socket.send_string(json.dumps(message))

            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug(f"{message} dispatched")

            self.dispatched = self.dispatched + 1
