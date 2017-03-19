#!/usr/bin/env python

'''
CheckIf.py
----------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

from flows.Actions.Action import Action


class CheckIf(Action):
    """
    CheckIf Class
    output values less than an input parameter
    """

    type = "check_if"
    separator = ";"
    output = None

    def on_init(self):
        super().on_init()
        if "separator" in self.configuration:
            self.separator = self.configuration["separator"]

        if "output" in self.configuration:
            self.output = self.configuration["output"]

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        operation = str(self.configuration["operation"])

        value = 0
        limit = 0

        # If the input has a separator, the syntax expected is
        # value[separator]limit
        if self.separator in action_input.message:
            input_message = action_input.message
            value = int(input_message.split(self.separator)[0])
            limit = int(input_message.split(self.separator)[1])
        else:
            # if not, the value is the message and the limit is read fromn the
            # config
            value = int(action_input.message)
            limit = int(self.configuration["limit"])

        if operation == "<":
            if value < limit:
                self.send_output(str(value))
        if operation == "<=":
            if value <= limit:
                self.send_output(str(value))
        if operation == ">":
            if value > limit:
                self.send_output(str(value))
        if operation == ">=":
            if value >= limit:
                self.send_output(str(value))
        if operation == "==":
            if value == limit:
                self.send_output(str(value))
        if operation == "!=":
            if value != limit:
                self.send_output(str(value))
        if operation == "%":
            if value % limit == 0:
                self.send_output(str(value))

    def send_output(self, value):
        if self.output:
            string_to_log = self.output.replace("{value}", value)
            self.send_message(string_to_log)
        else:
            self.send_message(value)
