#!/usr/bin/env python3

"""
FlowsVentilator.py
---------

Copyright 2016-2017 Davide Mastromatteo
License: Apache-2.0
"""

import asyncio
from datetime import datetime

import zmq

from flows import global_module as Global
from flows.flows_worker import FlowsWorker

__author__ = "Davide Mastromatteo"
__copyright__ = "Copyright 2016, Davide Mastromatteo"
__credits__ = [""]
__license__ = "Apache-2.0"
__version__ = Global.VERSION
__maintainer__ = "Davide Mastromatteo"
__email__ = "dave35@me.com"
__status__ = "Production/Stable"


class FlowsVentilator:
    """Main class for the ventilator process.
    Spawn the messages to all the workers that join the process"""

    def __init__(self):

        self.sendersocket = None
        self.sinksocket = None

        self.fetched: int = 0
        self.is_running: bool = False

        self.last_queue_check_count: int = 0
        self.last_queue_check_date: datetime = datetime.now()
        self.last_stats_check_date: datetime = datetime.now()

        self.workers: [FlowsWorker] = []
        self.loop = asyncio.get_event_loop()

        Global.ZMQ_CONTEXT = zmq.Context()

    def start(self) -> None:
        """Start the ventilator"""
        self._set_manager_sockets()
        self.is_running = True

        self.loop.run_until_complete(self._start_async_message_fetcher())

    def stop(self) -> None:
        """Stop the ventilator"""
        self._stop_message_fetcher()

    def _set_manager_sockets(self) -> None:
        """Set ZMQ Sockets"""
        self.sendersocket = Global.ZMQ_CONTEXT.socket(zmq.PUSH) # pylint: disable=E1101
        self.sendersocket.bind("tcp://*:5557")

        self.sinksocket = Global.ZMQ_CONTEXT.socket(zmq.PULL) # pylint: disable=E1101
        self.sinksocket.bind("tcp://*:5558")

    async def _start_async_message_fetcher(self):
        """
        Start the message fetcher (called from coroutine)
        """
        Global.LOGGER.info('WORK: starting the message fetcher')
        while self.is_running:
            asyncio.ensure_future(self._fetch_messages(), loop=self.loop)
            await asyncio.sleep(Global.CONFIG_MANAGER.message_fetcher_sleep_interval)

    # region MESSAGE FETCHER MANAGEMENT
    def _stop_message_fetcher(self) -> None:
        """
        Stop the message fetcher
        :return: None
        """
        self.is_running = False

    async def _fetch_messages(self) -> None:
        """
        Get an input message from the socket
        """
        try:
            msg = self.sinksocket.recv(flags=zmq.NOBLOCK) # pylint: disable=E1101

            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug("VENT: the manager has fetched a new message")

            self.fetched = self.fetched + 1

            self._deliver_message_to_worker(msg)

        except zmq.error.Again:
            return None
        except Exception as new_exception:
            Global.LOGGER.error(new_exception)
            raise new_exception

    # endregion

    def _deliver_message_to_worker(self, msg) -> None:
        """
        Deliver the message to the listening workers
        """
        self.sendersocket.send(msg)

        if Global.CONFIG_MANAGER.tracing_mode:
            Global.LOGGER.debug("VENT: delivered a new message for the listening workers")
