#!/usr/bin/env python

'''
BufferAction.py
----------------------------

Copyright 2016 Davide Mastromatteo
'''

import re
from flows.Actions.Action import Action


class BufferAction(Action):
    """
    BufferAction Class
    """

    type = "buffer"
    buffer = None
    regex = ""

    def on_init(self):
        super().on_init()
        if "regex_new_buffer" not in self.configuration:
            raise ValueError(str.format("The buffer action {0} is not properly configured."
                                        "The regex_new_buffer parameter is missing",
                                        self.name))

        self.buffer = []
        self.regex = self.configuration["regex_new_buffer"]

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)
        # Action
        match = re.search(self.regex, action_input.message)

        # if no match, bufferize & return
        if match is None:
            self.buffer.append(action_input.message)
            return (None, "*")

        if len(self.buffer) > 0:
            return_value = ''.join(self.buffer)
            self.buffer.clear()
            self.buffer.append(action_input.message)
            self.send_message(return_value)
        else:
            self.buffer.append(action_input.message)
