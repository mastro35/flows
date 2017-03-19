#!/usr/bin/env python

'''
GenericCustomAction.py
----------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

from flows.Actions.Action import Action


class GenericCustomAction(Action):
    """
    GenericCustomAction Class
    """

    type = "generic"

    def on_init(self):
        super().on_init()
        # if needed, execute initializazion code HERE

    def on_stop(self):
        # if needed, execute finalization code HERE
        return super().on_stop()

    def on_cycle(self):
        super().on_cycle()
        # if needed, execute code to be executed each cycle HERE

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # if needed, execute code to handle input received HERE, doing something clever ...
        # - like reverting the input string?
        to_return = action_input.message[::-1]

        # and - if needed - message other actions with the result of your
        # operation
        self.send_message(to_return)
