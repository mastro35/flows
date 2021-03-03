"""
TimerAction.py
--------------

Copyright 2016 Davide Mastromatteo
"""

from Actions.action import Async_Action

class TimerAction(Async_Action):
    """
    TimerAction Class
    """

    type = "timer"
    timeout = 0
    loop = None

    async def run(self):
        """
        Execute the timer action when the delay is over
        """
        self.log("starting timer")
        while self.is_running:
            await self.sleep(self.timeout)
            self.send_message(f"TIMER {self.name} {self.id}")

    def on_init(self):
        super().on_init()
        self.log("initializing timer")
        self.timeout = int(self.configuration["delay"])
