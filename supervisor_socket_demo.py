import asyncio
import logging

from five9.client import Five9RestClient, Five9Socket
from five9.methods.socket_handlers import SocketEventHandler

from five9.private.credentials import ACCOUNTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

class QueueStatistics:
    def __init__(self, *args, **kwargs):
        self.queueId = kwargs.get("queueId", None)
        self.queueName = kwargs.get("queueName", None)
        self.queue_info_raw = kwargs.get("queue_info_raw", None)

        self.queue_id_map = {}

        self.current_queue_snapshot = {}
        self.previous_queue_snapshot = {}

        self.map_queue_ids(self.queue_info_raw)

    def map_queue_ids(self, queue_info_raw):
        self.queue_info_raw = queue_info_raw
        for queue in self.queue_info_raw:
            self.queue_id_map[queue["queueId"]] = queue["name"]        

    def update_queue_info(self, queue_info):
        self.previous_queue_snapshot = self.current_queue_snapshot
        self.current_queue_snapshot = queue_info


class StatsEvent5000Handler(SocketEventHandler):
    """Default handler for event 5000
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eventId = "5000"

    async def handle(self, event):
        logging.info(f"Stats Handler EVENT: {event['context']['eventId']} - {event['payLoad']}")
        return


if __name__ == "__main__":

    username = ACCOUNTS["default_test_account"]["username"]
    password = ACCOUNTS["default_test_account"]["password"]

    client = Five9RestClient(username=username, password=password)
    client.initialize_supervisor_session()

    queues = client.supervisor.DomainQueues.invoke()
    print(queues)
    # logging.debug(f"Token: {c.tokenId}")

    supervisor_socket = Five9Socket(client, "supervisor", "demo_script")

    # Run the connect method to start the WebSocket connection
    asyncio.run(supervisor_socket.connect())
