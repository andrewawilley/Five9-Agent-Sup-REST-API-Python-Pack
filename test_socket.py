import asyncio
import logging

from five9.client import VCC_Client

from five9.sockets import Five9SupervisorSocket

from five9.private.credentials import ACCOUNTS

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    username = ACCOUNTS["default_test_account"]["username"]
    password = ACCOUNTS["default_test_account"]["password"]

    c = VCC_Client(username=username, password=password, log_in_on_create=True)
    c.initialize_supervisor_session()

    # logging.debug(f"Token: {c.tokenId}")

    supervisor_socket = Five9SupervisorSocket(c)

    # Run the connect method to start the WebSocket connection
    asyncio.run(supervisor_socket.connect())

    

