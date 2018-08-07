#!/usr/bin/env python3

"""
LogAction.py
------------

Copyright 2016 Davide Mastromatteo
"""

import logging
import time
from logging.handlers import RotatingFileHandler

from flows.Actions.action import Action


class LogAction(Action):
    """
    LogAction Class
    Log the input to the stdout, and passes it to the output
    """

    type = "log"
    print_to_stdout = True
    output_file = ""
    file_logger = None
    rolling = False

    def on_init(self):
        super().on_init()
        self.is_thread = False

        if "option" in self.configuration:
            option_token = self.configuration["option"]
            if option_token == "null":
                self.print_to_stdout = False
            else:
                self.output_file = option_token

                if "rolling" in self.configuration:

                    self.rolling = True
                    self.file_logger = logging.getLogger(
                        "Rotating Log" + self.output_file)
                    self.file_logger.setLevel(logging.DEBUG)

                    max_bytes = 20000000
                    if "maxBytes" in self.configuration:
                        max_bytes = int(self.configuration["maxBytes"])

                    backup_count = 5
                    if "backupCount" in self.configuration:
                        backup_count = int(self.configuration["backupCount"])

                    handler = RotatingFileHandler(self.output_file, maxBytes=max_bytes,
                                                  backupCount=backup_count)

                    self.file_logger.addHandler(handler)

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        string_to_log = ""

        if "text" in self.configuration:
            string_to_log = self.configuration["text"]

        input_message = action_input["message"]

        string_to_log = string_to_log.replace("\\n", '\n')
        string_to_log = string_to_log.replace("\\t", '\t')
        string_to_log = string_to_log.replace("{input}", input_message)
        string_to_log = string_to_log.replace(
            "{date}", time.strftime("%d/%m/%Y"))
        string_to_log = string_to_log.replace(
            "{time}", time.strftime("%H:%M:%S"))

        if "message_dictionary" in action_input:
            string_to_log = string_to_log.replace("{event_type}",
                                                  action_input["message_dictionary"].event_type)
            string_to_log = string_to_log.replace("{file_source}",
                                                  action_input["message_dictionary"].src_path)
            string_to_log = string_to_log.replace("{is_directory}",
                                                  str(action_input["message_dictionary"].is_directory))
            if hasattr(action_input["message_dictionary"], "dest_path"):
                string_to_log = string_to_log.replace("{file_destination}",
                                                      action_input["message_dictionary"].src_path)

        if string_to_log == "":
            string_to_log = input_message

        if self.print_to_stdout:
            if self.output_file == "":
                print(string_to_log)
            else:
                if self.rolling:
                    self.file_logger.debug(string_to_log.strip())
                else:
                    out_file = open(self.output_file, "a")
                    out_file.write(string_to_log.strip() + "\n")
                    out_file.close()

        # returns the output
        self.send_message(string_to_log)

    def on_stop(self):
        super().on_stop()
        if self.rolling:
            # remove handlers smoothly
            for handler in self.file_logger.handlers:
                self.file_logger.removeHandler(handler)
            self.file_logger = None
