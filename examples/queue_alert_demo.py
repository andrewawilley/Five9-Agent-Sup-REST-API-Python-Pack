import logging

from five9_agent_sup_rest.client import Five9RestClient, Five9Socket
from five9_agent_sup_rest.methods.socket_handlers import SocketEventHandler

from five9_agent_sup_rest.private.credentials import ACCOUNTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class QueueStatistics:
    def __init__(self, *args, **kwargs):
        self.queue_id_map = {}
        self.queue_mapping_info = kwargs.get("queue_mapping_info", None)
        self.map_queue_ids()

        self.current_queue_snapshot = {
            "added": [],
            "updated": [],  
            "removed": [],
        }

    def map_queue_ids(self):
        for queue in self.queue_mapping_info:
            self.queue_id_map[queue["id"]] = queue["name"]

    def update_queue_info(self, queue_info):
        self.previous_queue_snapshot = self.current_queue_snapshot
        self.current_queue_snapshot = queue_info

class StatsEvent5000Handler(SocketEventHandler):
    """Handler for event 5000 - Statistics Update"""

    eventId = "5000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not hasattr(self.client, "queue_statistics"):
            self.client.queue_statistics = QueueStatistics(
                queue_mapping_info=self.client.supervisor.DomainQueues.invoke()
            )
            logging.info("Queue Statistics Handler Initialized")

    async def handle(self, event):
        logging.info(
            f"Stats Handler EVENT: {event['context']['eventId']} - {event['payLoad']}"
        )
        for updated_object in event["payLoad"]:
            if updated_object["dataSource"] == "ACD_STATUS":
                self.client.queue_statistics.update_queue_info(updated_object["object"])

        self.client.queue_statistics.update_queue_info(event["payLoad"])
        return


if __name__ == "__main__":
    username = ACCOUNTS["default_test_account"]["username"]
    password = ACCOUNTS["default_test_account"]["password"]

    custom_socket_handlers = [StatsEvent5000Handler]

    client = Five9RestClient(
        username=username,
        password=password,
        supervisor_socket_handlers=custom_socket_handlers,
    )
    client.initialize_supervisor_session()

    # queues = client.supervisor.DomainQueues.invoke()

    client.supervisor_socket.connect()

    client.supervisor.LogOut.invoke()
