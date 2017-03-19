#!/usr/bin/env python

'''
PassOnInterval.py
--------------

Pass the input received to the output only if we are in the middle of a defined interval

Copyright 2016 Davide Mastromatteo
'''

import datetime
from flows.Actions.Action import Action


class PassOnInterval(Action):
    """
    PassOnInterval Class
    """

    type = "pass_on_interval"

    weekdays = "*"
    day = "*"
    month = "*"
    start_date = datetime.datetime(1, 1, 1, 0, 0, 0, 0)
    end_date = datetime.datetime(9999, 12, 31, 0, 0, 0, 0)
    start_time = datetime.time(0, 0, 0, 0)
    end_time = datetime.time(23, 59, 59, 999)

    def on_init(self):
        super().on_init()

        if "weekdays" in self.configuration:
            self.weekdays = self.configuration["weekdays"]

        if "day" in self.configuration:
            self.day = self.configuration["day"]

        if "month" in self.configuration:
            self.month = self.configuration["month"]

        if "start_date" in self.configuration:
            self.start_date = (datetime.datetime.strptime(self.configuration["start_date"],
                                                          "%d/%m/%Y"))

        if "end_date" in self.configuration:
            self.end_date = (datetime.datetime.strptime(self.configuration["end_date"],
                                                        "%d/%m/%Y"))

        if "start_time" in self.configuration:
            self.start_time = (datetime.datetime.strptime(self.configuration["start_time"],
                                                          "%H:%M").time())

        if "end_time" in self.configuration:
            self.end_time = (datetime.datetime.strptime(self.configuration["end_time"],
                                                        "%H:%M").time())

    def verify_date(self, now):
        '''Verify the date'''
        return now >= self.start_date and now <= self.end_date

    def verify_time(self, now):
        '''Verify the time'''
        return now.time() >= self.start_time and now.time() <= self.end_time

    def verify_weekday(self, now):
        '''Verify the weekday'''
        return self.weekdays == "*" or str(now.weekday()) in self.weekdays.split(" ")

    def verify_day(self, now):
        '''Verify the day'''
        return self.day == "*" or str(now.day) in self.day.split(" ")

    def verify_month(self, now):
        '''Verify the month'''
        return self.month == "*" or str(now.month) in self.month.split(" ")

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        now = datetime.datetime.now()
        now = now.replace(microsecond=0)

        # if now is not in interval return
        if (not self.verify_day(now) or
                not self.verify_month(now) or
                not self.verify_date(now) or
                not self.verify_time(now) or
                not self.verify_weekday(now)):
            # then
            return (None, "*")

        return_value = action_input.message
        self.send_message(return_value)
