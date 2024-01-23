import logging

from five9.config import CONTEXT_PATHS


class SocketEventHandler:
    """Base class for socket event handlers
    """

    def __init__(self, *args, **kwargs):
        self.eventId = kwargs.get("eventId", None)
        self.client = kwargs.get("client", None)

    async def handle(self, event):
        """Handles an event received from the socket
        """
        # logging.info(f"Generic Handler EVENT: {event["context"]["eventId"]} - {event["context"]["eventReason"]}}")
        logging.info(f"Generic Handler EVENT: {event["context"]["eventId"]} - {event["context"]["eventReason"]} - Payload:\n{event["payLoad"]}\n")
        return

class DefaultEventHandler1202(SocketEventHandler):
    """Default handler for event 1202
    """

    async def handle(self, event):
        logging.info(f"Default Handler EVENT: {event["context"]["eventId"]} - {event["payLoad"]}")
        return
