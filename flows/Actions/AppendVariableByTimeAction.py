#!/usr/bin/env python

'''
AppendVariableByTime.py
-----------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

import datetime
import collections
from flows.Actions.Action import Action


class AppendVariableByTime(Action):
    """
    AppendVariableByTime Class
    returns the input received plus a column and a variable based upon the time of the day
    """

    type = "append_variable_by_time"

    separator = ";"
    time_config = ""

    def on_init(self):
        super().on_init()
        if "separator" in self.configuration:
            self.separator = self.configuration["separator"]

        self.time_config = collections.OrderedDict(
            sorted(self.configuration.items()))

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        now = datetime.datetime.now().time()

        for config in self.time_config:
            if ":" in config:
                limit = datetime.datetime.strptime(config, "%H:%M").time()
                if now >= limit:
                    variable = self.configuration[config]

        msg = str.format("{0}{1}{2}", action_input.message,
                         self.separator, variable)

        # returns the output
        self.send_message(msg)
