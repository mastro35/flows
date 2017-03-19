#!/usr/bin/env python

'''
CountAction.py
--------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

import datetime
import threading
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
    next_timer = None

    def run_operation(self):
        self.send_message(str(self.counter))
        if self.partial_counter:
            self.counter = 0

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
        if "timeout" in self.configuration:
            self.timed_counter = True
            self.timeout = int(self.configuration["timeout"])

        if "partial" in self.configuration:
            self.partial_counter = True

        if self.timed_counter:
            self.start_timer()

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)
        self.counter = self.counter + 1
        if not self.timed_counter:
            self.send_message(str(self.counter))
