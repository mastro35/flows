#!/usr/bin/env python3

'''
CronAction.py
--------------

Execute an action when the schedule criterion is met.
The parameter crontab_schedule has to be in the crontab format:

.---------------- [m]inute: (0 - 59)
|  .------------- [h]our: (0 - 23)
|  |  .---------- [d]ay of month: (1 - 31)
|  |  |  .------- [mon]th: (1 - 12)
|  |  |  |  .---- [w]eek day: (0 - 6)
|  |  |  |  |
*  *  *  *  *

Copyright 2016 Davide Mastromatteo
'''

import asyncio
import datetime

from croniter import croniter

from flows.Actions.Action import Action


class CronAction(Action):
    """
    CronAction Class
    """

    type = "cron"

    crontab_schedule = "* * * * *"
    next = None
    cron = None
    timeout = 60
    loop = None

    async def run_operation(self):
        """
        Execute the action when the cront time has reached
        """
        while self.is_running:
            now = datetime.datetime.now()
            now = now.replace(microsecond=0)

            if now >= self.next:
                self.next = self.cron.get_next(datetime.datetime)
                self.send_message("CRON : " + self.name)

            await asyncio.sleep(1)

    def on_init(self):
        super().on_init()

        if "crontab_schedule" not in self.configuration:
            raise ValueError(str.format("The cron action {0} is not properly configured."
                                        "The crontab_schedule parameter is missing",
                                        self.name))

        self.crontab_schedule = self.configuration["crontab_schedule"]

        now = datetime.datetime.now()
        now = now.replace(microsecond=0)

        self.cron = croniter(self.crontab_schedule, now)
        self.next = self.cron.get_next(datetime.datetime)

        self.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.run_operation(), loop=self.loop)
