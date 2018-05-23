#!/usr/bin/env python3

"""
__main__.py
entry point of the program
----------------------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
"""

from flows import Global
from flows.FlowsManager import FlowsManager


# ############################
# FIX FOR PYINSTALLER
# ############################
# import smtplib
# import croniter
# import tyler
# from watchdog import *
# from smtplib import *
# import adodbapi
# import logging.handlers
# import watchdog.events
# import watchdog.observers
# import email.mime
# ############################
# END FIX FOR PYINSTALLER
# ############################

def main(args=None):
    my_flows_manager = FlowsManager()

    try:
        my_flows_manager.start()
    except KeyboardInterrupt:
        Global.LOGGER.info("Quit command received")
        my_flows_manager.stop()


if __name__ == "__main__":
    main()
