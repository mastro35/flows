#!/usr/bin/env python

'''
SubstringAction.py
------------------

Copyright 2016 Davide Mastromatteo
'''

from flows.Actions.Action import Action


class SubstringAction(Action):
    """
    SubstringAction Class
    """

    type = "substring"
    from_index = 0
    to_index = 0
    separator = ""
    item = 0
    substring_type = "cut"

    def on_init(self):
        super().on_init()
        if "from" in self.configuration:
            self.from_index = int(self.configuration["from"])
            if self.from_index < 0:
                self.from_index = 0

        if "to" in self.configuration:
            self.to_index = int(self.configuration["to"])

        if "separator" in self.configuration:
            self.separator = self.configuration["separator"].strip()

        if "item" in self.configuration:
            self.item = int(self.configuration["item"]) - 1

        if "subtype" in self.configuration:
            self.substring_type = self.configuration["subtype"]

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        if action_input.sender == self.name:
            return None

        # Action
        return_value = ""

        # do stuff...
        input_string = action_input.message

        if self.substring_type == "cut":
            return_value = input_string[self.from_index:self.to_index]

        if self.substring_type == "split":
            return_value = input_string.split(self.separator)[self.item]

        # returns the output
        self.send_message(return_value)
