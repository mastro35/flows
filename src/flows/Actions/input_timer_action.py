"""
TimerAction.py
--------------

Copyright 2016-2021 Davide Mastromatteo
"""

from Actions.action import Action
import time

class TimerAction(Action):
    """
    TimerAction Class
    """

    type = "timer"
    timeout = 0

    def run(self):
        """
        Execute the timer action when the delay is over
        """
        self.log("starting timer")
        while self.is_running:
            time.sleep(self.timeout)
            self.send_message(f"TIMER {self.name} {self.id}")

    def on_init(self):
        super().on_init()
        self.log("initializing timer")
        self.timeout = int(self.configuration["delay"])
