#!/usr/bin/env python3

'''
WatchdogAction.py
--------------

Copyright 2016 Davide Mastromatteo
'''
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from flows.Actions.Action import Action


class DannyFileSystemEventHandler(PatternMatchingEventHandler):
    """Customized watchdog's FileSystemEventHandler"""
    delegates = None
    is_thread = True

    def __init__(self, patterns=None, ignore_patterns=None,
                 ignore_directories=False, case_sensitive=False):

        super().__init__(patterns,
                         ignore_patterns,
                         ignore_directories,
                         case_sensitive)

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

    def convert_event_to_message(self, event):

        message={"event_type":event.event_type if hasattr(event, "event_type") else "",
            "is_directory":str(event.is_directory) if hasattr(event, "is_directory") else "",
            "src_path":event.src_path if hasattr(event, "src_path") else "",
            "dest_path":event.dest_path if hasattr(event, "dest_path") else ""
        }

        return message

    def on_init(self):
        super().on_init()

        self.path = self.configuration["input"]
        if "option" in self.configuration:
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

        if "timeout" in self.configuration:
            self.timeout = int(self.configuration["timeout"])

        self.observer = Observer(self.timeout)

        self.observer.schedule(my_event_handler, self.path,
                               recursive=self.recursive_flag)
        self.observer.start()

        self.log(f"observer started on {self.path}")

    def on_stop(self):
        super().on_stop()
        self.observer.stop()
        self.observer.join()

    def on_created(self, event):
        '''Fired when something's been created'''
        self.log("something has been created")

        if self.trigger != "create":
            return
        message = self.convert_event_to_message(event)
        self.send_message(message)

    def on_modified(self, event):
        '''Fired when something's been modified'''
        self.log("something has been modified")

        if self.trigger != "modify":
            return
        message = self.convert_event_to_message(event)
        self.send_message(message)

    def on_deleted(self, event):
        '''Fired when something's been deleted'''
        self.log("something has been deleted")

        if self.trigger != "delete":
            return
        message = self.convert_event_to_message(event)
        self.send_message(message)


    def on_moved(self, event):
        '''Fired when something's been moved'''
        self.log("something has been moved")

        if self.trigger != "move":
            return
        message = self.convert_event_to_message(event)
        self.send_message(message)

    def on_any_event(self, event):
        '''Fired on any filesystem event'''
        self.log("something has happened")

        if self.trigger != "any":
            return
        message = self.convert_event_to_message(event)
        self.send_message(message)

