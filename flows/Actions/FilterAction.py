#!/usr/bin/env python

'''
FilterAction.py
----------------------------

Copyright 2016 Davide Mastromatteo
'''


import re
import os
from flows.Actions.Action import Action


class FilterAction(Action):
    """
    FilterAction Class
    """

    type = "filter"
    regex = ""
    regexes_file = ""
    ignorecase = False

    invert_match = False

    regexes = []

    def on_init(self):
        super().on_init()

        self.regexes = []
        if "regexes_file" in self.configuration:
            self.regexes_file = self.configuration["regexes_file"]
            if os.path.isfile(self.regexes_file):
                file_containing_regexes = open(self.regexes_file)
                self.regexes = file_containing_regexes.readlines()
                file_containing_regexes.close()
            else:
                print(self.regexes_file + " not found, skipped")

        if "regex" in self.configuration:
            self.regexes.append(self.configuration["regex"])

        if "subtype" in self.configuration:
            subtype = self.configuration["subtype"]
            if subtype == "invert":
                self.invert_match = True

        if "ignorecase" in self.configuration:
            self.ignorecase = True

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        return_value = action_input.message

        flags = 0
        if self.ignorecase:
            flags = re.IGNORECASE

        # Normal match: if any of the regexes matches, returns the input
        if not self.invert_match:
            for regex in self.regexes:
                regex = regex.strip()
                if regex != "":
                    match = re.search(regex, action_input.message, flags)
                    if match is not None:
                        self.send_message(return_value)

        # Inverted match: returns the input message only if NO conditions
        # match!
        else:
            for regex in self.regexes:
                regex = regex.strip()
                match = re.search(regex, action_input.message, flags)
                if match is not None:
                    return None

            self.send_message(return_value)
