"""
Action.py
Action superclasses
-------------------

Copyright 2016-2024 Davide Mastromatteo
License: GPL-2.0
"""

import gc
import glob
import importlib
import importlib.util
import os
import site
import time

from threading import Lock, Thread

from flows.ConfigManager import ConfigManager
from flows.FlowsLogger import FlowsLogger
from flows.MessageDispatcher import MessageDispatcher


class Action(Thread):
    """
    Generic abstract class that should be subclassed to create
    custom action classes.
    """

    type = ""
    name = ""
    _instance_lock = Lock()
    configuration = None
    context = None
    socket = None
    is_running = True
    monitored_input: list
    my_action_input = None
    logger = FlowsLogger.default_instance().get_logger()
    config_manager = ConfigManager.default_instance()
    message_dispatcher = MessageDispatcher.default_instance()

    python_files = []

    def __init__(self, name: str, configuration, managed_input: list):
        """
        Main constructor of the Action class
        """
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
        pass

    def send_output(self, output):
        """
        Send an output to the socket
        """
        self.message_dispatcher.send_message(output)

    def log(self, message):
        """
        Log a messge
        """
        self.logger.debug(message)

    def send_message(self, output):
        """
        Send a message to the socket
        """
        output_message = {"message": output, "sender": self.name, "target": "*"}
        self.message_dispatcher.send_message(output_message)

    def stop(self):
        """
        Stop the current action
        """
        self.logger.debug(f"action {self.name} stopped")
        self.is_running = False
        self.on_stop()

    def run(self):
        """
        Start the action
        """
        self.logger.debug(f"action {self.name} is running")

        for tmp_monitored_input in self.monitored_input:
            sender = "*" + tmp_monitored_input + "*"
            self.logger.debug(f"action {self.name} is monitoring {sender}")

        while self.is_running:
            try:
                time.sleep(self.config_manager.sleep_interval)
                self.on_cycle()

            except Exception as exc:
                self.logger.error(
                    f"error while running the action {self.name}: {str(exc)}"
                )

    @classmethod
    def load_module(cls, module_name, module_filename):
        """
        Load a module at runtime
        """
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as ex:
            cls.logger.warn(f"{ex}")
            cls.logger.warn(
                f"an error occured while importing {module_name}, so the module will be skipped."
            )

    @classmethod
    def search_actions(cls):
        """
        Search and load the usable actions
        """
        # if we load the actions yet, return them
        if len(Action.python_files) > 0:
            return Action.python_files

        # else, load all the custom actions you find
        cls.logger.debug("searching for installed actions... it can takes a while")
        site_packages = site.getsitepackages()

        cls.logger.debug(f"current path: {os.getcwd()}")
        # get custom actions in current path

        cls.logger.debug("looking inside the current directory")
        tmp_python_files_in_current_directory = glob.glob(
            f"{os.getcwd()}/*Action.py", recursive=False
        )

        cls.logger.debug(
            f"found {len(tmp_python_files_in_current_directory)} actions in current directory"
        )

        basenames = list(map(os.path.basename, tmp_python_files_in_current_directory))
        tmp_python_files_dict = dict(
            zip(basenames, tmp_python_files_in_current_directory)
        )

        # get custom actions in current /Action subdir
        cls.logger.debug("looking inside any ./Actions subdirectory")
        tmp_python_files_in_current_action_subdirectory = glob.glob(
            f"{os.getcwd()}/**/Actions/*Action.py", recursive=True
        )

        cls.logger.debug(
            f"found {len(tmp_python_files_in_current_action_subdirectory)} actions in a ./Actions subdirectory"
        )
        for action_file in tmp_python_files_in_current_action_subdirectory:
            action_filename = os.path.basename(action_file)
            if action_filename not in tmp_python_files_dict:
                tmp_python_files_dict[action_filename] = action_file

        # get custom actions in site_packages directory
        cls.logger.debug("looking inside the Python environment")
        for my_site in site_packages:
            tmp_python_files_in_site_directory = glob.glob(
                f"{my_site}/**/Actions/*Action.py", recursive=True
            )

            cls.logger.debug(
                f"found {len(tmp_python_files_in_site_directory)} actions in {my_site}"
            )

            for action_file in tmp_python_files_in_site_directory:
                action_filename = os.path.basename(action_file)
                if action_filename not in tmp_python_files_dict:
                    tmp_python_files_dict[action_filename] = action_file

        # Action.python_files = list(set(tmp_python_files))
        action_files = tmp_python_files_dict.values()

        if len(action_files) > 0:
            cls.logger.debug(f"{len(action_files)} actions found")

            if cls.config_manager.tracing_mode:
                actions_found = "\n-->".join(action_files)
                cls.logger.debug(f"actions found: \n-->{actions_found}")
        else:
            cls.logger.debug(f"no actions found")

        Action.python_files = action_files

        return action_files

    @classmethod
    def create_action_for_code(cls, action_code, name, configuration, managed_input):
        """
        Factory method to create an instance of an Action from an input code
        """
        cls.logger.debug(f"creating action {name} for code {action_code}")
        cls.logger.debug(f"configuration length: {len(configuration)}")
        cls.logger.debug(f"input: {managed_input}")

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
