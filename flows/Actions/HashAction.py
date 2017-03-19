#!/usr/bin/env python

'''
HashAction.py
-------------

Copyright 2016 Davide Mastromatteo
'''

import hashlib
from flows.Actions.Action import Action


class HashAction(Action):
    """
    HashAction Class
    """

    type = "hash"

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        return_value = ""

        input_message = action_input.message

        md5_object = hashlib.md5()
        md5_object.update(input_message.encode('utf-8'))
        return_value = md5_object.hexdigest()

        # returns the output
        self.send_message(return_value)
