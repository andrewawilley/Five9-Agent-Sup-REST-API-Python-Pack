import logging
from typing import Dict, Any

import requests

from five9_agent_sup_rest.config import CONTEXT_PATHS


class FiveNineRestMethod:
    # """Base class for all Five9 REST methods.

    def __init__(self, config, *args, **kwargs):
        self.call_count = 0
        self.update_config(config)

    def update_config(self, config):
        self.config = config
        config.subscribe_observer(self)

    def invoke(self, *args, **kwargs):
        url = f"{self.config.base_api_url}{self.context_path}{self.path}"
        qstring_params = kwargs.get("qstring_params", None)
        payload = kwargs.get("payload", None)

        req = requests.Request(
            method=self.method,
            url=url,
            headers=self.config.api_header,
        )

        if self.method != "GET" and payload:
            req.json = payload
        if qstring_params:
            req.params = qstring_params

        prepared_request = req.prepare()

        logging.debug(
            f"FiveNineRestMethod Prepared Request:\n{prepared_request.__dict__}"
        )

        try:
            self.response = requests.Session().send(prepared_request)
            # self.response.raise_for_status()
            logging.info(f"{self.method_name} - RESPONSE: {self.response.status_code}")
            logging.debug(f"{self.method_name} -    TEXT: {self.response.text}")

        except requests.exceptions.HTTPError as errh:
            logging.error(f"{self.method_name} - HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"{self.method_name} - Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            logging.error(f"{self.method_name} - Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            logging.error(f"{self.method_name} - Unexpected Error: {err}")
        
        return self.response


class SupervisorRestMethod(FiveNineRestMethod):
    """Base class for all Five9 Supervisor REST methods."""

    context_path = CONTEXT_PATHS["sup_rest"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def method_name(self):
        return f"Supervisor:{self.__class__.__name__}" 

class AgentRestMethod(FiveNineRestMethod):
    """Base class for all Five9 Agent REST methods."""

    context_path = CONTEXT_PATHS["agent_rest"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def method_name(self):
        return f"Agent:{self.__class__.__name__}" 
    