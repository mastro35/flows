#!/usr/bin/env python3

'''
RestartAction.py
----------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

from flows.Actions.action import Action
import flows.global_module


class RestartAction(Action):
    """
    RestartAction Class
    """

    type = "restart"

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        flows.global_module.PROCESS_MANAGER.restart()
