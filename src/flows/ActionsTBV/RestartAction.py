"""
RestartAction.py
----------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
"""

from flows.Actions.Action import Action


class RestartAction(Action):
    """
    RestartAction Class
    """

    type = "restart"

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        self.PROCESS_MANAGER.restart()
