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

from flows import Global
from flows.FlowsWorker import FlowsWorker

__author__ = "Davide Mastromatteo"
__copyright__ = "Copyright 2016, Davide Mastromatteo"
__credits__ = [""]
__license__ = "Apache-2.0"
__version__ = Global.VERSION
__maintainer__ = "Davide Mastromatteo"
__email__ = "dave35@me.com"
__status__ = "Production/Stable"


class FlowsVentilator:

    def __init__(self):

        self.fetched: int = 0
        self.is_running: bool = False

        self.last_queue_check_count: int = 0
        self.last_queue_check_date: datetime = datetime.now()
        self.last_stats_check_date: datetime = datetime.now()

        self.workers: [FlowsWorker] = []

        Global.ZMQ_CONTEXT = zmq.Context()

    def start(self) -> None:
        self._set_manager_sockets()
        self._start_message_fetcher()

    def stop(self) -> None:
        self._stop_message_fetcher()

    def _set_manager_sockets(self) -> None:
        self.sendersocket = Global.ZMQ_CONTEXT.socket(zmq.PUSH)
        self.sendersocket.bind("tcp://*:5557")

        self.sinksocket = Global.ZMQ_CONTEXT.socket(zmq.PULL)
        self.sinksocket.bind("tcp://*:5558")

    # region MESSAGE FETCHER MANAGEMENT
    def _start_message_fetcher(self) -> None:
        """
        Start the message fetcher (called from coroutine)
        """
        Global.LOGGER.info('VENT: starting the message fetcher!!!')
        event_loop = asyncio.get_event_loop()
        try:
            Global.LOGGER.debug('VENT: entering event loop for message fetcher coroutine on the manager')
            event_loop.run_until_complete(self.message_fetcher_coroutine(event_loop))
        finally:
            Global.LOGGER.debug('VENT: closing the event loop on the manager')
            event_loop.close()

    def _stop_message_fetcher(self) -> None:
        """
        Stop the message fetcher
        :return: None
        """
        self.is_running = False

    async def message_fetcher_coroutine(self, loop) -> None:
        """
        Register callback for message fetcher coroutines
        """
        Global.LOGGER.debug('VENT: registering callbacks for message fetcher coroutine on the manager')
        self.is_running = True
        while self.is_running:
            loop.call_soon(self._fetch_messages)
            #            loop.call_soon(self._perform_system_check)
            await asyncio.sleep(Global.CONFIG_MANAGER.message_fetcher_sleep_interval)

        Global.LOGGER.debug('VENT: message fetcher stopped')

    def _fetch_messages(self) -> None:
        """
        Get an input message from the socket
        """
        try:
            msg = self.sinksocket.recv(flags=zmq.NOBLOCK)

            if Global.CONFIG_MANAGER.tracing_mode:
                Global.LOGGER.debug("VENT: the manager has fetched a new message")

            self.fetched = self.fetched + 1

            #  obj = pickle.loads(msg)
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
