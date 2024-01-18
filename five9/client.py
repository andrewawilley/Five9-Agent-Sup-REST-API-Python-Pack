import inspect
import logging
from typing import Dict, Any

import requests

from five9.config import SETTINGS
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
        login_request = requests.post(
            SETTINGS.get("FIVENINE_VCC_LOGIN_URL", ""), json=self.login_payload
        )
        login_response = login_request.json()
        if login_request.status_code == 200:
            host = login_response["metadata"]["dataCenters"][0]["apiUrls"][0]["host"]
            port = login_response["metadata"]["dataCenters"][0]["apiUrls"][0]["port"]
            base_api_url = f"https://{host}:{port}"
            logging.debug(f"Metadata Obtained - Base API URL: {base_api_url}")
            FiveNineRestMethod.base_api_url = base_api_url
            FiveNineRestMethod.orgId = login_response["orgId"]
            FiveNineRestMethod.userId = login_response["userId"]
            FiveNineRestMethod.farmId = login_response["context"]["farmId"]
            FiveNineRestMethod.tokenId = login_response["tokenId"]
            FiveNineRestMethod.api_header = {
                "Authorization": f"Bearer-{login_response['tokenId']}",
                "farmId": login_response["context"]["farmId"],
                "Accept": "application/json, text/javascript",
            }

            self.logged_in = True

            self.agent = self.AgentRESTNamespace()
            self.supervisor = self.SupervisorRESTNamespace()

            current_supervisor_login_state = self.supervisor_login_state

            logging.info(f"Current Supervisor Login State: {current_supervisor_login_state}")

            if (
                auto_accept_notice == True
                and current_supervisor_login_state == "ACCEPT_NOTICE"
            ):
                logging.info(
                    f"Accepting Maintenance Notice for Supervisor: {self.userId}"
                )
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

        else:
            self.logged_in = False

        return self.logged_in

    # @property
    # def agent_login_state(self):
    #     s = requests.Session()
    #     url = f"/agents/{self.userId}/login_state"
    #     url = f"{self.base_api_url}{CONTEXT_PATHS["agent_rest"]}{url}"
    #     req = requests.Request(
    #         method="GET",
    #         url=url,
    #         headers=self.api_header,
    #     )
    #     prepped = req.prepare()
    #     response = s.send(prepped)
    #     return response.text

    @property
    def supervisor_login_state(self):
        return self.supervisor.SupervisorLoginState.invoke()

    # def start_agent_session(self):
    #     if self.agent_login_state == '"SELECT_STATION"':
    #         logging.info("Starting Agent Session")
    #         self.agent.AgentSessionStart()

    # def start_supervisor_session(self):
    #     if self.supervisor_login_state == '"SELECT_STATION"':
    #         logging.info("Starting Supervisor Session")
    #         self.supervisor.SupervisorSessionStart(self)

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
