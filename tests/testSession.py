import logging

import unittest
from unittest.mock import patch

from five9.client import VccClient, VccClientSessionConfig

from five9.sockets import Five9SupervisorSocket

from five9.private.credentials import ACCOUNTS


# run with coverage
# coverage run -m unittest discover -s tests -p "test*.py" -v
# coverage html


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class TestCreateSessions(unittest.TestCase):
    # def test_login(self):
    #     username = ACCOUNTS["default_test_account"]["username"]
    #     password = ACCOUNTS["default_test_account"]["password"]

    #     session_config = VccClientSessionConfig(username=username, password=password)

    #     expected_login_payload = {
    #         "passwordCredentials": {
    #             "username": username,
    #             "password": password,
    #         },
    #         "appKey": "mypythonapp-supervisor-session",
    #         "policy": "AttachExisting",
    #     }

    #     self.assertEqual(session_config.login_payload, expected_login_payload)

    #     session_config.login()

    def test_supervisor_session(self):
        username = ACCOUNTS["default_test_account"]["username"]
        password = ACCOUNTS["default_test_account"]["password"]

        c = VccClient(username=username, password=password)
        c.initialize_supervisor_session()

        notices = c.supervisor.MaintenanceNoticesGet.invoke()
        c.supervisor.LogOut.invoke()

    
    def test_agent_session(self):
        username = ACCOUNTS["default_test_account"]["username"]
        password = ACCOUNTS["default_test_account"]["password"]

        c = VccClient(username=username, password=password)
        c.initialize_agent_session()

        notices = c.agent.MaintenanceNoticesGet.invoke()
        c.agent.LogOut.invoke()
