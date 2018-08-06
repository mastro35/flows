#!/usr/bin/env python3

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
# from threading import Thread, Lock

from flows import global_module as Global


#class Action(Thread):
class Action():
    """
    Generic abstract class that should be subclassed to create
    custom action classes.
    """

    type = ""
    name = ""
    # _instance_lock: Lock = Lock()
    configuration = None
    context = None
    socket = None
    is_running = True
    monitored_input = None
    #    my_action_input = None

    python_files = []

    def __init__(self, name, configuration, worker, managed_input):
        super().__init__()

        # Set the action as a daemon
        self.daemon = True

        # Init the action instance variables
        self.monitored_input = managed_input
        self.configuration = configuration
        self.worker = worker
        self.name = name

        # Launch custom configuration method
        self.on_init()

        # Start the action (as a thread, the run method will be executed)
        # self.start()

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
        pass

    def send_custom_dictionary(self, output) -> None:
        """
        Send a message to the socket by using a custom dictionary
        """
        output_action = {"message": "dictionary",
                         "message_dictionary": output,
                         "sender": self.name,
                         "target": "*"}

        # Global.MESSAGE_DISPATCHER.send_message(output_action)
        self.worker.message_dispatcher.send_message(output_action)

    def send_message(self, output) -> None:
        """
        Send a message to the socket
        """

        output_action = {"message": output,
                         "sender": self.name,
                         "target": "*"}

        # Global.MESSAGE_DISPATCHER.send_message(output_action)
        self.worker.message_dispatcher.send_message(output_action)

    def stop(self):
        """ Stop the current action """
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

            except Exception as exc: # pylint: disable=W0703
                Global.LOGGER.error(f"error while running the action {self.name}: {str(exc)}")

    @classmethod
    def load_module(cls, module_name, module_filename):
        """
        Load a single module passed as parameter
        """
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_filename)
            my_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(my_module)
        except Exception as ex: # pylint: disable=W0703
            Global.LOGGER.warn(f"{ex}")
            Global.LOGGER.warn(f"an error occurred while importing {module_name}"
                               f", so the module will be skipped.")

    @classmethod
    def search_actions(cls):
        """
        Search for all the installed actions
        """
        # if we load the actions yet, return them
        if Action.python_files:
            return Action.python_files

        # elsewere, load all the custom actions you find
        Global.LOGGER.debug("searching for installed actions... it can takes a while")

        site_packages = []

        try:
            site_packages = site.getsitepackages()
        except AttributeError as ex:
            Global.LOGGER.warn(f"{ex}")
            Global.LOGGER.warn(f"Perhaps you're using a PyInstaller package?")

            # This try/except block is needed for the use with PyInstaller, because
            # in this case you don't have any site and the getsitepackages would raise
            # an AttributeError Exception.

        Global.LOGGER.debug(f"current path: {os.getcwd()}")
        # get custom actions in current path
        Global.LOGGER.debug("looking inside the current directory")
        py_files_in_current_directory = glob.glob(f"{os.getcwd()}/*Action.py",
                                                  recursive=False)
        Global.LOGGER.debug(f"found {len(py_files_in_current_directory)} \
                              actions in current directory")
        basenames = list(map(os.path.basename, py_files_in_current_directory))
        tmp_python_files_dict = dict(zip(basenames, py_files_in_current_directory))

        # get custom actions in current /Action subdir
        Global.LOGGER.debug("looking inside any ./Actions subdirectory")
        py_files_in_this_action_subdir = glob.glob(f"{os.getcwd()}"
                                                   f"/**/Actions/*Action.py",
                                                   recursive=True)
        Global.LOGGER.debug(f"found "
                            f"{len(py_files_in_this_action_subdir)}"
                            f" actions in a ./Actions subdirectory")
        for action_file in py_files_in_this_action_subdir:
            action_filename = os.path.basename(action_file)
            if action_filename not in tmp_python_files_dict:
                tmp_python_files_dict[action_filename] = action_file

        # get custom actions in site_packages directory
        Global.LOGGER.debug("looking inside the Python environment")
        for my_site in site_packages:
            python_files_in_site_directory = \
                glob.glob(f"{my_site}/**/Actions/*Action.py", recursive=True)
            Global.LOGGER.debug(f"found "
                                f"{len(python_files_in_site_directory)}"
                                f" actions in {my_site}")

            for action_file in python_files_in_site_directory:
                action_filename = os.path.basename(action_file)
                if action_filename not in tmp_python_files_dict:
                    tmp_python_files_dict[action_filename] = action_file

        # Action.python_files = list(set(tmp_python_files))
        action_files = tmp_python_files_dict.values()

        if action_files:
            Global.LOGGER.debug(f"{len(action_files)} actions found")

            if Global.CONFIG_MANAGER.tracing_mode:
                actions_found = "\n".join(action_files)
                Global.LOGGER.debug(f"actions found: \n{actions_found}")
        else:
            Global.LOGGER.debug(f"no actions found")

        Action.python_files = action_files

        return action_files

    @classmethod
    def create_action_for_code(cls, action_code, name, configuration, worker, managed_input):
        """
        Factory method to create an instance of an Action from an input code
        """
        Global.LOGGER.debug(f"creating action {name} for code {action_code}")
        Global.LOGGER.debug(f"configuration length: {len(configuration)}")
        Global.LOGGER.debug(f"input: {managed_input}")

        # get the actions catalog
        my_actions_file = Action.search_actions()

        # load custom actions to find the right one
        for filename in my_actions_file:
            module_name = os.path.basename(os.path.normpath(filename))[:-3]

            # garbage collect all the modules you load if they are not necessary
            #            context = {}
            Action.load_module(module_name, filename)
            for subclass in Action.__subclasses__():
                if subclass.type == action_code:
                    action_class = subclass
                    action = action_class(name, configuration, worker, managed_input)
                    return action
            #            subclass = None
            gc.collect()
