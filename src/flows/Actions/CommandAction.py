"""
CommandAction.py
----------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
"""

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
            raise ValueError(
                str.format(
                    "The command action {0} is not properly configured:"
                    "The command parameter is missing",
                    self.name,
                )
            )

        self.command = self.configuration["command"]

    def on_input_received(self, message=None):
        super().on_input_received(message)

        cmd = self.command
        cmd = cmd.replace("{input}", repr(self.input_message))
        cmd = cmd.replace("{date}", time.strftime("%d/%m/%Y"))
        cmd = cmd.replace("{time}", time.strftime("%H:%M:%S"))

        if "event_type" in self.input_message:
            cmd = cmd.replace("{event_type}", self.input_message["event_type"])

        if "src_path" in self.input_message:
            cmd = cmd.replace("{file_source}", self.input_message["src_path"])

        if "is_directory" in self.input_message:
            cmd = cmd.replace("{is_directory}", str(self.input_message["is_directory"]))

        if "dest_path" in self.input_message:
            cmd = cmd.replace("{file_destination}", self.input_message["dest_path"])

        process = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        out = process.stdout

        output_string = str(out.strip().encode("ascii", "ignore").decode("utf-8"))
        # output_string = out.encode('utf-8')
        # returns the output
        self.send_message(output_string)

    def on_cycle(self):
        pass

    def on_stop(self):
        pass
