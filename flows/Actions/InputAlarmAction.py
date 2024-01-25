"""
AlarmAction.py
--------------

Use the parameter "date" as following to set an alarm

date = 01/11/2017 18:25

Copyright 2016-2024 Davide Mastromatteo
"""

import datetime
from flows.Actions.Action import Action


class AlarmAction(Action):
    """
    AlarmAction Class
    """

    type = "alarm"

    def on_init(self):
        super().on_init()

        if "date" not in self.configuration:
            raise ValueError(
                str.format(
                    "The alarm action {0} is not properly configured."
                    "The `date` parameter is missing",
                    self.name,
                )
            )

        try:
            date = self.configuration["date"]
            self.next = datetime.datetime.strptime(date, "%d/%m/%Y %H:%M")
        except:
            raise ValueError(
                str.format(
                    "An error occured while parsing the data parameter."
                    "The `date` parameter is not in a valid format",
                    self.name,
                )
            )
            

    def on_cycle(self):
        super().on_cycle()

        now = datetime.datetime.now()
        now = now.replace(second=0, microsecond=0)
        if now >= self.next:
            self.next = None
            self.send_message(f"ALARM -{self.name}-")
            self.stop()

    def on_input_received(self):
        pass

    def on_stop(self):
        pass
