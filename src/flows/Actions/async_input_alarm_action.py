#!/usr/bin/env python3

'''
AlarmAction.py
--------------

Use the parameter "date" as following to set an alarm

date = 01/11/2017 18:25

Copyright 2016 Davide Mastromatteo
'''

import datetime
from Actions.action import Async_Action


class AlarmAction(Async_Action):
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


    async def run(self):
        """
        Execute the action when the cront time has reached
        """
        while self.is_running:
            now = datetime.datetime.now()
            now = now.replace(microsecond=0)

            if now >= self.next:
                self.send_message(f"ALARM {self.name} {self.id} ")
                self.is_running = False

            await self.sleep(1)
    
