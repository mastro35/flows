#!/usr/bin/env python

'''
TimerAction.py
--------------

Copyright 2016 Davide Mastromatteo
'''

import threading
from flows.Actions.Action import Action


class TimerAction(Action):
    """
    TimerAction Class
    """

    type = "timer"
    timeout = 0
    next_timer = None

    def run_operation(self):
        self.send_message("TIMER : " + self.name)

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
        self.timeout = int(self.configuration["delay"])
        # self.start_time = datetime.datetime.now()

        self.start_timer()
