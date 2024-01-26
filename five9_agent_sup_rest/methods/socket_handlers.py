import logging

from five9_agent_sup_rest.config import CONTEXT_PATHS


class SocketEventHandler:
    """Base class for socket event handlers
    """

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "eventId"):
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

    eventId = "1202"

    async def handle(self, event):
        logging.info(f"Default Handler EVENT: {event["context"]["eventId"]} - {event["payLoad"]}")
        return

class DefaultEventHandler70(SocketEventHandler):
    """Default handler for event 70 - Migration Started
    """

    eventId = "70"

    async def handle(self, event):
        logging.info(f"MGR EVENT: {event["context"]["eventId"]} - {event["payLoad"]}")
        return
    
class DefaultEventHandler1002(SocketEventHandler):
    """Default handler for event 1002 - Domain Migrated
    The payLoad for this event contains the new metadata for the session to use.
    This event updates the session_configuration object with the new metadata, and
    then invokes the SessionStart method to reconnect the session using the new metadata.

    The return value of this handler is used to determine whether the session should
    reconnect or not. If the return value is "reconnect", the socket object which received
    the event will reconnect the session. If the return value is anything else, the socket
    will proceed as normal and the session will not reconnect.
    """

    eventId = "1002"

    async def handle(self, event):
        logging.info(f"Default Handler EVENT: {event["context"]["eventId"]} - {event["context"]["eventReason"]}")
        self.client.session_configuration.update_config(event["payLoad"])
        if self.client.current_supervisor_login_state != "WORKING":
            self.client.supervisor.SessionStart.invoke()
            return "reconnect"
        return
