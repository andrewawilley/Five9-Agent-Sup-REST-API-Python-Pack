import asyncio
import logging

import websockets

from five9.client import VccClient
from five9.config import CONTEXT_PATHS

from five9.private.credentials import ACCOUNTS



class Five9SupervisorSocket:
    def __init__(self, client: VccClient, socket_key: str = None, max_pings: int = 3):
        self.client = client
        socket_context_path = CONTEXT_PATHS["websocket_super"]
        self.uri = f"wss://{client.host}:{client.port}{CONTEXT_PATHS['websocket_super']}"
        self.uri = self.uri.format(socket_key=socket_key)
        self.max_pings = max_pings
        self.pings_sent = 0
        logging.debug(f"WebSocket URI: {self.uri}")

    async def send_ping(self, websocket):
        while True:
            try:
                await websocket.send('ping')
                self.pings_sent += 1
                if self.pings_sent >= self.max_pings:
                    logging.debug("Max pings sent, closing connection.")
                    await websocket.close()
                    break
                logging.debug("Ping sent")
                await asyncio.sleep(15)  # Send a ping every 15 seconds
            except websockets.ConnectionClosed:
                logging.debug("Connection closed, stopping ping.")
                break

    async def handle_messages(self, websocket):
        async for message in websocket:
            logging.debug(f"Message received: {message}")
            # Here you can add your event handler logic based on the received message
            # if message == 'some_event':
            #     handle_some_event()

    async def connect(self):
        cookie_header = '; '.join([f"{cookie.name}={cookie.value}" for cookie in self.client.session_cookies])
        headers = {
            "Authorization": f"Bearer-{self.client.tokenId}",  # Use the token provided during initialization
            "Cookie": cookie_header
        }
        
        async with websockets.connect(self.uri, extra_headers=headers) as websocket:
            # Run sending pings and message handler concurrently
            await asyncio.gather(
                self.send_ping(websocket),
                self.handle_messages(websocket),
            )
    
    async def close(self):
        if self.websocket and self.websocket.open:
            await self.websocket.close()
            print("WebSocket closed.")
