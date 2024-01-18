import logging

from .base import FiveNineRestMethod
from five9.config import CONTEXT_PATHS

#####################################################################
# Agent and Supervisor REST API Session Start Methods
#####################################################################


class GetMaintenanceNotices(FiveNineRestMethod):
    """ Returns an array of maintenance notices.
    GET /agents/{agentId}/maintenance_notices

    """

    method_name = "Agent:GetMaintenanceNotices"

    def __init__(self, session_metadata):
        super().__init__(session_metadata)
        self.method = "GET"
        self.context = CONTEXT_PATHS["agent_rest"]
        self.path = f"/agents/{session_metadata.userId}/maintenance_notices"
        

# class AgentSessionStart(FiveNineRestMethod):
#     """Creates a session and registers the station for the agent.
#     PUT /agents/{agentId}/session_start

#     The initial login state must be in SELECT_STATION state. This request
#     modifies the agent’s login state. If successful, the request changes the
#     LoginState value and sends the EVENT_STATION_UPDATED and
#     EVENT_LOGIN_STATE_UPDATED events. The agent must have the
#     CAN_RUN_WEB_AGENT permission
#     """

#     method_name = "Agent:AgentSessionStart"

#     def __init__(self, session_metadata):
#         super().__init__(session_metadata)
#         self.method = "PUT"
#         self.context = CONTEXT_PATHS["agent_rest"]
#         self.path = "/agents/{agentId}/session_start"
#         self.path_params["agentId"] = session_metadata.userId
#         self.payload = {
#             "state": session_metadata.stationState,
#             "stationId": session_metadata.stationId,
#             "stationType": session_metadata.stationType,
#         }
