import logging

import asyncio

import unittest
from unittest.mock import patch, MagicMock

from five9_agent_sup_rest.client import Five9RestClient, Five9Socket

from five9_agent_sup_rest.private.credentials import ACCOUNTS



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class TestCreateSessions(unittest.TestCase):
    def setUp(self):
        self.username = ACCOUNTS["default_test_account"]["username"]
        self.password = ACCOUNTS["default_test_account"]["password"]
        self.client = Five9RestClient(username=self.username, password=self.password)
        

    def tearDown(self):
        # logging out can be invoked on either the supervisor or agent session
        # and will close both sessions if they are open
        self.client.supervisor.LogOut.invoke()
        logging.info("\nTeardown Complete\n")

    def test_supervisor_session(self):
        logging.info("\n\nsetUp for Test")
        self.client.initialize_supervisor_session()
        self.assertEqual(self.client.supervisor_login_state, "WORKING")

    def test_agent_session(self):        
        self.assertEqual(self.client.agent_login_state, "SELECT_STATION")
        self.client.initialize_agent_session()        
        self.assertIn(self.client.agent_login_state, ["WORKING", "SELECT_SKILLS"])
        
    def test_supervisor_socket(self):
        self.client.initialize_supervisor_session()
        supervisor_socket = Five9Socket(self.client, "supervisor", "unittests")
        supervisor_socket.connect()
