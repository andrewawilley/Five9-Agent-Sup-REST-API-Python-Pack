import asyncio
import logging
import threading

import websockets

from five9.client import VccClient
from five9.config import CONTEXT_PATHS

from five9.private.credentials import ACCOUNTS



class Five9SupervisorSocket:
    def __init__(self, client: VccClient, socket_key: str = None):
        self.client = client
        self.socket_context_path = CONTEXT_PATHS["websocket_super"]
        self.uri = f"wss://{client.session_configuration.host}:{client.session_configuration.port}{CONTEXT_PATHS['websocket_super']}"
        self.uri = self.uri.format(socket_key=socket_key)

        self.disconnect_requested = False

        logging.info(f"WebSocket URI: {self.uri}")

    async def send_ping(self, websocket):
        while True:
            if self.disconnect_requested:
                logging.info("Disconnect requested, stopping ping.")
                break
            try:
                await websocket.send('ping')
                logging.info("Ping sent")
                await asyncio.sleep(15)  # Send a ping every 15 seconds

            except websockets.ConnectionClosed:
                logging.info("Connection closed, stopping ping.")
                break

    async def handle_messages(self, websocket):
        async for message in websocket:
            if self.disconnect_requested:
                logging.info("Disconnect requested, stopping message handler.")
                break
            
            logging.debug(f"Message received: {message}")
            

    async def listen_for_disconnect(self):
        # Use a thread to listen for the disconnect command
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._await_disconnect, loop)

    def _await_disconnect(self, loop):
        input("Press Enter to disconnect...")
        self.disconnect_requested = True
        logging.info("Disconnect command received.")
        # Use the passed event loop to schedule the close coroutine
        asyncio.run_coroutine_threadsafe(self.close(), loop)        

    async def connect(self):
        headers = {
            "Authorization": f"Bearer-{self.client.session_configuration.tokenId}",  # Use the token provided during initialization
            "Cookie": self.client.session_configuration.cookies_header,  # Use the cookies provided during initialization
        }
        
        async with websockets.connect(self.uri, extra_headers=headers) as websocket:
            self.websocket = websocket  # Assign the websocket instance to self.websocket
            # Run sending pings and message handler concurrently
            await asyncio.gather(
                self.send_ping(websocket),
                self.handle_messages(websocket),
                self.listen_for_disconnect(),
            )
    
    async def close(self):
        if hasattr(self, 'websocket') and self.websocket and self.websocket.open:
            await self.websocket.close()
            print("WebSocket closed.")
