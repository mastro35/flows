"""
MailIfResponseErrorAction.py
-------------

Copyright 2016 Davide Mastromatteo
"""

import smtplib
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
import time
from flows.Actions.Action import Action


class MailIfResponseErrorAction(Action):
    """
    MailAction Class
    send an email
    """

    type = "mail_if_response_error"

    def on_init(self):
        super().on_init()

        if "smtp_server" not in self.configuration:
            raise ValueError(
                str.format(
                    "The mail action {0} is not properly configured."
                    "The smtp_server parameter is missing",
                    self.name,
                )
            )

        if "smtp_port" not in self.configuration:
            raise ValueError(
                str.format(
                    "The mail action {0} is not properly configured."
                    "The smtp_port parameter is missing",
                    self.name,
                )
            )

        if "subject" not in self.configuration:
            raise ValueError(
                str.format(
                    "The mail action {0} is not properly configured."
                    "The subject parameter is missing",
                    self.name,
                )
            )

        if "from" not in self.configuration:
            raise ValueError(
                str.format(
                    "The mail action {0} is not properly configured."
                    "The from parameter is missing",
                    self.name,
                )
            )

        if "to" not in self.configuration:
            raise ValueError(
                str.format(
                    "The mail action {0} is not properly configured."
                    "The to parameter is missing",
                    self.name,
                )
            )

        if "body" not in self.configuration:
            raise ValueError(
                str.format(
                    "The mail action {0} is not properly configured."
                    "The body parameter is missing",
                    self.name,
                )
            )

        self.url = self.configuration["url"]

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # CHECK

        status = ""

        try:
            response = urllib.request.urlopen(self.url)
            status = response.getcode()
        except urllib.error.HTTPError as err:
            status = err.code
        except urllib.error.URLError as err:
            status = ""

        if "verbose" in self.configuration:
            self.logger.info(str.format("{0} - {1}", self.name, status))

        # returns the output
        if status != 200:
            # END of check

            # Action
            input_message = str(status)

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
            msg["Subject"] = subject

            msg["From"] = self.configuration["from"]
            msg["To"] = self.configuration["to"]
            if "cc" in self.configuration:
                msg["Cc"] = self.configuration["cc"]

            try:
                smtp_obj = smtplib.SMTP(
                    self.configuration["smtp_server"]
                    + ":"
                    + self.configuration["smtp_port"]
                )
                smtp_obj.send_message(msg)
                smtp_obj.quit()
                self.logger.debug("Successfully sent email")
            except Exception as exc:
                self.logger.error(str(exc))
                self.logger.error("Error: unable to send email")

            # returns the output
            self.send_message(body)
