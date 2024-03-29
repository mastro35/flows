"""
Action.py
Action superclasses
-------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
"""

import gc
import glob
import importlib
import importlib.util
import os
import site
import time
import threading
from threading import Thread

from flows.ConfigManager import ConfigManager
from flows.FlowsLogger import FlowsLogger
from flows.MessageDispatcher import MessageDispatcher


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
    _instance_lock = threading.Lock()
    configuration = None
    context = None
    socket = None
    is_running = True
    monitored_input: list
    my_action_input = None
    LOGGER = FlowsLogger.default_instance().get_logger()
    CONFIG_MANAGER = ConfigManager.default_instance()
    MESSAGE_DISPATCHER = MessageDispatcher.default_instance()

    python_files = []

    def __init__(self, name: str, configuration, managed_input: list):
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
        self.MESSAGE_DISPATCHER.send_message(output)

    def send_message(self, output):
        """
        Send a message to the socket
        """

        file_system_event = None
        if self.my_action_input:
            file_system_event = self.my_action_input.file_system_event or None

        output_action = ActionInput(file_system_event, output, self.name, "*")

        self.MESSAGE_DISPATCHER.send_message(output_action)

    def stop(self):
        """Stop the current action"""
        self.LOGGER.debug(f"action {self.name} stopped")
        self.is_running = False
        self.on_stop()

    def run(self):
        """
        Start the action
        """
        self.LOGGER.debug(f"action {self.name} is running")

        for tmp_monitored_input in self.monitored_input:
            sender = "*" + tmp_monitored_input + "*"
            self.LOGGER.debug(f"action {self.name} is monitoring {sender}")

        while self.is_running:
            try:
                time.sleep(self.CONFIG_MANAGER.sleep_interval)
                self.on_cycle()

            except Exception as exc:
                self.LOGGER.error(
                    f"error while running the action {self.name}: {str(exc)}"
                )

    @classmethod
    def load_module(cls, module_name, module_filename):
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_filename)
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
        except Exception as ex:
            cls.LOGGER.warn(f"{ex}")
            cls.LOGGER.warn(
                f"an error occured while importing {module_name}, so the module will be skipped."
            )

    @classmethod
    def search_actions(cls):
        # if we load the actions yet, return them
        if len(Action.python_files) > 0:
            return Action.python_files

        # elsewere, load all the custom actions you find
        cls.LOGGER.debug("searching for installed actions... it can takes a while")
        site_packages = site.getsitepackages()

        cls.LOGGER.debug(f"current path: {os.getcwd()}")
        # get custom actions in current path
        cls.LOGGER.debug("looking inside the current directory")
        tmp_python_files_in_current_directory = glob.glob(
            f"{os.getcwd()}/*Action.py", recursive=False
        )
        cls.LOGGER.debug(
            f"found {len(tmp_python_files_in_current_directory)} actions in current directory"
        )
        basenames = list(map(os.path.basename, tmp_python_files_in_current_directory))
        tmp_python_files_dict = dict(
            zip(basenames, tmp_python_files_in_current_directory)
        )

        # get custom actions in current /Action subdir
        cls.LOGGER.debug("looking inside any ./Actions subdirectory")
        tmp_python_files_in_current_action_subdirectory = glob.glob(
            f"{os.getcwd()}/**/Actions/*Action.py", recursive=True
        )
        cls.LOGGER.debug(
            f"found {len(tmp_python_files_in_current_action_subdirectory)} actions in a ./Actions subdirectory"
        )
        for action_file in tmp_python_files_in_current_action_subdirectory:
            action_filename = os.path.basename(action_file)
            if action_filename not in tmp_python_files_dict:
                tmp_python_files_dict[action_filename] = action_file

        # get custom actions in site_packages directory
        cls.LOGGER.debug("looking inside the Python environment")
        for my_site in site_packages:
            tmp_python_files_in_site_directory = glob.glob(
                f"{my_site}/**/Actions/*Action.py", recursive=True
            )
            cls.LOGGER.debug(
                f"found {len(tmp_python_files_in_site_directory)} actions in {my_site}"
            )

            for action_file in tmp_python_files_in_site_directory:
                action_filename = os.path.basename(action_file)
                if action_filename not in tmp_python_files_dict:
                    tmp_python_files_dict[action_filename] = action_file

        # Action.python_files = list(set(tmp_python_files))
        action_files = tmp_python_files_dict.values()

        if len(action_files) > 0:
            cls.LOGGER.debug(f"{len(action_files)} actions found")

            if cls.CONFIG_MANAGER.tracing_mode:
                actions_found = "\n".join(action_files)
                cls.LOGGER.debug(f"actions found: \n{actions_found}")
        else:
            cls.LOGGER.debug(f"no actions found on {my_site}")

        Action.python_files = action_files

        return action_files

    @classmethod
    def create_action_for_code(cls, action_code, name, configuration, managed_input):
        """
        Factory method to create an instance of an Action from an input code
        """
        cls.LOGGER.debug(f"creating action {name} for code {action_code}")
        cls.LOGGER.debug(f"configuration length: {len(configuration)}")
        cls.LOGGER.debug(f"input: {managed_input}")

        # get the actions catalog
        my_actions_file = Action.search_actions()

        # load custom actions to find the right one
        for filename in my_actions_file:
            module_name = os.path.basename(os.path.normpath(filename))[:-3]

            # garbage collect all the modules you load if they are not necessary
            context = {}
            Action.load_module(module_name, filename)
            for subclass in Action.__subclasses__():
                if subclass.type == action_code:
                    action_class = subclass
                    action = action_class(name, configuration, managed_input)
                    return action
            subclass = None
            gc.collect()
