#!/usr/bin/env python3

"""
Global.py - singleton and utility for Flows
"""

import pkg_resources

VERSION = pkg_resources.get_distribution('flows').version
CONFIG_MANAGER = None
LOGGER = None
ZMQ_CONTEXT = None
MESSAGES = None 