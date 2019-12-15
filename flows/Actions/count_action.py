#!/usr/bin/env python3

'''
CountAction.py
--------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

import datetime
import asyncio
from flows.Actions.Action import Action


class CountAction(Action):
    """
    CountAction Class
    Count the input and pass the counter to the output.
    Can work in association with a TIMER event.
    """

    timed_counter = False
    type = "count"
    counter = 0
    timer_start = datetime.datetime.now()
    timeout = 0
    partial_counter = False

    def on_init(self):
        super().on_init()
        if "timeout" in self.configuration:
            self.timed_counter = True
            self.timeout = int(self.configuration["timeout"])

        if "partial" in self.configuration:
            self.partial_counter = True

        self.loop = asyncio.get_event_loop()

        if self.timed_counter:
            asyncio.ensure_future(self.run_timer(), loop=self.loop)

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)
        self.counter = self.counter + 1
        if not self.timed_counter:
            self.send_message(str(self.counter))

    async def run_timer(self):
        """
        Execute the timer action when the delay is over
        """
        while self.is_running:
            await asyncio.sleep(self.timeout)
            self.send_message(str(self.counter))
            if self.partial_counter:
                self.counter = 0
