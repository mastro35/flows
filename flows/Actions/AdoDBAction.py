# #!/usr/bin/env python

# '''
# AdoDBAction.py
# ----------------------

# Copyright 2016 Davide Mastromatteo
# License: Apache-2.0
# '''

import adodbapi
from flows.Actions.Action import Action


class AdoDBAction(Action):
    """
    AdoDBAction Class
    """

    type = "adodb"

    conn = None
    query = None
    separator = ";"

    def on_init(self):
        super().on_init()

        connstring = self.configuration['connstring']
        # server = self.configuration['server']
        # user = self.configuration['user']
        # password = self.configuration['password']
        # dbname = self.configuration['dbname']

        # self.conn = pymssql.connect(
        #     server, user, password, dbname)

        self.conn = adodbapi.connect(connstring)

        self.query = self.configuration['query']
        if 'separator' in self.configuration:
            self.separator = self.configuration['separator']

    def on_stop(self):
        super().on_stop()
        self.conn.close()

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # Action
        if self.conn is not None and self.query is not None:
            cursor = self.conn.cursor()
            cursor.execute(self.query)

            row = cursor.fetchone()

            return_value = self.separator.join(map(str, row))
            self.send_message(return_value)
