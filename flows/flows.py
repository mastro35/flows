#!/usr/bin/env python3

"""
flows.py
entry point of the program
----------------------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
"""

from flows import Global
from flows.FlowsManager import FlowsManager


def main():
    my_flows_manager = FlowsManager()

    try:
        my_flows_manager.start()
    except KeyboardInterrupt:
        Global.LOGGER.info("Quit command received")
        my_flows_manager.stop()


if __name__ == "__main__":
    main()
