#!/usr/bin/env python

'''
CommandAction.py
----------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

import time
import subprocess
from flows.Actions.Action import Action


class CommandAction(Action):
    """
    CommandAction Class
    """

    type = "command"
    command = ""

    def on_init(self):
        super().on_init()

        if "command" not in self.configuration:
            raise ValueError(str.format("The command action {0} is not properly configured:"
                                        "The command parameter is missing",
                                        self.name))

        self.command = self.configuration["command"]

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        input_message = action_input.message

        cmd = self.command
        cmd = cmd.replace("{input}", input_message)
        cmd = cmd.replace("{date}", time.strftime("%d/%m/%Y"))
        cmd = cmd.replace("{time}", time.strftime("%H:%M:%S"))

        if action_input.file_system_event is not None:
            cmd = cmd.replace(
                "{event_type}", action_input.file_system_event.event_type)
            cmd = cmd.replace(
                "{file_source}", action_input.file_system_event.src_path)
            cmd = cmd.replace("{is_directory}", str(
                action_input.file_system_event.is_directory))
            if hasattr(action_input.file_system_event, "dest_path"):
                cmd = cmd.replace("{file_destination}",
                                  action_input.file_system_event.src_path)

        process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True)

        out = process.stdout

        output_string = str(out.strip().encode(
            'ascii', 'ignore').decode('utf-8'))
        # output_string = out.encode('utf-8')
        # returns the output
        self.send_message(output_string)
