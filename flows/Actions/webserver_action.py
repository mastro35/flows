#!/usr/bin/env python3

'''
WebserverAction.py
------------------

Copyright 2016 Davide Mastromatteo
'''

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import flows.global_module
from flows.Actions.action import Action


class WebserverAction(Action):
    """
    WebserverAction Class
    """

    type = "webserver"

    host_name = ""
    host_port = ""

    my_server = None

    def on_init(self):
        super().on_init()
        my_hostname = self.configuration["hostname"]
        my_hostport = self.configuration["hostport"]
        self.host_name = my_hostname
        self.host_port = int(my_hostport)

        self.my_server = DannyHTTPServer(
            (self.host_name, self.host_port), MyServerRequestHandler)

        flows.global_module.LOGGER.info(str.format(
            "Server Starts - {0}:{1}", self.host_name, self.host_port))

        threading.Thread(target=self.my_server.serve_forever).start()

    def on_cycle(self):
        super().on_cycle()

        MyServerRequestHandler.message["sleep_interval"] = (
            str(flows.global_module.CONFIG_MANAGER.sleep_interval))

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)
        # Action

        MyServerRequestHandler.message[
            action_input.sender] = action_input["message"]
        self.send_message(action_input["message"])

    def on_stop(self):
        super().on_stop()
        self.my_server.stop()


class MyServerRequestHandler(BaseHTTPRequestHandler):
    """
    MyServerRequestHandler Class
    """
    message = {}

    def initialize_server(self):
        """
        Initialize the request handler for the webserver
        """
        self.message = {}

    def do_GET(self):
        """
        Handle GET WebMethod
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write(bytes(json.dumps(self.message), "utf-8"))

    def log_message(self, format, *args):
        string_to_log = str.format("{0} - - [{1}] {2}",
                                   self.address_string(),
                                   self.log_date_time_string(),
                                   format % args)
        flows.global_module.LOGGER.debug(string_to_log)


class DannyHTTPServer(HTTPServer):
    """
    DannyHTTPServer Class
    """
    is_alive = True

    def serve_forever(self, poll_interval=0.5):
        """
        Cycle for webserer
        """
        while self.is_alive:
            self.handle_request()
            time.sleep(poll_interval)

    def stop(self):
        """
        Stop the webserver
        """
        self.is_alive = False
        self.server_close()
        flows.global_module.LOGGER.info("Server Stops " + (str(self.server_address)))
