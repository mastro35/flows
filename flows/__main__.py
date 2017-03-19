from flows.FlowsManager import FlowsManager
from flows import Global


def main():
    my_flows_manager = FlowsManager()

    try:
        my_flows_manager.start()
    except KeyboardInterrupt:
        Global.LOGGER.info("Quit command received")
        my_flows_manager.stop()


if __name__ == "__main__":
    main()
