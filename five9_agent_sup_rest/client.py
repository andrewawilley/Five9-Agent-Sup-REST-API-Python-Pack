import asyncio
import inspect
import json
import logging

import requests
import websockets

from five9_agent_sup_rest.config import CONTEXT_PATHS
from five9_agent_sup_rest.config import SETTINGS

from five9_agent_sup_rest.exceptions import Five9DuplicateLoginError

from five9_agent_sup_rest.methods.base import SupervisorRestMethod, AgentRestMethod
from five9_agent_sup_rest.methods import agent_methods, supervisor_methods

from five9_agent_sup_rest.methods import default_socket_handlers


API_METHOD_MODULES = {
    "agent_methods": {
        "module": agent_methods,
        "sublass": AgentRestMethod,
    },
    "supervisor_methods": {
        "module": supervisor_methods,
        "sublass": SupervisorRestMethod,
    },
}


class Five9RestClientSessionConfig:
    def __init__(self, *args, **kwargs):
        self.observers = []

        self.username = kwargs.get("username", "")
        self.password = kwargs.get("password", "")

        self.login_payload = {
            "passwordCredentials": {
                "username": self.username,
                "password": self.password,
            },
            "appKey": "mypythonapp-supervisor-session",
            "policy": "AttachExisting",
        }
        self.region = kwargs.get("region", "US")
        self.login_url = kwargs.get(
            "login_url", SETTINGS[self.region].get("FIVENINE_VCC_LOGIN_URL", "")
        )

        self.login()

    def login(self, *args, **kwargs):
        self.session_metadata = None

        login_request = requests.post(self.login_url, json=self.login_payload)

        self.session_metadata = login_request.json()
        logging.debug(
            f"Five9RestClientSessionConfig - Login Result: {self.session_metadata}"
        )

        if login_request.status_code < 400:
            logging.debug(f"SESSION COOKIES {login_request.cookies}")
            self.cookies_header = "; ".join(
                [f"{cookie.name}={cookie.value}" for cookie in login_request.cookies]
            )

        if self.session_metadata:
            self.process_session_metadata()
            return True
        else:
            return False

    def process_session_metadata(self, *args, **kwargs):
        # Break down the processing into smaller, manageable parts
        self.set_api_urls()
        self.set_credentials()
        self.set_api_header()

        # Notify observers after processing is complete
        self.notify_observers()
        logging.debug(
            f"Metadata Processing Complete - Base API URL: {self.base_api_url}"
        )
        return True

    def set_api_urls(self):
        data_center_info = self.session_metadata["metadata"]["dataCenters"][0]
        api_url_info = data_center_info["apiUrls"][0]

        self.host = api_url_info["host"]
        self.port = api_url_info["port"]
        self.base_api_url = f"https://{self.host}:{self.port}"

        logging.debug(f"API URLs Set - Base API URL: {self.base_api_url}")

    def set_credentials(self):
        self.orgId = self.session_metadata["orgId"]
        self.userId = self.session_metadata["userId"]
        self.farmId = self.session_metadata["context"]["farmId"]
        self.tokenId = self.session_metadata["tokenId"]

        logging.debug(f"Credentials Set - UserID: {self.userId}, OrgID: {self.orgId}")

    def set_api_header(self):
        self.api_header = {
            "Authorization": f"Bearer-{self.tokenId}",
            "farmId": self.farmId,
            "Accept": "application/json, text/javascript",
        }
        logging.debug(
            f"API Header Set - Authorization Token: {self.api_header['Authorization']}"
        )

    def subscribe_observer(self, observer):
        self.observers.append(observer)

    def notify_observers(self, *args, **kwargs):
        for observer in self.observers:
            observer.update_config(self)


class Five9RestClient:
    class RESTNamespace:
        def __init__(
            self, target_module, session_configuration: Five9RestClientSessionConfig
        ):
            for name, obj in inspect.getmembers(
                API_METHOD_MODULES[target_module]["module"]
            ):
                if inspect.isclass(obj) and issubclass(
                    obj, API_METHOD_MODULES[target_module]["sublass"]
                ):
                    setattr(self, name, obj(session_configuration))

    def __init__(self, *args, **kwargs):
        self.stationId = kwargs.get("stationId", "")
        self.stationType = kwargs.get("stationType", "EMPTY")
        self.stationState = kwargs.get("stationState", "DISCONNECTED")


        custom_supervisor_methods = kwargs.get("custom_supervisor_methods", [])
        custom_agent_methods = kwargs.get("custom_agent_methods", [])
        
        self.custom_socket_handlers = kwargs.get("custom_socket_handlers", {})
        self.socket_app_key = kwargs.get("socket_app_key", "python_pack_socket")

        self.logged_in = False

        logging.info(f"Initializing VCC_Client for user: {kwargs["username"]}")

        self.session_configuration = Five9RestClientSessionConfig(
            username=kwargs["username"],
            password=kwargs["password"],
        )

        self.agent = self.RESTNamespace("agent_methods", self.session_configuration)
        self.supervisor = self.RESTNamespace(
            "supervisor_methods", self.session_configuration
        )

        for method in custom_supervisor_methods:
            if inspect.isclass(method) and issubclass(method, SupervisorRestMethod):
                setattr(
                    self.supervisor, method.__name__, method(self.session_configuration)
                )
                logging.info(f"Custom Supervisor Method Added: {method.__name__}")

        for method in custom_agent_methods:
            if inspect.isclass(method) and issubclass(method, AgentRestMethod):
                setattr(self.agent, method.__name__, method(self.session_configuration))
                logging.info(f"Custom Agent Method Added: {method.__name__}")

        self.extensions = {}

    def accept_maintenance_notices(self, user_type="supervisor"):
        if user_type == "supervisor":
            logging.info(f"Accepting Maintenance Notice for Supervisor: {self.session_configuration.userId}")
            notices = self.supervisor.MaintenanceNoticesGet.invoke()
            for notice in notices:
                if notice["accepted"] == False:
                    self.supervisor.MaintenanceNoticeAccept.invoke(notice["id"])
                    logging.info(f"Accepted Maintenance Notice: {notice['id']}")

        if user_type == "agent":
            logging.info(f"Accepting Maintenance Notice for Agent: {self.session_configuration.userId}")
            notices = self.agent.MaintenanceNoticesGet.invoke()
            for notice in notices:
                if notice["accepted"] == False:
                    self.agent.MaintenanceNoticeAccept.invoke(notice["id"])
                    logging.info(f"Accepted Maintenance Notice: {notice['id']}")

    def initialize_supervisor_session(
        self, socket_handlers={}, auto_accept_notice=True
    ):
        current_supervisor_login_state = self.supervisor_login_state

        self.socket_handlers = socket_handlers
        
        current_supervisor_login_state = self.supervisor_login_state

        if current_supervisor_login_state == "WORKING":
            self.supervisor_socket = Five9Socket(
                self, "supervisor", self.socket_app_key
            )
            return True

        if current_supervisor_login_state in ["ACCEPT_NOTICE", "WORKING"]:
            if auto_accept_notice == True:
                self.accept_maintenance_notices(user_type="supervisor")

        if current_supervisor_login_state == "SELECT_STATION":
            try:
                session = self.supervisor.SupervisorSessionStart.invoke(
                    self.stationId, self.stationType, self.stationState
                )
            except Five9DuplicateLoginError:
                logging.info(
                    "Supervisor already logged in, logging out, please try again."
                )
                self.supervisor.LogOut.invoke()
                return False

            logging.debug(f"SUPERVISOR SESSION STARTED Result: {session.__dict__}")
            self.supervisor_socket = Five9Socket(
                self, "supervisor", self.socket_app_key
            )
            return True

    def initialize_agent_session(self, auto_accept_notice=True):
           
        current_agent_login_state = self.agent_login_state

        if current_agent_login_state == "WORKING":
            self.supervisor_socket = Five9Socket(
                self, "supervisor", self.socket_app_key
            )
            return True

        if current_agent_login_state == "WORKING":
            self.agent_socket = Five9Socket(
                self, "agent", self.socket_app_key
            )
            return True

        if current_agent_login_state == "SELECT_STATION":
            try:
                session = self.agent.AgentSessionStart.invoke(
                    self.stationId, self.stationType, self.stationState
                )
                logging.debug(f"AGENT SESSION STARTED Result: {session.__dict__}")

            except Five9DuplicateLoginError:
                logging.info("Agent already logged in, logging out, please try again.")
                self.agent.LogOut.invoke()
                return False

            logging.debug(f"AGENT SESSION STARTED Result: {session.__dict__}")

            self.agent_socket = Five9Socket(self, "agent", self.socket_app_key)
            return True

    @property
    def supervisor_login_state(self):
        return self.supervisor.SupervisorLoginState.invoke()

    @property
    def agent_login_state(self):
        return self.agent.AgentLoginState.invoke()


class Five9Socket:
    """Class for facilitating Five9 WebSocket connections
    Requires a Five9RestClient instance and a socket_app_key.  The socket_app_key is used to identify the socket for your app and is arbitrary.
    The context parameter must be either "agent" or "supervisor" and is used to determine the context path for the WebSocket URI.
    """

    def __init__(self, client: Five9RestClient, context, socket_app_key):
        self.client = client
        self.socket_app_key = socket_app_key
        self.context_path = CONTEXT_PATHS[f"websocket_{context}"]
        self.uri = f"wss://{client.session_configuration.host}:{client.session_configuration.port}{self.context_path}"
        self.uri = self.uri.format(socket_app_key=self.socket_app_key)

        self.disconnect_event = asyncio.Event()
        self.disconnect_requested = False

        logging.debug(f"WebSocket URI: {self.uri}")

    def add_socket_handler(self, handler):
        if (
            inspect.isclass(handler)
            and issubclass(handler, default_socket_handlers.SocketEventHandler)
            and hasattr(handler, "eventId")
        ):
            handler = handler(client=self.client)
            self.handlers[handler.eventId] = handler
            logging.debug(f"Handler Added: {handler.eventId}")

        else:
            logging.debug(f"Skipping {handler}")

    async def send_ping(self, websocket):
        while not self.disconnect_requested:
            try:
                await websocket.send("ping")
                logging.debug("Ping sent")

                # Create tasks from the coroutines
                sleep_task = asyncio.create_task(asyncio.sleep(15))
                event_task = asyncio.create_task(self.disconnect_event.wait())

                # Wait for either the sleep task to complete or the event task to be set
                done, pending = await asyncio.wait(
                    [sleep_task, event_task], return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel any pending tasks to avoid them running in the background
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            except websockets.ConnectionClosed:
                logging.info("Connection closed, stopping ping.")
                break

    async def handle_messages(self, websocket):
        async for message in websocket:
            if self.disconnect_requested:
                logging.info(
                    "Socket Disconnect Requested by Client, stopping message handler."
                )
                break

            event = json.loads(message)

            handler = self.handlers.get(event["context"]["eventId"], None)

            if not handler:
                logging.info(
                    f"No handler found for event {event['context']['eventId']}, creating generic handler."
                )
                handler = default_socket_handlers.SocketEventHandler(
                    self.client, event["context"]["eventId"]
                )
                self.handlers[event["context"]["eventId"]] = handler

            handled = await handler.handle(event)
            if handled == "reconnect":
                logging.info("Reconnecting socket.")
                await self.close()
                self.connect()

    async def listen_for_disconnect(self):
        # Get the event loop for the current thread,
        # and schedule the await_disconnect coroutine to run in the background
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._await_disconnect, loop)

    def _await_disconnect(self, loop):
        input("\nWebsocket Open, press Enter to disconnect...\n")
        self.disconnect_requested = True
        self.disconnect_event.set()  # Set the event to wake up the send_ping coroutine
        logging.info("Disconnect command received.")
        asyncio.run_coroutine_threadsafe(self.close(), loop)

    async def _connect(self):
        headers = {
            "Authorization": f"Bearer-{self.client.session_configuration.tokenId}",  # Use the token provided during initialization
            "Cookie": self.client.session_configuration.cookies_header,  # Use the cookies provided during initialization
        }

        self.handlers = {}

        for name, handler in inspect.getmembers(default_socket_handlers):
            if inspect.isclass(handler) and issubclass(
                handler, default_socket_handlers.SocketEventHandler
            ):
                self.add_socket_handler(handler)

        for handler in self.client.custom_socket_handlers:
            added = self.add_socket_handler(handler)
            logging.debug(f"Handler Added: {handler.eventId}")

        async with websockets.connect(self.uri, extra_headers=headers) as websocket:
            self.websocket = websocket
            # Run sending pings and message handler concurrently
            await asyncio.gather(
                self.send_ping(websocket),
                self.handle_messages(websocket),
                self.listen_for_disconnect(),
            )

    def connect(self):
        try:
            asyncio.run(self._connect())
        except:
            logging.exception("Error in WebSocket connection.")

    async def close(self):
        if hasattr(self, "websocket") and self.websocket and self.websocket.open:
            await self.websocket.close()
            logging.info("WebSocket closed.")
