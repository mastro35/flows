"""
Flows main Module
---------

Copyright 2016 - 2024 Davide Mastromatteo
License: GPL 2.0
"""

from flows.FlowsManager import FlowsManager


def main():
    """
    Entry point of the flows module
    """

    my_flows_manager = FlowsManager()

    try:
        my_flows_manager.start()
    except KeyboardInterrupt:
        my_flows_manager.stop()


if __name__ == "__main__":
    main()
