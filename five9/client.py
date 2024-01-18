import inspect
import logging
from typing import Dict, Any

import requests

from five9.config import SETTINGS
from five9.exceptions import Five9DuplicateLoginError
from five9.methods.base import FiveNineRestMethod, SupervisorRestMethod, AgentRestMethod
from five9.methods import agent_methods, supervisor_methods


class VCC_Client:
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

    class SupervisorRESTNamespace:
        def __init__(self):
            self._generate_rest_methods(supervisor_methods)

        def _generate_rest_methods(self, module):
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, SupervisorRestMethod):
                    setattr(self, name, obj())

    class AgentRESTNamespace:
        def __init__(self):
            self._generate_rest_methods(agent_methods)

        def _generate_rest_methods(self, module):
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, AgentRestMethod):
                    setattr(self, name, obj())

    def __init__(self, *args, **kwargs):
        logging.info("Initializing VCC_Client")

        self.login_payload["passwordCredentials"] = {
            "username": kwargs["username"],
            "password": kwargs["password"],
        }

        self.log_in_on_create = kwargs.get("log_in_on_create", self.log_in_on_create)

        if self.log_in_on_create == True:
            logging.debug("Logging in on create")
            login_result = self.login()

    def login(self, auto_accept_notice=True):
        try:
            login_request = requests.post(
                SETTINGS.get("FIVENINE_VCC_LOGIN_URL", ""), json=self.login_payload
            )
        except Five9DuplicateLoginError:
            login_request = requests.get(
                SETTINGS.get("FIVENINE_VCC_METADATA_URL", "")
            )
        
        session_metadata = login_request.json()
        if login_request.status_code == 200:
            host = session_metadata["metadata"]["dataCenters"][0]["apiUrls"][0]["host"]
            port = session_metadata["metadata"]["dataCenters"][0]["apiUrls"][0]["port"]
            base_api_url = f"https://{host}:{port}"
            logging.debug(f"Metadata Obtained - Base API URL: {base_api_url}")
            FiveNineRestMethod.base_api_url = base_api_url
            FiveNineRestMethod.orgId = session_metadata["orgId"]
            FiveNineRestMethod.userId = session_metadata["userId"]
            FiveNineRestMethod.farmId = session_metadata["context"]["farmId"]
            FiveNineRestMethod.tokenId = session_metadata["tokenId"]
            FiveNineRestMethod.api_header = {
                "Authorization": f"Bearer-{session_metadata['tokenId']}",
                "farmId": session_metadata["context"]["farmId"],
                "Accept": "application/json, text/javascript",
            }

            self.logged_in = True

            self.agent = self.AgentRESTNamespace()
            self.supervisor = self.SupervisorRESTNamespace()

        else:
            self.logged_in = False

        return self.logged_in

    def initialize_supervisor_session(
        self, auto_accept_notice=True, supervisor_login_state=None
    ):
        current_supervisor_login_state = (
            supervisor_login_state or self.supervisor_login_state
        )

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

        if (
            auto_accept_notice == True 
            and current_agent_login_state == "ACCEPT_NOTICE"
        ):
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
