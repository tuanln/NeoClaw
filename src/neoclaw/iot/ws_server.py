"""WebSocket server for real-time claw control from browser."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Set

from neoclaw.config.settings import get_settings

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for real-time claw control."""

    def __init__(self, command_handler=None):
        self._settings = get_settings().iot
        self._clients: Set = set()
        self._server = None
        self._command_handler = command_handler

    async def start(self) -> None:
        """Start the WebSocket server."""
        try:
            import websockets

            self._server = await websockets.serve(
                self._handle_client,
                self._settings.ws_host,
                self._settings.ws_port,
            )
            logger.info(
                f"WebSocket server started on ws://{self._settings.ws_host}:{self._settings.ws_port}"
            )
        except ImportError:
            logger.warning("websockets package not installed")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def broadcast(self, data: dict) -> None:
        """Send data to all connected clients."""
        if not self._clients:
            return
        message = json.dumps(data)
        await asyncio.gather(
            *(client.send(message) for client in self._clients),
            return_exceptions=True,
        )

    async def _handle_client(self, websocket, path=None) -> None:
        """Handle a WebSocket client connection."""
        self._clients.add(websocket)
        logger.info(f"Client connected ({len(self._clients)} total)")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if self._command_handler:
                        response = self._command_handler(data)
                        if response:
                            await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))
        except Exception:
            pass
        finally:
            self._clients.discard(websocket)
            logger.info(f"Client disconnected ({len(self._clients)} total)")

    @property
    def client_count(self) -> int:
        return len(self._clients)
