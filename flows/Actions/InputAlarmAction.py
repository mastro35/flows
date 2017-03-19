#!/usr/bin/env python

'''
AlarmAction.py
--------------

Use the parameter "date" as following to set an alarm

date = 01/11/2017 18:25

Copyright 2016 Davide Mastromatteo
'''

import datetime
from flows.Actions.Action import Action


class AlarmAction(Action):
    """
    AlarmAction Class
    """

    type = "alarm"
    next = None

    def on_init(self):
        super().on_init()

        if "date" not in self.configuration:
            raise ValueError(str.format("The alarm action {0} is not properly configured."
                                        "The Date parameter is missing",
                                        self.name))

        date = self.configuration["date"]
        self.next = datetime.datetime.strptime(date, "%d/%m/%Y %H:%M")

    def on_cycle(self):
        super().on_cycle()

        now = datetime.datetime.now()
        now = now.replace(second=0, microsecond=0)
        if now >= self.next:
            self.next = None
            self.send_message("ALARM")
