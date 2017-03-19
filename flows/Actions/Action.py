#!/usr/bin/env python

'''
Action.py
Action superclasses
-------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

import glob
import importlib
import importlib.util
import os
import time
from threading import Thread

from flows import Global


class ActionInput:
    """
    Standard input for every action in flows
    """
    sender = ""
    receiver = ""
    message = ""
    file_system_event = None

    def __init__(self, event, message, sender, receiver="*"):
        super().__init__()
        self.message = message
        self.file_system_event = event
        self.sender = sender
        self.receiver = receiver


class Action(Thread):
    """
    Generic abstract class that should be subclassed to create
    custom action classes.
    """

    type = ""
    name = ""
    configuration = None
    context = None
    socket = None
    is_running = True
    monitored_input = None
    my_action_input = None

    def __init__(self, name, configuration, managed_input):
        super().__init__()

        # Set the action as a daemon
        self.daemon = True

        # Init the action instance variables
        self.monitored_input = managed_input
        self.configuration = configuration
        self.name = name

        # Launch custom configuration method
        self.on_init()

        # Start the action (as a thread, the run method will be executed)
        self.start()

    def on_init(self):
        """
        Initialization of the action, code to be executed before start
        """
        pass

    def on_cycle(self):
        """
        Main cycle of the action, code to be executed before the start of each cycle
        """
        pass

    def on_input_received(self, action_input=None):
        """
        Fire the current action
        """
        pass

    def on_stop(self):
        """
        Code to be executed before end
        """

    def send_output(self, output):
        """
        Send an output to the socket
        """
        Global.MESSAGE_DISPATCHER.send_message(output)

    def send_message(self, output):
        """
        Send a message to the socket
        """

        file_system_event = None
        if self.my_action_input:
            file_system_event = self.my_action_input.file_system_event or None

        output_action = ActionInput(file_system_event,
                                    output,
                                    self.name,
                                    "*")

        Global.MESSAGE_DISPATCHER.send_message(output_action)

    def stop(self):
        ''' Stop the current action '''
        Global.LOGGER.debug("..." + self.name + " stopped")
        self.is_running = False
        self.on_stop()

    def run(self):
        """
        Start the action
        """

        Global.LOGGER.debug("RUNNING - " + self.name + " " + str(len(self.monitored_input)))

        for tmp_monitored_input in self.monitored_input:
            sender = "*" + tmp_monitored_input + "*"
            Global.LOGGER.debug(self.name + " is monitoring " + sender)

        while self.is_running:
            try:
                time.sleep(Global.CONFIG_MANAGER.sleep_interval)
                self.on_cycle()

            except Exception as exc:
                Global.LOGGER.error(
                    "Error while running the action " + self.name + " \n " + str(exc))

    @staticmethod
    def create_action_for_code(action_code, name, configuration, managed_input):
        """
        Factory method to create an instance of an Action from an input code
        """
        debug = "debug" in configuration

        python_files = glob.glob("./**/Actions/*Action.py", recursive=True)
        if debug:
            print("Actions found: " + str(python_files))

        # import Actions
        for path in python_files:
            filename = os.path.basename(os.path.normpath(path))[:-3]
            module_name = "flows.Actions." + filename
            Global.LOGGER.debug("...importing " + module_name)
            importlib.import_module(module_name, package="flows.Actions")

        action = None

        for subclass in Action.__subclasses__():
            if debug:
                print("checking if the action is " + str(subclass.type))
            if subclass.type == action_code:
                action_class = subclass
                action = action_class(name, configuration, managed_input)
                Global.LOGGER.debug("...created action " + str(action))
                return action

        return action
