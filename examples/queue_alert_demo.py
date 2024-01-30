import logging

from five9_agent_sup_rest.client import Five9RestClient, Five9Socket
from five9_agent_sup_rest.methods.default_socket_handlers import SocketEventHandler

from five9_agent_sup_rest.private.credentials import ACCOUNTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

DEFAULT_QUEUE_DATA_INCREMENT_ALERTS = {
    "callsInQueue": 1,
    # "callbacksInQueue": 1,
    # "voicemailsInQueue": 1,
    # "vivrCallsInQueue": 1
}

class QueueStatistics:
    def __init__(self, *args, **kwargs):
        self.queue_id_map = {}
        self.queue_mapping_info = kwargs.get("queue_mapping_info", None)
        self.map_queue_ids()

        self.current_queue_snapshot = {}
        self.previous_queue_snapshot = {}

        self.queue_alerts = kwargs.get("queue_alerts", DEFAULT_QUEUE_DATA_INCREMENT_ALERTS)

    def map_queue_ids(self):
        for queue in self.queue_mapping_info:
            self.queue_id_map[queue["id"]] = queue["name"]

    def update_queue_info(self, queue_info):
        logging.debug(f"\nPrevious Snapshot:\n{self.previous_queue_snapshot}\n")
        logging.debug(f"\nCurrent Snapshot:\n{self.current_queue_snapshot}\n")
        for queue in queue_info:
            self.current_queue_snapshot[queue["id"]] = queue
        alerts = self.get_alerts_for_changes()
        self.previous_queue_snapshot = self.current_queue_snapshot.copy()

        return True, alerts
        
    def get_alerts_for_changes(self):
        alerts = []
        for queue_id, queue_info in self.current_queue_snapshot.items():
            if queue_id == "0":
                continue

            for alert_on, difference_threshold in self.queue_alerts.items():
                previous_value = self.previous_queue_snapshot.get(queue_id, {}).get(alert_on, 0)
                current_value = self.current_queue_snapshot.get(queue_id, {}).get(alert_on, 0)
                logging.debug(f"Comparing Thresholds: {self.queue_id_map[queue_id]} - {alert_on}: Current [{current_value}] Previous [{previous_value}]")
                difference = current_value - previous_value                
                if difference >= difference_threshold:
                    logging.debug(f"Difference [{difference}] is greater than threshold [{difference_threshold}]")               
                    alerts.append({
                        "queue_name": self.queue_id_map[queue_id],
                        "alert_on": alert_on,
                        "current_value": current_value,
                        "previous_value": previous_value,
                        "difference": difference,
                    })
        return alerts


class StatsEventBase(SocketEventHandler):
    def __init__(self, *args, **kwargs):
        self.eventId = kwargs.get("eventId", None)
        super().__init__(*args, **kwargs)
        if self.client.extensions.get("queue_statistics", None) is None:
            self.client.extensions["queue_statistics"] = QueueStatistics(
                queue_mapping_info=self.client.supervisor.DomainQueues.invoke()
            )
            logging.info("Client extension 'queue_statistics' initialized")
        logging.debug("Queue Statistics Handler Initialized")


class StatsEvent5000Handler(StatsEventBase):
    """Handler for event 5000 - Initial Statistics Snapshot"""

    eventId = "5000"

    def __init__(self, *args, **kwargs):
        super().__init__(eventId=self.eventId, *args, **kwargs)

    async def handle(self, event):
        logging.debug(
            f"Stats Handler EVENT: {event['context']['eventId']} - {event['payLoad']}"
        )
        for updated_object in event["payLoad"]:
            if updated_object["dataSource"] == "ACD_STATUS":
                logging.debug("Initial Queue Data Snapshot Received")
                self.client.extensions["queue_statistics"].update_queue_info(
                    updated_object["data"]
                )
        return


class StatsEvent5012Handler(StatsEventBase):
    """Handler for event 5012 - Statistics Update"""

    eventId = "5012"

    def __init__(self, *args, **kwargs):
        super().__init__(eventId=self.eventId, *args, **kwargs)

    async def handle(self, event):
        logging.debug(
            f"Stats Handler EVENT: {event['context']['eventId']} - {event['payLoad']}"
        )

        for updated_object in event["payLoad"]:
            if updated_object["dataSource"] == "ACD_STATUS":
                logging.debug("QUEUE DATA UPDATE RECEIVED")
                updated, alerts = self.client.extensions["queue_statistics"].update_queue_info(
                    updated_object["updated"]
                )
                # handle any alerts here
                for alert in alerts:
                    # ring a bell, send an email, etc.
                    logging.info(f"Queue Alert: {alert}")

        return


if __name__ == "__main__":
    username = ACCOUNTS["default_test_account"]["username"]
    password = ACCOUNTS["default_test_account"]["password"]

    custom_socket_handlers = [
        StatsEvent5000Handler,
        StatsEvent5012Handler,
    ]

    client = Five9RestClient(
        username=username,
        password=password,
        socket_app_key="queue_alert_demo",  # optional, will default to "python_pack_socket"
        custom_socket_handlers=custom_socket_handlers,
    )
    client.initialize_supervisor_session()

    # the socket will remain connected until either the user hits "Enter" or
    # there is an error in the socket connection that can't be recovered from
    client.supervisor_socket.connect()

    client.supervisor.LogOut.invoke()
