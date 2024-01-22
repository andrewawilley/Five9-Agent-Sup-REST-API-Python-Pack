import asyncio
import logging

from five9.client import VccClient
from five9.sockets import Five9SupervisorSocket

from five9.private.credentials import ACCOUNTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


if __name__ == "__main__":

    username = ACCOUNTS["default_test_account"]["username"]
    password = ACCOUNTS["default_test_account"]["password"]

    client = VccClient(username=username, password=password)
    client.initialize_supervisor_session()

    # logging.debug(f"Token: {c.tokenId}")

    supervisor_socket = Five9SupervisorSocket(client)

    # Run the connect method to start the WebSocket connection
    asyncio.run(supervisor_socket.connect())
