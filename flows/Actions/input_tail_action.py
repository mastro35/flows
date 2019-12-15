#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
TailAction.py
-------------

Copyright 2016 Davide Mastromatteo
'''

import datetime
import os.path
import re
import tyler
from flows.Actions.Action import Action


class TailAction(Action):
    """
    TailAction Class
    """

    type = "tail"
    is_thread = True
    my_log_file = None
    file_is_opened = False
    last_flush_date = datetime.datetime.now()

    def on_init(self):
        super().on_init()

        # Normal init
        self.path = self.configuration["input"]
        self.buffer = []
        self.timeout = 3

        self.file_is_opened = False
        self.regex = ""

        self.enable_buffer = False
        if "regex_new_buffer" in self.configuration:
            self.regex = self.configuration["regex_new_buffer"]
            self.enable_buffer = True

        if "timeout" in self.configuration:
            self.timeout = int(self.configuration["regex_new_buffer"])

        if os.path.isfile(self.path):
            self.my_log_file = tyler.Tyler(self.path)

        self.try_opening_file()

    def try_opening_file(self):
        '''Try to open the input file'''
        # read all the file to tail til the end...
        if os.path.isfile(self.path):
            self.my_log_file = tyler.Tyler(self.path)
            try:
                for _ in self.my_log_file:
                    pass
            except StopIteration:
                pass

            self.file_is_opened = True

    def bufferize_line(self, line):
        ''' Insert a new line into the buffer '''
        self.buffer.append(line)

    def flush_buffer(self):
        ''' Flush the buffer of the tail '''
        if self.buffer:
            return_value = ''.join(self.buffer)
            self.buffer.clear()
            self.send_message(return_value)
            self.last_flush_date = datetime.datetime.now()

    def on_cycle(self):
        super().on_cycle()

        # tailing...
        for line in self.my_log_file:
            # WITHOUT BUFFER:
            if not self.enable_buffer:
                self.send_message(line)
                return

            # WITH BUFFER:
            match = re.search(self.regex, line)

            # if the input line is NOT a new buffer expression no match
            if match is None:
                # bufferize and return
                self.bufferize_line(line)
                return

            # if the input line is the start of a new buffer,
            # flush the buffer and bufferize the new line
            self.flush_buffer()
            self.bufferize_line(line)

        # If there's been something in the buffer for a long time, flush the buffer
        # the default value is 3 seconds
        if (datetime.datetime.now() - self.last_flush_date).total_seconds() > self.timeout:
            self.flush_buffer()
