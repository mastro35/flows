#!/usr/bin/env python

'''
MailAction.py
-------------

Copyright 2016 Davide Mastromatteo
'''

import smtplib
import time
from email.mime.text import MIMEText

import flows.Global
from flows.Actions.Action import Action


class MailAction(Action):
    """
    MailAction Class
    send an email
    """

    type = "mail"

    def on_init(self):
        super().on_init()

        if "smtp_server" not in self.configuration:
            raise ValueError(str.format("The mail action {0} is not properly configured."
                                        "The smtp_server parameter is missing", self.name))

        if "smtp_port" not in self.configuration:
            raise ValueError(str.format("The mail action {0} is not properly configured."
                                        "The smtp_port parameter is missing", self.name))

        if "subject" not in self.configuration:
            raise ValueError(str.format("The mail action {0} is not properly configured."
                                        "The subject parameter is missing", self.name))

        if "from" not in self.configuration:
            raise ValueError(str.format("The mail action {0} is not properly configured."
                                        "The from parameter is missing", self.name))

        if "to" not in self.configuration:
            raise ValueError(str.format("The mail action {0} is not properly configured."
                                        "The to parameter is missing", self.name))

        if "body" not in self.configuration:
            raise ValueError(str.format("The mail action {0} is not properly configured."
                                        "The body parameter is missing", self.name))

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        input_message = str(action_input.message)

        body = self.configuration["body"]
        body = body.replace("{input}", input_message)
        body = body.replace("{date}", time.strftime("%d/%m/%Y"))
        body = body.replace("{time}", time.strftime("%H:%M:%S"))

        # Create a text/plain message
        msg = MIMEText(body)

        subject = self.configuration["subject"]
        subject = subject.replace("{input}", input_message)
        subject = subject.replace("{date}", time.strftime("%d/%m/%Y"))
        subject = subject.replace("{time}", time.strftime("%H:%M:%S"))
        msg['Subject'] = subject

        msg['From'] = self.configuration["from"]
        msg['To'] = self.configuration["to"]
        if 'cc' in self.configuration:
            msg['Cc'] = self.configuration["cc"]

        try:
            smtp_obj = smtplib.SMTP(self.configuration["smtp_server"] +
                                    ":" + self.configuration["smtp_port"])
            smtp_obj.send_message(msg)
            smtp_obj.quit()
            flows.Global.LOGGER.debug("Successfully sent email")
        except Exception as exc:
            flows.Global.LOGGER.error(str(exc))
            flows.Global.LOGGER.error("Error: unable to send email")

        # returns the output
        self.send_message(body)
