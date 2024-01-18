import logging

from .base import AgentRestMethod
from five9.config import CONTEXT_PATHS
from five9.exceptions import Five9DuplicateLoginError

#####################################################################
# Agent and Agent REST API Session Start Methods
#####################################################################


class MaintenanceNoticesGet(AgentRestMethod):
    """Returns an array of maintenance notices.
    GET /agents/{agentId}/maintenance_notices

    """

    method_name = "Agent:MaintenanceNoticesGet"

    def invoke(self):
        self.method = "GET"
        self.path = f"/agents/{self.userId}/maintenance_notices"
        super().invoke()
        return self.response.json()


class MaintenanceNoticesAccept(AgentRestMethod):
    """ Returns an array of maintenance notices.
    PUT /agents/{agentId}/maintenance_notices/{noticeId}/accept

    """

    method_name = "agent:MaintenanceNoticesAccept"

    def invoke(self, noticeId):
        self.method = "PUT"
        self.path = f"/agents/{self.userId}/maintenance_notices/{noticeId}/accept"
        super().invoke()
        return self.response.json()
    

class AgentLoginState(AgentRestMethod):
    method_name = "Agent:AgentLoginState"

    def invoke(self):
        self.method = "GET"
        self.path = f"/agents/{self.userId}/login_state"
        super().invoke()
        return self.response.text.strip('"')


class AgentSessionStart(AgentRestMethod):
    """Registers the station for the agent.
    PUT /agents/{agentId}/session_start

    The initial login state must be in SELECT_STATION state. This request
    modifies the agent’s login state. If successful, the request changes the
    LoginState value and sends the EVENT_STATION_UPDATED and
    EVENT_LOGIN_STATE_UPDATED events. The agent must have the
    CAN_RUN_WEB_AGENT permission
    """

    method_name = "Agent:AgentSessionStart"

    def invoke(self, stationId="", stationType="EMPTY", stationState="DISCONNECTED"):
        self.method = "PUT"
        self.path = f"/agents/{self.userId}/session_start"
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
        
class LogOut(AgentRestMethod):
    """Logs out the agent.
    PUT /auth/logout

    """

    method_name = "Agent:LogOut"

    def invoke(self):
        self.method = "POST"
        self.path = f"/auth/logout"
        super().invoke()
        if self.response.status_code < 400:
            return
        
        else:
            raise Exception(f"Error: {self.response.status_code} - {self.response.text}")        
