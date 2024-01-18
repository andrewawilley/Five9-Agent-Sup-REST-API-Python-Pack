import inspect
import logging
from typing import Dict, Any

import requests

from five9.config import SETTINGS
from five9.exceptions import Five9DuplicateLoginError
from five9.methods.base import FiveNineRestMethod, SupervisorRestMethod, AgentRestMethod
from five9.methods import agent_methods, supervisor_methods


class VccClientSessionConfig:
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

        self.login_url = kwargs.get(
            "login_url", SETTINGS.get("FIVENINE_VCC_LOGIN_URL", "")
        )

        self.login()

    def login(self, *args, **kwargs):
        self.session_metadata = None
        try:
            login_request = requests.post(
                SETTINGS.get("FIVENINE_VCC_LOGIN_URL", ""), json=self.login_payload
            )
        except Five9DuplicateLoginError:
            login_request = requests.get(SETTINGS.get("FIVENINE_VCC_METADATA_URL", ""))
            logging.debug(
                f"VccClientSessionConfig - Already Logged in, obtaining metadata: {login_request.json()}"
            )

        self.session_metadata = login_request.json()
        logging.debug(f"VccClientSessionConfig - Login Result: {self.session_metadata}")

        if self.session_metadata:
            self.process_session_metadata()
            return True
        else:
            return False

    def process_session_metadata(self, *args, **kwargs):
        self.host = self.session_metadata["metadata"]["dataCenters"][0]["apiUrls"][0][
            "host"
        ]
        self.port = self.session_metadata["metadata"]["dataCenters"][0]["apiUrls"][0][
            "port"
        ]

        self.base_api_url = f"https://{self.host}:{self.port}"
        self.base_api_url = self.base_api_url
        self.orgId = self.session_metadata["orgId"]
        self.userId = self.session_metadata["userId"]
        self.farmId = self.session_metadata["context"]["farmId"]
        self.tokenId = self.session_metadata["tokenId"]

        self.api_header = {
            "Authorization": f"Bearer-{self.tokenId}",
            "farmId": self.farmId,
            "Accept": "application/json, text/javascript",
        }

        logging.debug(f"Metadata Obtained - Base API URL: {self.base_api_url}")

        self.notify_observers()

        return True

    def subscribe_observer(self, observer):
        self.observers.append(observer)

    def notify_observers(self, *args, **kwargs):
        for observer in self.observers:
            observer.update_config(self)


REST_MODULES = {
    "agent_methods": {
        "module": agent_methods,
        "sublass": AgentRestMethod,
    },
    "supervisor_methods": {
        "module": supervisor_methods,
        "sublass": SupervisorRestMethod,
    },
}


class VccClient:
    class RESTNamespace:
        def __init__(
            self, target_module, session_configuration: VccClientSessionConfig
        ):
            for name, obj in inspect.getmembers(REST_MODULES[target_module]["module"]):
                if inspect.isclass(obj) and issubclass(
                    obj, REST_MODULES[target_module]["sublass"]
                ):
                    setattr(self, name, obj(session_configuration))

    def __init__(self, *args, **kwargs):
        self.stationId = kwargs.get("stationId", "")
        self.stationType = kwargs.get("stationType", "EMPTY")
        self.stationState = kwargs.get("stationState", "DISCONNECTED")

        self.log_in_on_create = kwargs.get("log_in_on_create", True)

        self.logged_in = False

        logging.info("Initializing VCC_Client")

        self.session_configuration = VccClientSessionConfig(
            username=kwargs["username"],
            password=kwargs["password"],
        )

        self.agent = self.RESTNamespace("agent_methods", self.session_configuration)
        self.supervisor = self.RESTNamespace(
            "supervisor_methods", self.session_configuration
        )

    def initialize_supervisor_session(self, auto_accept_notice=True):
        current_supervisor_login_state = self.supervisor_login_state

        if (
            auto_accept_notice == True
            and current_supervisor_login_state == "ACCEPT_NOTICE"
        ):
            logging.info(f"Accepting Maintenance Notice for Supervisor: {self.userId}")
            notices = self.supervisor.MaintenanceNotices_Get.invoke()
            for notice in notices:
                if notice["accepted"] == False:
                    self.supervisor.AcceptMaintenanceNotice(notice["id"])
                    logging.info(f"Accepted Maintenance Notice: {notice['id']}")
            # self.supervisor.AcceptMaintenanceNotice.invoke()

        if current_supervisor_login_state == "SELECT_STATION":
            start_session = self.supervisor.SupervisorSessionStart.invoke(
                self.stationId, self.stationType, self.stationState
            )
            logging.debug(f"Login Result: {start_session}")

    def initialize_agent_session(self, auto_accept_notice=True, agent_login_state=None):
        current_agent_login_state = agent_login_state or self.agent_login_state

        if auto_accept_notice == True and current_agent_login_state == "ACCEPT_NOTICE":
            logging.info(f"Accepting Maintenance Notice for Agent: {self.userId}")
            notices = self.agent.MaintenanceNotices_Get.invoke()
            for notice in notices:
                if notice["accepted"] == False:
                    self.agent.AcceptMaintenanceNotice(notice["id"])
                    logging.info(f"Accepted Maintenance Notice: {notice['id']}")
            # self.supervisor.AcceptMaintenanceNotice.invoke()

        if current_agent_login_state == "SELECT_STATION":
            start_session = self.agent.AgentSessionStart.invoke(
                self.stationId, self.stationType, self.stationState
            )
            logging.debug(f"Login Result: {start_session}")

    @property
    def supervisor_login_state(self):
        logging.debug(f"Supervisor Login State: {self.supervisor.SupervisorLoginState.invoke()}")
        return self.supervisor.SupervisorLoginState.invoke()

    @property
    def agent_login_state(self):
        return self.agent.AgentLoginState.invoke()

    # login metadata payload sample = {
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
