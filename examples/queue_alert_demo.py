import argparse
from getpass import getpass
import logging
import os

from five9_agent_sup_rest.client import Five9RestClient
from five9_agent_sup_rest.methods.default_socket_handlers import SocketEventHandler

# You can create a directory called "private" and create a file called "credentials.py" in it
# with a dictionary called "ACCOUNTS" that contains your Five9 account credentials
# ACCOUNTS = {
#     'default_test_account': {
#       'username': 'your_username@your_domain',
#       'password': 'superSecretPassword',
#     }
try:
    from private.credentials import ACCOUNTS
except ImportError:
    ACCOUNTS = {}

DEFAULT_QUEUE_DATA_INCREMENT_ALERTS = {
    "callsInQueue": 1,
    # "callbacksInQueue": 1,
    # "voicemailsInQueue": 1,
    # "vivrCallsInQueue": 1
    # "emailsInQueue": 1,
    # "chatsInQueue": 1,
}


class QueueStatistics:
    def __init__(self, *args, **kwargs):
        self.queue_id_map = {}
        self.queue_mapping_info = kwargs.get("queue_mapping_info", None)
        self.map_queue_ids()

        self.current_queue_snapshot = {}
        self.previous_queue_snapshot = {}

        self.queue_alerts = kwargs.get(
            "queue_alerts", DEFAULT_QUEUE_DATA_INCREMENT_ALERTS
        )

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
                previous_value = self.previous_queue_snapshot.get(queue_id, {}).get(
                    alert_on, 0
                )
                current_value = self.current_queue_snapshot.get(queue_id, {}).get(
                    alert_on, 0
                )
                logging.debug(
                    f"Comparing Thresholds: {self.queue_id_map[queue_id]} - {alert_on}: Current [{current_value}] Previous [{previous_value}]"
                )
                difference = current_value - previous_value
                if difference >= difference_threshold:
                    logging.debug(
                        f"Difference [{difference}] is greater than threshold [{difference_threshold}]"
                    )
                    alerts.append(
                        {
                            "queue_name": self.queue_id_map[queue_id],
                            "alert_on": alert_on,
                            "current_value": current_value,
                            "previous_value": previous_value,
                            "difference": difference,
                        }
                    )
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
                updated, alerts = self.client.extensions[
                    "queue_statistics"
                ].update_queue_info(updated_object["updated"])
                # handle any alerts here
                for alert in alerts:
                    # ring a bell, send an email, etc.
                    logging.info(f"Queue Alert: {alert}")

        return


if __name__ == "__main__":
    """
    This is an example of using the Five9RestClient to create a client session
    and opening a Five9 Websocket listener.

    This example uses custom socket handlers to handle the 5000 and 5012 events from the
    websocket (The initial queue statistics snapshot and the queue statistics update
    events, respectively). The event handlers use a QueueStatistics class to track the
    changes in the queues, and which could process alerts if changes exceed a change threshold.
    """
    parser = argparse.ArgumentParser(
        description="Run the Five9RestClient with specified parameters."
    )
    parser.add_argument(
        "-u",
        "--username",
        default=os.environ.get("FIVE9_USERNAME", None),
        help="Username for authentication",
    )
    parser.add_argument(
        "-p",
        "--password",
        default=os.environ.get("FIVE9_PASSWORD", None),
        help="Password for authentication",
    )
    parser.add_argument(
        "-a",
        "--account-alias",
        default=None,
        help="Account alias to use for looking up credentials in ACCOUNTS dictionary",
    )
    parser.add_argument(
        "-s",
        "--socket-app-key",
        default="python_pack_socket",
        help="Socket application key",
    )
    parser.add_argument("-r", "--region", default="US", help="US, CA, LDN, FRK")
    parser.add_argument(
        "-l", "--logging-level", default="INFO", help="Logging level to use"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=args.logging_level.upper(),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if args.account_alias:
        account_info = ACCOUNTS.get(args.account_alias)
        if not account_info:
            raise ValueError(f"No account found for alias: {args.account_alias}")
        username = account_info["username"]
        password = account_info["password"]
    else:
        username = args.username or input("Enter username: ")
        password = args.password or getpass("Enter password: ")

    custom_socket_handlers = [
        StatsEvent5000Handler,
        StatsEvent5012Handler,
    ]

    client = Five9RestClient(
        username=username,
        password=password,
        socket_app_key=args.socket_app_key,
        custom_socket_handlers=custom_socket_handlers,
        region=args.region
    )
    client.initialize_supervisor_session()

    client.supervisor_socket.connect()

    client.supervisor.LogOut.invoke()
