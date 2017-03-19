#!/usr/bin/env python

'''
ReadFileAction.py
-----------------

Copyright 2016 Davide Mastromatteo
'''

import os.path
from flows.Actions.Action import Action


class ReadFileAction(Action):
    """
    ReadFileAction Class
    """

    type = "readfile"

    path = ""
    file = None
    file_is_opened = False
    offset_file_name = ""

    def on_init(self):
        super().on_init()

        # Normal init
        self.path = self.configuration["input"]
        self.try_opening_file()

    def try_opening_file(self):
        '''Try to open the input file'''
        if os.path.isfile(self.path):
            self.file = open(self.path, 'r')
            self.file_is_opened = True

    def on_stop(self):
        super().on_stop()
        if os.path.isfile(self.offset_file_name):
            os.remove(self.offset_file_name)

    def on_cycle(self):
        super().on_cycle()

        if not self.file_is_opened:
            self.try_opening_file()

        # Action
        line = self.file.readline()
        if len(line) == 0:
            # eof
            self.file.close()
            return

        self.send_message(line)
