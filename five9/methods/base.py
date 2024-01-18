import logging
from typing import Dict, Any

import requests

from five9.config import CONTEXT_PATHS

class FiveNineRestMethod:
    # """Base class for all Five9 REST methods.

    def __init__(self, *args, **kwargs):
        self.call_count = 0

    def invoke(self, *args, **kwargs):
        url = f"{self.base_api_url}{self.context_path}{self.path}"
        qstring_params = kwargs.get("qstring_params", None)
        payload = kwargs.get("payload", None)

        logging.debug(f"URL: {url}")

        req = requests.Request(
            method=self.method,
            url=url,
            headers=self.api_header,
        )

        if self.method != "GET" and payload:
            req.json = payload
        if qstring_params:
            req.params = qstring_params

        prepared_request = req.prepare()

        logging.debug(f"PREPARED REQUEST: {prepared_request.__dict__}")

        try:
            self.response = requests.Session().send(prepared_request)
            self.response.raise_for_status()
            logging.debug(f"RESPONSE: {self.response.text}")

        except requests.exceptions.HTTPError as errh:
            logging.error(f"FiveNineRestMethod - HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"FiveNineRestMethod - Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            logging.error(f"FiveNineRestMethod - Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            logging.error(f"FiveNineRestMethod - Unexpected Error: {err}")


class SupervisorRestMethod(FiveNineRestMethod):
    """Base class for all Five9 Supervisor REST methods.

    """
    context_path = CONTEXT_PATHS["sup_rest"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    

class AgentRestMethod(FiveNineRestMethod):
    """Base class for all Five9 Agent REST methods.

    """
    context_path = CONTEXT_PATHS["agent_rest"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)