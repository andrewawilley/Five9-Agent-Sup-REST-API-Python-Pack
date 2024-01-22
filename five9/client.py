import inspect
import logging

import requests

from five9.config import SETTINGS
from five9.exceptions import Five9DuplicateLoginError
from five9.methods.base import FiveNineRestMethod, SupervisorRestMethod, AgentRestMethod
from five9.methods import agent_methods, supervisor_methods


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

        login_request = requests.post(self.login_url, json=self.login_payload)

        self.session_metadata = login_request.json()
        logging.debug(f"VccClientSessionConfig - Login Result: {self.session_metadata}")

        if login_request.status_code < 400:
            logging.debug(f"SESSION COOKIES {login_request.cookies}")
            self.cookies_header = '; '.join([f"{cookie.name}={cookie.value}" for cookie in login_request.cookies])
        


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


class VccClient:
    class RESTNamespace:
        def __init__(
            self, target_module, session_configuration: VccClientSessionConfig
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

    def accept_maintenance_notices(self, user_type="supervisor"):
        if user_type == "supervisor":
            logging.info(f"Accepting Maintenance Notice for Supervisor: {self.userId}")
            notices = self.supervisor.MaintenanceNotices_Get.invoke()
            for notice in notices:
                if notice["accepted"] == False:
                    self.supervisor.AcceptMaintenanceNotice(notice["id"])
                    logging.info(f"Accepted Maintenance Notice: {notice['id']}")
        
        if user_type == "agent":
            logging.info(f"Accepting Maintenance Notice for Agent: {self.userId}")
            notices = self.agent.MaintenanceNotices_Get.invoke()
            for notice in notices:
                if notice["accepted"] == False:
                    self.agent.AcceptMaintenanceNotice(notice["id"])
                    logging.info(f"Accepted Maintenance Notice: {notice['id']}")

    def initialize_supervisor_session(self, auto_accept_notice=True):
        current_supervisor_login_state = self.supervisor_login_state
        if (
            auto_accept_notice == True
            and current_supervisor_login_state == "ACCEPT_NOTICE"
        ):
            self.accept_maintenance_notices(user_type="supervisor")
            current_supervisor_login_state = self.supervisor_login_state

        if current_supervisor_login_state == "SELECT_STATION":
            session = self.supervisor.SupervisorSessionStart.invoke(
                self.stationId, self.stationType, self.stationState
            )
            logging.debug(f"SUPERVISOR SESSION STARTED Result: {session.__dict__}")

    def initialize_agent_session(self, auto_accept_notice=True):
        current_agent_login_state = self.agent_login_state
        if (
            auto_accept_notice == True
            and current_agent_login_state == "ACCEPT_NOTICE"
        ):
            self.accept_maintenance_notices(user_type="agent")
            current_agent_login_state = self.agent_login_state


        if current_agent_login_state == "SELECT_STATION":
            session = self.agent.AgentSessionStart.invoke(
                self.stationId, self.stationType, self.stationState
            )
            logging.debug(f"AGENT SESSION STARTED Result: {session.__dict__}")

    @property
    def supervisor_login_state(self):
        return self.supervisor.SupervisorLoginState.invoke()

    @property
    def agent_login_state(self):
        return self.agent.AgentLoginState.invoke()
