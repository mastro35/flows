#!/usr/bin/env python3

"""
TimerAction.py
--------------

Copyright 2016 Davide Mastromatteo
"""

import asyncio
from flows.Actions.action import Action


class TimerAction(Action):
    """
    TimerAction Class
    """

    type = "timer"
    timeout = 0
    loop = None

    def run_operation(self):
        """
        Fire a single operation
        """
        self.send_message("TIMER : " + self.name)

        if self.is_running:
            self.start_timer()
        else:
            self.loop.close()

    def start_timer(self):
        """
        Schedule the next run
        """
        self.loop.call_later(self.timeout, self.run_operation)

    def on_stop(self):
        self.is_running = False
        super().on_stop()

    def on_init(self):
        super().on_init()
        self.timeout = int(self.configuration["delay"])
        self.loop = asyncio.get_event_loop()

        self.start_timer()
