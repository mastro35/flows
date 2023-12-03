from flows.FlowsManager import FlowsManager


def main():
    my_flows_manager = FlowsManager()

    try:
        my_flows_manager.start()
    except KeyboardInterrupt:
        my_flows_manager.stop()


if __name__ == "__main__":
    main()
