import logging

from .base import SupervisorRestMethod
from five9.config import CONTEXT_PATHS


class MaintenanceNoticesGet(SupervisorRestMethod):
    """Returns an array of maintenance notices.
    GET /supervisors/{supervisorId}/maintenance_notices

    """

    method_name = "Supervisor:MaintenanceNoticesGet"

    def invoke(self):
        self.method = "GET"
        self.path = f"/supervisors/{self.userId}/maintenance_notices"
        super().invoke()
        return self.response.json()


class MaintenanceNoticesAccept(SupervisorRestMethod):
    """ Returns an array of maintenance notices.
    PUT /supervisors/{supervisorId}/maintenance_notices/{noticeId}/accept

    """

    method_name = "supervisor:MaintenanceNoticesAccept"

    def invoke(self, noticeId):
        self.method = "PUT"
        self.path = f"/supervisors/{self.userId}/maintenance_notices/{noticeId}/accept"
        super().invoke()
        return self.response.json()


class SupervisorLoginState(SupervisorRestMethod):
    method_name = "Supervisor:SupervisorLoginState"

    def invoke(self):
        self.method = "GET"
        self.path = f"/supervisors/{self.userId}/login_state"
        logging.debug(f"URL: {self.base_api_url}{self.context_path}{self.path}")
        super().invoke()
        return self.response.text.strip('"')


class SupervisorSessionStart(SupervisorRestMethod):
    """Creates a session and registers the station for the agent.
    PUT /supervisors/{supervisorId}/session_start

    The initial login state must be in SELECT_STATION state. This request
    modifies the agent’s login state. If successful, the request changes the
    LoginState value and sends the EVENT_STATION_UPDATED and
    EVENT_LOGIN_STATE_UPDATED events. The agent must have the
    CAN_RUN_WEB_AGENT permission
    """

    method_name = "Supervisor:SupervisorSessionStart"

    def invoke(self, stationId="", stationType="EMPTY", stationState="DISCONNECTED"):
        self.method = "PUT"
        self.path = f"/supervisors/{self.userId}/session_start"
        payload = {
            "state": stationState,
            "stationId": stationId,
            "stationType": stationType,
        }
        super().invoke(payload=payload)
        if self.response.status_code < 400:
            return
        
        else:
            raise Exception(f"Error: {self.response.status_code} - {self.response.text}")
