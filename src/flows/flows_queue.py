#!/usr/bin/env python3

"""
FlowsWorker.py
---------

Copyright 2016-2021 Davide Mastromatteo
License: Apache-2.0
"""

import queue

class FlowsQueue():
    """
    Main queue of all the messages
    """
    def __init__(self):
        self.internal_queue = queue.Queue()

    def put(self, message):
        self.internal_queue.put(message)

    def get(self):
        if self.internal_queue.empty():
            return None

        return self.internal_queue.get()