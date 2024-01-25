"""
TimerAction.py
--------------

Copyright 2016 Davide Mastromatteo
"""

import threading
from flows.Actions.Action import Action


class TimerAction(Action):
    """
    TimerAction Class
    """

    type = "timer"
    next_timer = None

    def run_operation(self):
        self.send_message(f"TIMER -{self.name}-")

        if self.is_running:
            self.start_timer()

    def start_timer(self):
        self.next_timer = threading.Timer(self.timeout, self.run_operation)
        self.next_timer.start()

    def on_stop(self):
        if self.next_timer is not None:
            self.next_timer.cancel()

        super().on_stop()

    def on_init(self):
        super().on_init()
        
        if "delay" not in self.configuration:
            raise ValueError(
                str.format(
                    "The timer action {0} is not properly configured."
                    "The `delay` parameter is missing",
                    self.name,
                )
            )

        try:
            self.timeout = int(self.configuration["delay"])
            self.start_timer()
        except:
            raise ValueError(
                str.format(
                    "The timer action {0} is not properly configured."
                    "Error while reading the `delay` parameter",
                    self.name,
                )
            )
            

    def on_input_received(self):
        pass

    def on_stop(self):
        pass

    def on_cycle(self):
        pass
