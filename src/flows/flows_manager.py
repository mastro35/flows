#!/usr/bin/env python3

"""
FlowsManager.py
---------

Copyright 2016-2021 Davide Mastromatteo
License: Apache-2.0
"""

import argparse
import config_manager
import logging
import time
import flows_logger
import flows_queue
import flows_worker
import global_module as Global
import queue
import ray

__author__ = "Davide Mastromatteo"
__copyright__ = "Copyright 2016-2021, Davide Mastromatteo"
__credits__ = [""]
__license__ = "Apache-2.0"
__version__ = Global.VERSION
__maintainer__ = "Davide Mastromatteo"
__email__ = "mastro35@gmail.com"
__status__ = "Production/Stable"


def _parse_input_parameters():
    """
    Set the configuration for the Logger
    """
    Global.LOGGER.debug("MNGR: define and parsing command line arguments")
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
    """
    Set internal configuration variables
    according to the input parameters
    """
    Global.LOGGER.debug("MNGR: setting command line arguments")

    if args.VERBOSE:
        Global.LOGGER.debug("MNGR: verbose mode active")
        Global.CONFIG_MANAGER.log_level = logging.DEBUG
        Global.LOGGER_INSTANCE.reconfigure_log_level()

    if args.TRACE:
        Global.LOGGER.debug("MNGR: tracing mode active")
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

    Global.LOGGER.debug(f"MNGR: recipes to be parsed: {args.FILENAME}")
    Global.CONFIG_MANAGER.recipes = args.FILENAME

class FlowsManager:
    """
    Orchestrator of the program
    """
    def __init__(self):
        self.workers = []

        Global.LOGGER_INSTANCE = flows_logger.FlowsLogger.default_instance()
        Global.LOGGER = Global.LOGGER_INSTANCE.get_logger()
        Global.CONFIG_MANAGER = config_manager.ConfigManager.default_instance()

        _set_command_line_arguments(_parse_input_parameters())
        
        # ray.init()
        ray.init(address='auto', _redis_password='5241590000000000')
        self.is_running = True

    # region WORKERS MANAGEMENT
    def _start_workers(self):
        my_worker = flows_worker.FlowsWorker()
        self.workers.append(my_worker)
        while self.is_running:
            time.sleep(0.1)

    def _stop_workers(self):
        for worker in self.workers:
            Global.LOGGER.debug(f"MNGR: stopping worker {worker}")
            worker.stop()
    # endregion

    # region MANAGER MANAGEMENT
    def start(self):
        """Start all the processes
        """
        Global.LOGGER.info("MNGR: starting the workers")
        self._start_workers()

    def stop(self):
        """Stop all the processes
        """
        Global.LOGGER.info("MNGR: stopping the workers")
        self._stop_workers()
        self.is_running = False
        time.sleep(3)
        Global.LOGGER.info("MNGR: flows has been stopped. \nSo long, and thanks for all the fish.")

    def restart(self):
        """Restart all the processes
        """
        Global.LOGGER.info("MNGR: restarting")
        self.stop()
        self.start()
    # endregion