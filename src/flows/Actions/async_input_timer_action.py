#!/usr/bin/env python3

"""
TimerAction.py
--------------

Copyright 2016 Davide Mastromatteo
"""

import asyncio
from Actions.action import Action

class TimerAction(Action):
    """
    TimerAction Class
    """

    type = "timer"
    timeout = 0
    loop = None

    async def run_timer(self):
        """
        Execute the timer action when the delay is over
        """
        while self.is_running:
            await asyncio.sleep(self.timeout)
            self.send_message(f"TIMER")

    def on_init(self):
        super().on_init()
        self.timeout = int(self.configuration["delay"])
        self.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.run_timer(), loop=self.loop)
