#!/usr/bin/env python3

"""
FlowsManager.py
---------

Copyright 2016-2017 Davide Mastromatteo
License: Apache-2.0
"""

import argparse
import logging

import zmq

import config_manager
import flows_logger
import flows_ventilator
import flows_worker
import global_module as Global

__author__ = "Davide Mastromatteo"
__copyright__ = "Copyright 2016, Davide Mastromatteo"
__credits__ = [""]
__license__ = "Apache-2.0"
__version__ = Global.VERSION
__maintainer__ = "Davide Mastromatteo"
__email__ = "dave35@me.com"
__status__ = "Production/Stable"


def _parse_input_parameters():
    """Set the configuration for the Logger
    """
    Global.LOGGER.debug("VENT: define and parsing command line arguments")
    parser = argparse.ArgumentParser(description='A workflow engine for Pythonistas',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('FILENAME',
                        nargs='+',
                        help='name of the recipe file(s)')
    # parser.add_argument('-i', '--INTERVAL', type=int, default=500,
    #                     metavar=('MS'),
    #                     help='perform a cycle each [MS] milliseconds. (default = 500)')

    # parser.add_argument('-m', '--MESSAGEINTERVAL', type=int,
    #                     metavar=('X'),
    #                     help='dequeue a message each [X] tenth of milliseconds. (default = auto)')
    # parser.add_argument('-s', '--STATS', type=int, default=0,
    #                     metavar=('SEC'),
    #                     help='show stats each [SEC] seconds. (default = NO STATS)')
    parser.add_argument('-t', '--TRACE', action='store_true',
                        help='enable super verbose output, only useful for tracing')
    parser.add_argument('-v', '--VERBOSE', action='store_true', help='enable verbose output')
    parser.add_argument('-V', '--VERSION',
                        action="version", version=__version__)

    args = parser.parse_args()
    return args


def _set_command_line_arguments(args):
    """Set internal configuration variables
    according to the input parameters
    """
    Global.LOGGER.debug("VENT: setting command line arguments")

    if args.VERBOSE:
        Global.LOGGER.debug("VENT: verbose mode active")
        Global.CONFIG_MANAGER.log_level = logging.DEBUG
        Global.LOGGER_INSTANCE.reconfigure_log_level()

    if args.TRACE:
        Global.LOGGER.debug("VENT: tracing mode active")
        Global.CONFIG_MANAGER.tracing_mode = True
        Global.CONFIG_MANAGER.log_level = logging.DEBUG
        Global.LOGGER_INSTANCE.reconfigure_log_level()

    # if args.STATS > 0:
    #     Global.LOGGER.debug(f"VENT: stats requested every {args.STATS} seconds")
    #     Global.CONFIG_MANAGER.show_stats = True
    #     Global.CONFIG_MANAGER.stats_timeout = args.STATS

    # if args.INTERVAL > 0:
    #     Global.LOGGER.debug(f"VENT: setting sleep interval to {args.INTERVAL} milliseconds")
    #     Global.CONFIG_MANAGER.sleep_interval = float(args.INTERVAL)/1000

    # if  args.MESSAGEINTERVAL is not None and args.MESSAGEINTERVAL > 0:
    #     Global.LOGGER.debug(
    #     f"VENT: setting message fetcher sleep interval to {args.MESSAGEINTERVAL/10} milliseconds")
    #     Global.CONFIG_MANAGER.message_fetcher_sleep_interval =  float(args.MESSAGEINTERVAL)/10000
    #     Global.CONFIG_MANAGER.fixed_message_fetcher_interval = True

    Global.LOGGER.debug(f"VENT: recipes to be parsed: {args.FILENAME}")
    Global.CONFIG_MANAGER.recipes = args.FILENAME


class FlowsManager:
    """Orchestrator of the program
    """
    def __init__(self):
        self.workers = []
        self.ventilator = None

        Global.LOGGER_INSTANCE = flows_logger.FlowsLogger.default_instance()
        Global.LOGGER = Global.LOGGER_INSTANCE.get_logger()
        Global.CONFIG_MANAGER = config_manager.ConfigManager.default_instance()

        _set_command_line_arguments(_parse_input_parameters())

        Global.ZMQ_CONTEXT = zmq.Context()

    # region WORKERS MANAGEMENT
    def _start_workers(self):
        my_worker = flows_worker.FlowsWorker()
        self.workers.append(my_worker)

    def _stop_workers(self):
        for worker in self.workers:
            Global.LOGGER.debug(f"VENT: stopping worker {worker}")
            worker.stop()

    # endregion

    # region VENTILATOR MANAGEMENT
    def _start_ventilator(self):
        self.ventilator = flows_ventilator.FlowsVentilator()
        self.ventilator.start()

    def _stop_ventilator(self):
        self.ventilator.stop()

    # endregion

    def start(self):
        """Start all the processes
        """
        Global.LOGGER.info("MNGR: starting the workers")
        self._start_workers()

        Global.LOGGER.info("MNGR: starting the ventilator")
        self._start_ventilator()

    def stop(self):
        """Stop all the processes
        """
        Global.LOGGER.info("MNGR: stopping the workers")
        self._stop_workers()

        Global.LOGGER.info("MNGR: stopping the ventilator")
        self._stop_ventilator()

    def restart(self):
        """Restart all the processes
        """
        Global.LOGGER.info("MNGR: restarting")
        self.stop()
        self.start()

    # def _perform_system_check(self):
    #     """
    #     Perform a system check to define if we need to throttle to handle
    #     all the incoming messages
    #     """
    #     if Global.CONFIG_MANAGER.tracing_mode:
    #         Global.LOGGER.debug("VENT: performing a system check")
    #
    #     now = datetime.datetime.now()
    #     sent = Global.MESSAGE_DISPATCHER.dispatched
    #     received = self.fetched
    #     queue_length = sent - received
    #     message_sleep_interval = Global.CONFIG_MANAGER.message_fetcher_sleep_interval
    #
    #     if Global.CONFIG_MANAGER.show_stats:
    #         if (now - self.last_stats_check_date).total_seconds() \
    #           > Global.CONFIG_MANAGER.stats_timeout:
    #             self.last_stats_check_date = now
    #              stats_string = f"VENT: showing stats\n" \
    #                             f"--- [STATS] ---\n" \
    #                             f"Message Sent: {sent}\n" \
    #                             f"Message Received: {received}\n" \
    #                             f"Message Sleep Interval = {message_sleep_interval}\n" \
    #                             f"Queue length = {queue_length}\n" \
    #                             f"--- [ END ] ---"
    #             Global.LOGGER.info(stats_string)
    #
    #     # if we are accumulating messages, or we have processed at least 5000 messages
    #     # since last check, we need to speed up the process
    #      messages_limit_reached = sent - self.last_queue_check_count > \
    #                               Global.CONFIG_MANAGER.messages_dispatched_for_system_check
    #     queue_limit_reached = queue_length > Global.CONFIG_MANAGER.queue_length_for_system_check
    #      time_limit_since_last_check_is_over = (now - \
    #                                      self.last_queue_check_date).total_seconds() > \
    #                                            Global.CONFIG_MANAGER.seconds_between_queue_check
    #
    #     if not Global.CONFIG_MANAGER.fixed_message_fetcher_interval:
    #         if (messages_limit_reached) or \
    #                    (queue_limit_reached and time_limit_since_last_check_is_over):
    #             cause = "messages limit reached"
    #                     if messages_limit_reached else "queue limit reached"
    #             Global.LOGGER.debug(f"VENT: triggering the throttle function due to {cause}")
    #             self._adapt_sleep_interval(sent, received, queue_length, now)

    # def _adapt_sleep_interval(self, sent, received, queue, now):
    #     """
    #     Adapt sleep time based on the number of the messages in queue
    #     """
    #     Global.LOGGER.debug("VENT: adjusting sleep interval")
    #
    #     dispatched_since_last_check = sent - self.last_queue_check_count
    #     seconds_since_last_check = (
    #         now - self.last_queue_check_date).total_seconds()
    #
    #     Global.LOGGER.debug(
    #         str(dispatched_since_last_check) + " dispatched in the last "
    #            + str(seconds_since_last_check))
    #     sleep_time = (seconds_since_last_check /
    #                   (dispatched_since_last_check + queue + 1)) * 0.75
    #
    #     if sleep_time > 0.5:
    #         sleep_time = 0.5
    #
    #     if sleep_time < 0.0001:
    #         sleep_time = 0.0001
    #
    #     self.last_queue_check_date = now
    #     self.last_queue_check_count = sent
    #
    #     Global.CONFIG_MANAGER.message_fetcher_sleep_interval = sleep_time
    #
    #     sleep_interval_log_string = f"VENT: new sleep_interval = {sleep_time}"
    #     Global.LOGGER.debug(sleep_interval_log_string)
    #
    #     if Global.CONFIG_MANAGER.show_stats:
    #         Global.LOGGER.info(sleep_interval_log_string)
