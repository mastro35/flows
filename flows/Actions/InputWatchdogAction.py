#!/usr/bin/env python

'''
WatchdogAction.py
--------------

Copyright 2016 Davide Mastromatteo
'''

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from flows.Actions.Action import Action
from flows.Actions.Action import ActionInput
import flows.Global


class DannyFileSystemEventHandler(PatternMatchingEventHandler):
    """Customized watchdog's FileSystemEventHandler"""
    delegates = None

    def __init__(self, patterns=None, ignore_patterns=None,
                 ignore_directories=False, case_sensitive=False):

        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)

        self.delegates = []

    def on_any_event(self, event):
        """On any event method"""
        for delegate in self.delegates:
            if hasattr(delegate, "on_any_event"):
                delegate.on_any_event(event)

    def on_created(self, event):
        """On created method"""
        for delegate in self.delegates:
            if hasattr(delegate, "on_created"):
                delegate.on_created(event)

    def on_deleted(self, event):
        """On deleted method"""
        for delegate in self.delegates:
            if hasattr(delegate, "on_deleted"):
                delegate.on_deleted(event)

    def on_modified(self, event):
        """On modified method"""
        for delegate in self.delegates:
            if hasattr(delegate, "on_modified"):
                delegate.on_modified(event)

    def on_moved(self, event):
        """On moved method"""
        for delegate in self.delegates:
            if hasattr(delegate, "on_moved"):
                delegate.on_moved(event)


class WatchdogAction(Action):
    """
    WatchdogAction Class
    """

    type = "watchdog"

    observer = None
    path = ""
    trigger = ""
    recursive_flag = False
    patterns = None
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = False

    timeout = 1

    def on_init(self):
        super().on_init()

        self.path = self.configuration["input"]
        self.recursive_flag = (
            str.lower(self.configuration["option"]) == "recursive")
        self.trigger = self.configuration["monitor"]

        if "patterns" in self.configuration:
            self.patterns = self.configuration["patterns"].split(" ")

        if "ignore_patterns" in self.configuration:
            self.ignore_patterns = self.configuration[
                "ignore_patterns"].split(" ")

        if "ignore_directories" in self.configuration:
            self.ignore_directories = True

        if "case_sensitive" in self.configuration:
            self.case_sensitive = True

        my_event_handler = DannyFileSystemEventHandler(self.patterns,
                                                       self.ignore_patterns,
                                                       self.ignore_directories,
                                                       self.case_sensitive)
        my_event_handler.delegates.append(self)

        # if "polling" in self.configuration:
        # self.observer = PollingObserver(1)
        # else:
        if "timeout" in self.configuration:
            self.timeout = int(self.configuration["timeout"])

        self.observer = Observer(self.timeout)

        self.observer.schedule(my_event_handler, self.path,
                               recursive=self.recursive_flag)
        self.observer.start()

    def on_stop(self):
        super().on_stop()
        self.observer.stop()
        self.observer.join()

    def on_created(self, event):
        '''Fired when something's been created'''
        if self.trigger != "create":
            return
        action_input = ActionInput(event, "", self.name)
        flows.Global.MESSAGE_DISPATCHER.send_message(action_input)

    def on_modified(self, event):
        '''Fired when something's been modified'''
        if self.trigger != "modify":
            return
        action_input = ActionInput(event, "", self.name)
        flows.Global.MESSAGE_DISPATCHER.send_message(action_input)

    def on_deleted(self, event):
        '''Fired when something's been deleted'''
        if self.trigger != "delete":
            return
        action_input = ActionInput(event, "", self.name)
        flows.Global.MESSAGE_DISPATCHER.send_message(action_input)

    def on_moved(self, event):
        '''Fired when something's been moved'''
        if self.trigger != "move":
            return
        action_input = ActionInput(event, "", self.name)
        flows.Global.MESSAGE_DISPATCHER.send_message(action_input)

    def on_any_event(self, event):
        '''Fired on any filesystem event'''
        if self.trigger != "any":
            return
        action_input = ActionInput(event, "", self.name)
        flows.Global.MESSAGE_DISPATCHER.send_message(action_input)
