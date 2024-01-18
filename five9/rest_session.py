import logging
from typing import Dict, Any

import requests


SETTINGS = {
    "FIVENINE_VCC_LOGIN_URL": "https://app.five9.com/appsvcs/rs/svc/auth/login",
    "logging_level": "DEBUG",
}

CONTEXT_PATHS = {
    # Agent REST API Services
    "agent_rest": "/appsvcs/rs/svc",
    # Agent call recordings and email message attachments"
    "agent_str": "/strsvcs/rs/svc",
    # Supervisor REST API Services
    "sup_rest": "/supsvcs/rs/svc",
}


logging.basicConfig(
    level=logging.DEBUG if SETTINGS["logging_level"] == "DEBUG" else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class FiveNineRestMethod:
    name: str = ""
    client = None
    method: str = ""
    context: str = ""
    path: str = ""
    path_params: Dict[str, Any] = {}
    qstring_params: Dict[str, Any] = {}
    payload: Dict[str, Any] = {}
    response = None
    data = None
    debug_output: bool = False

    def __init__(self):
        self.session = requests.Session()

    def invoke(self):
        url = f"{self.client.base_api_url}{self.context}{self.path}"
        url = url.format_map(self.path_params)

        req = requests.Request(
            method=self.method,
            url=url,
            headers=self.client.api_header,
        )

        if self.method != "GET":
            req.json = self.payload
        if self.qstring_params:
            req.params = self.qstring_params

        prepped = req.prepare()

        try:
            self.response = self.session.send(prepped)
            self.response.raise_for_status()
            logging.debug(f"RESPONSE: {self.response.text}")
            if self.response.text:
                self.data = self.response.json()
        except requests.exceptions.HTTPError as errh:
            logging.error(f"HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            logging.error(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            logging.error(f"Unexpected Error: {err}")

    @property
    def pre_invoke_debug(self):
        return {
            "method": self.name,
            "endpoint": f"{self.method} {self.context}{self.path}",
            "invoke_path_params": self.path_params,
            "inv_qstring_params": self.qstring_params,
            "inv_payload": self.payload,
        }



class SupervisorSessionStart(FiveNineRestMethod):
    """Creates a session and registers the station for the agent.
    PUT /supervisors/{agentId}/session_start

    The initial login state must be in SELECT_STATION state. This request
    modifies the agent’s login state. If successful, the request changes the
    LoginState value and sends the EVENT_STATION_UPDATED and
    EVENT_LOGIN_STATE_UPDATED events. The agent must have the
    CAN_RUN_WEB_AGENT permission
    """

    name = "Supervisor:SupervisorSessionStart"

    def __init__(self, client, *args, **kwargs):
        super().__init__()
        self.client = client
        self.method = "PUT"
        self.context = CONTEXT_PATHS["sup_rest"]
        self.path = "/supervisors/{supervisorId}/session_start"
        self.path_params["supervisorId"] = self.client.userId
        self.payload = {
            "state": self.client.stationState,
            "stationId": self.client.stationId,
            "stationType": self.client.stationType,
        }
        logging.debug(self.payload)
        self.invoke()


#####################################################################
# Agent REST API Services
# Alphabetical by class-based API method name
#####################################################################


class AgentInteractions(FiveNineRestMethod):
    """Returns a list of interactions in which the agent is taking part.

    This request returns only calls and voicemail messages. It does not return
    previews, queue callbacks, and multi-channel interactions.

    Required Arguments:
    client = Authenticated VCC_Client object

    {
        'channelType': 'CALL'
            # CALL
            # CHAT
            # EMAIL
            # SOCIAL
            # TEXT
            # VOICE_MAIL,
        'interactionId': 'UUID' # string Interaction ID
    """

    name = "Agent:AgentInteractions"

    def __init__(self, client, get_params):
        super().__init__()
        self.client = client
        self.method = "GET"
        self.context = CONTEXT_PATHS["agent_rest"]
        self.path = "/agents/{agentId}/interactions"
        self.path_params["agentId"] = self.client.userId
        logging.debug(self.pre_invoke_debug)
        self.invoke()

    def __str__(self):
        return f"{self.data}"


#####################################################################
# VCC Client Class
#####################################################################
class VCC_Client:
    """Returns a client object to interact with the REST APIs

    required to instantiate:
    username
    password

    optional parameters:
    stationId = stationId on the org
                defaults to a fake ANI of 5554443333

    stationType = choices are ["PSTN", "SOFTPHONE", "GATEWAY", "EMPTY"]
                  default is "PSTN"

    stationState = choices are ["CONNECTING", "CONNECTED", "DISCONNECTED"]
                   default is "DISCONNECTED"

    appKey = defaults to "mypythonapp-supervisor-session", set to whatever you want to help identify your app
    """

    base_api_url = None
    response = None
    metadata = None

    userId = None
    farmId = None
    tokenId = None

    orgId = None

    login_payload = {
        "passwordCredentials": {
            "username": None,
            "password": None,
        },
        "appKey": "mypythonapp-supervisor-session",
        "policy": "AttachExisting",
    }

    stationId = ""
    stationType = "EMPTY"
    stationState = "DISCONNECTED"

    log_in_on_create = True

    logged_in = False

    def __init__(self, *args, **kwargs):
        self.login_payload["passwordCredentials"] = {
            "username": kwargs["username"],
            "password": kwargs["password"],
        }
        self.stationId = kwargs.get("stationId", self.stationId)
        self.stationType = kwargs.get("stationType", self.stationType)
        self.stationState = kwargs.get("stationState", self.stationState)
        self.debug_output = kwargs.get("debug_output", False)
        if self.log_in_on_create is True:
            logging.debug("Logging in on create")
            result = self.login()
            logging.debug(f"Login Result: {result}")

    def login(self):
        session = requests.post(
            SETTINGS.get("FIVENINE_VCC_LOGIN_URL", ""), json=self.login_payload
        )
        self.response = session.json()
        if session.status_code == 200:
            self.metadata = self.response.get("metadata", None)
            self.base_api_url = "https://%s:%s" % (
                self.metadata["dataCenters"][0]["apiUrls"][0]["host"],
                self.metadata["dataCenters"][0]["apiUrls"][0]["port"],
            )
            self.tokenId = self.response["tokenId"]
            self.farmId = self.response["context"]["farmId"]
            self.userId = self.response["userId"]
            self.orgId = self.response["orgId"]
            self.logged_in = True
        else:
            self.logged_in = False
        return self.logged_in

    def __init__(self, *args, **kwargs):
        self.login_payload["passwordCredentials"] = {
            "username": kwargs["username"],
            "password": kwargs["password"],
        }
        self.stationId = kwargs.get("stationId", self.stationId)
        self.stationType = kwargs.get("stationType", self.stationType)
        self.stationState = kwargs.get("stationState", self.stationState)
        self.login()

    @property
    def agent_login_state(self):
        s = requests.Session()
        url = f"/agents/{self.userId}/login_state"
        url = f"{self.base_api_url}{CONTEXT_PATHS["agent_rest"]}{url}"
        req = requests.Request(
            method="GET",
            url=url,
            headers=self.api_header,
        )
        prepped = req.prepare()
        response = s.send(prepped)
        return response.text

    @property
    def supervisor_login_state(self):
        s = requests.Session()
        url = f"/supervisors/{self.userId}/login_state"
        url = f"{self.base_api_url}{CONTEXT_PATHS["sup_rest"]}{url}"
        req = requests.Request(
            method="GET",
            url=url,
            headers=self.api_header,
        )
        prepped = req.prepare()
        response = s.send(prepped)
        logging.debug(f"Supervisor Login State: {response.text}")
        return response.text

    def start_agent_session(self):
        if self.agent_login_state == '"SELECT_STATION"':
            logging.debug("Starting Agent Session")
            AgentSessionStart(self)

    def start_supervisor_session(self):
        if self.supervisor_login_state == '"SELECT_STATION"':
            logging.debug("Starting Supervisor Session")
            SupervisorSessionStart(self)

    @property
    def api_header(self, *args, **kwargs):
        return {
            "Authorization": f"Bearer-{self.tokenId}",
            "farmId": self.farmId,
            "Accept": "application/json, text/javascript",
        }

    @property
    def active_agent_sessions(self, *args, **kwargs):
        active = AgentInteractions(self, {})
        return active.data

    # sample = {
    #     'tokenId': '8da2a97a-3c4d-11e9-a2f1-005056a7f388',
    #     'orgId': '113555',
    #     'userId': '300000000226050',
    #     'context': {
    #         'farmId': '3000000000000000022'
    #     },
    #     'metadata': {
    #         'freedomUrl': 'https: //app.five9.com',
    #         'dataCenters': [{
    #             'name': 'AtlantaDataCenter',
    #             'uiUrls': [{
    #                 'host': 'app-atl.five9.com',
    #                 'port': '443',
    #                 'routeKey': 'ATLUIQ8rCg',
    #                 'version': '10.2.32'
    #             }],
    #             'apiUrls': [{
    #                 'host': 'app-atl.five9.com',
    #                 'port': '443',
    #                 'routeKey': 'ATLAPIah1F',
    #                 'version': '10.2.32'
    #             }],
    #             'loginUrls': [{
    #                 'host': 'app-atl.five9.com',
    #                 'port': '443',
    #                 'routeKey': 'ATLLGNPOE9',
    #                 'version': '10.2.32'
    #             }],
    #             'active': True
    #         }]
    #     },
    # }
