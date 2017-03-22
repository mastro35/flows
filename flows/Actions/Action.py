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
import site
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

    python_files = []

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
        Global.LOGGER.debug(f"action {self.name} stopped")
        self.is_running = False
        self.on_stop()

    def run(self):
        """
        Start the action
        """
        Global.LOGGER.debug(f"action {self.name} is running")

        for tmp_monitored_input in self.monitored_input:
            sender = "*" + tmp_monitored_input + "*"
            Global.LOGGER.debug(f"action {self.name} is monitoring {sender}")

        while self.is_running:
            try:
                time.sleep(Global.CONFIG_MANAGER.sleep_interval)
                self.on_cycle()

            except Exception as exc:
                Global.LOGGER.error(f"error while running the action {self.name}: {str(exc)}")

    @staticmethod
    def load_actions():
        Global.LOGGER.debug("loading actions in memory")
        # if we load the actions yet, return them
        if len(Action.python_files) > 0:
            return Action.python_files

        # elsewere, load all the custom actions you find
        Global.LOGGER.debug("searching for installed actions... it can takes a while")
        site_packages = site.getsitepackages()

        # get custom actions in current path 
        Global.LOGGER.debug("looking inside the current directory")
        tmp_python_files_in_current_directory = glob.glob(f"./**/*Action.py", recursive=False)
        tmp_python_files_dict = dict(zip(list(map(os.path.basename, tmp_python_files_in_current_directory)), tmp_python_files_in_current_directory))

        # get custom actions in current /Action subdir
        Global.LOGGER.debug("looking inside the current ./Actions subdirectory")        
        tmp_python_files_in_current_action_subdirectory = glob.glob(f"./**/Actions/*Action.py", recursive=True)
        for action_file in tmp_python_files_in_current_action_subdirectory:
            action_filename = os.path.basename(action_file)
            if action_filename not in tmp_python_files_dict:
                tmp_python_files_dict[action_filename] = action_file

        # get custom actions in site_packages directory
        Global.LOGGER.debug("looking inside the Python environment")
        for my_site in site_packages:
            tmp_python_files_in_site_directory = glob.glob(f"{my_site}/**/Actions/*Action.py", recursive=True) 
            for action_file in tmp_python_files_in_site_directory:
                action_filename = os.path.basename(action_file)                
                if action_filename not in tmp_python_files_dict:
                    tmp_python_files_dict[action_filename] = action_file

        # Action.python_files = list(set(tmp_python_files))
        Action.python_files = tmp_python_files_dict.values()

        if len(Action.python_files) > 0:
            Global.LOGGER.debug(f"{len(Action.python_files)} actions found")

            if Global.CONFIG_MANAGER.tracing_mode:
                actions_found = "\n".join(Action.python_files)
                Global.LOGGER.debug(f"actions found: \n{actions_found}")
                # time.sleep(2)
        else:
            Global.LOGGER.debug(f"no actions found on {my_site}")
        

    @staticmethod
    def create_action_for_code(action_code, name, configuration, managed_input):
        """
        Factory method to create an instance of an Action from an input code
        """
        Global.LOGGER.debug(f"creating action {name} for code {action_code}")
        Global.LOGGER.debug(f"configuration length: {len(configuration)}")
        Global.LOGGER.debug(f"input: {managed_input}")

        Action.load_actions()
        
        # import Actions
        for path in Action.python_files:
            filename = os.path.basename(os.path.normpath(path))[:-3]
            module_name = "flows.Actions." + filename

            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug("importing " + module_name)

            try:
                importlib.import_module(module_name, package="flows.Actions")
            except ModuleNotFoundError as ex:
                Global.LOGGER.warn(f"an error occured while importing {module_name}, so the module will be skipped.")
                Global.LOGGER.debug(f"error occured : {ex}")

        action = None

        for subclass in Action.__subclasses__():
            if subclass.type == action_code:
                action_class = subclass
                action = action_class(name, configuration, managed_input)
                Global.LOGGER.debug("created action " + str(action))
                return action

        return action
