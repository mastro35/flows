#!/usr/bin/env python3

'''
CountAction.py
--------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

import datetime
from Actions.action import Action


class CountAction(Action):
    """
    CountAction Class
    Count the input and pass the counter to the output.
    Can work in association with a TIMER event.
    """

    type = "count"
    timed_counter = False
    partial_counter = False
    counter = 0
    timeout = 0
    timer_start = datetime.datetime.now()

    def on_init(self):
        super().on_init()
        if "timeout" in self.configuration:
            self.timed_counter = True
            self.timeout = int(self.configuration["timeout"])

        if "partial" in self.configuration:
            self.partial_counter = True

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)
        self.counter = self.counter + 1
        if not self.timed_counter:
            self.send_message(str(self.counter))

    async def run(self):
        """
        Execute the timer action when the delay is over
        """
        while self.is_running:
            if self.timed_counter:
                await self.sleep(self.timeout)
                self.send_message(str(self.counter))
                if self.partial_counter:
                    self.counter = 0
            else:
                await self.sleep(1)
