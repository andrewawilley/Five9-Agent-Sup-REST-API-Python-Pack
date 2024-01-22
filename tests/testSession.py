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
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class TestCreateSessions(unittest.TestCase):
    def setUp(self):
        logging.debug("setUp")
        self.username = ACCOUNTS["default_test_account"]["username"]
        self.password = ACCOUNTS["default_test_account"]["password"]
        self.client = VccClient(username=self.username, password=self.password)
        

    def tearDown(self) -> None:
        # logging out can be invoked on either the supervisor or agent session
        # and will close both sessions if they are open
        self.client.supervisor.LogOut.invoke()

    def test_session(self):
        self.assertIsInstance(self.client, VccClient)

    def test_supervisor_session(self):
        self.assertEqual(self.client.supervisor_login_state, "SELECT_STATION")
        self.client.initialize_supervisor_session()
        self.assertEqual(self.client.supervisor_login_state, "WORKING")

    def test_agent_session(self):        
        self.assertEqual(self.client.agent_login_state, "SELECT_STATION")
        self.client.initialize_agent_session()        
        self.assertIn(self.client.agent_login_state, ["WORKING", "SELECT_SKILLS"])
        
    def test_supervisor_socket(self):
        supervisor_socket = Five9SupervisorSocket(self.client)
        self.assertIsInstance(self.socket, Five9SupervisorSocket)
