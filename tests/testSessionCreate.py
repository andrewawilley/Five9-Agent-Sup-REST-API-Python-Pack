import logging

import unittest
from unittest.mock import patch

from five9.client import VCC_Client
from five9.private.credentials import ACCOUNTS

# run with coverage
# coverage run -m unittest discover -s tests -p "test*.py" -v
# coverage html


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s",
)


class TestCreateSession(unittest.TestCase):
    def test_create_session(self):
        username = ACCOUNTS["default_test_account"]["username"]
        password = ACCOUNTS["default_test_account"]["password"]

        c = VCC_Client(username=username, password=password, log_in_on_create=True)

        expected_login_payload = {
            "passwordCredentials": {
                "username": username,
                "password": password,
            },
            "appKey": "mypythonapp-supervisor-session",
            "policy": "AttachExisting",
        }

        self.assertEqual(c.login_payload, expected_login_payload)      

        notices = c.supervisor.MaintenanceNoticesGet.invoke()
        logging.debug(f"UNITTEST - NOTICES: {notices}")
