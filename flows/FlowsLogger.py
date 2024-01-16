"""
FlowsLogger.py
Logging facility module for flows
----------------------------------

Copyright 2016-2024 Davide Mastromatteo
License: GPL 2.0
"""

import logging
import threading


class FlowsLogger:
    """
    FlowsLogger class - Logger Factory
    """

    _instance_lock = threading.Lock()
    _instance = None
    _logger_instance = None
    log_level = logging.WARN

    @classmethod
    def default_instance(cls):
        """
        For use like a singleton, return the existing instance of the object
        or a new instance
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = FlowsLogger()

        return cls._instance

    def __init__(self):
        """
        Default constructor: it should never be called directly!
        """
        self._create_logger_instance()

    def get_logger(self):
        """
        Returns the existing logger instance or, if it doesn't exists,
        create a new instance and return it
        """
        return self._logger_instance or self._create_logger_instance

    def _create_logger_instance(self):
        """
        Create a logger instance
        """
        self._logger_instance = logging.getLogger("flowsLogger")
        self._logger_instance.setLevel(self.log_level)

        log_format = "%(asctime)s - [%(levelname)s]|%(thread)d\t%(message)s"
        log_date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(log_format, log_date_format)

        new_log_stream_handler = logging.StreamHandler()
        new_log_stream_handler.setFormatter(formatter)
        new_log_stream_handler.setLevel(self.log_level)

        self._logger_instance.addHandler(new_log_stream_handler)

        return self._logger_instance

    def reconfigure_log_level(self, log_level):
        """
        Returns a new standard logger instance
        """
        self.log_level = log_level
        self._create_logger_instance()
