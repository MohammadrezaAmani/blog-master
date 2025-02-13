import json
import logging
import time
import uuid
from collections import deque
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

from fastapi import Security, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, ValidationError
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]


class ConnectionMetadata(BaseModel):
    websocket: WebSocket
    connection_id: str
    user: Optional[Any] = None
    client_ip: Optional[str] = None
    auth: bool = False


class RateLimitExceeded(Exception):
    pass


class WebSocketManager:
    def __init__(
        self,
        redis_url: Optional[str] = None,
        rate_limit: int = 100,
        max_message_size: int = 1024 * 1024,
        auth_dependency: Optional[Callable] = None,
        message_model: Optional[BaseModel] = WebSocketMessage,
    ):
        self.redis = Redis.from_url(redis_url) if redis_url else None
        self.rate_limit = rate_limit
        self.max_message_size = max_message_size
        self.auth_dependency = auth_dependency
        self.message_model = message_model
        self.active_connections: Dict[str, ConnectionMetadata] = {}
        self.rate_limits: Dict[str, deque] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        client_ip = websocket.client.host if websocket.client else None
        metadata = ConnectionMetadata(
            websocket=websocket, connection_id=connection_id, client_ip=client_ip
        )
        self.active_connections[connection_id] = metadata
        logger.info(f"New connection: {connection_id}")
        return metadata

    async def disconnect(self, connection_id: str, code: int = 1000):
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].websocket.close(code=code)
            del self.active_connections[connection_id]
            logger.info(f"Connection closed: {connection_id}")

    async def authenticate(self, websocket: WebSocket, metadata: ConnectionMetadata):
        if self.auth_dependency:
            try:
                security_scopes = websocket.scope.get("securities", [])
                user = await Security(self.auth_dependency, scopes=security_scopes)(
                    websocket
                )
                metadata.user = user
                metadata.auth = True
            except Exception as e:
                logger.warning(f"Authentication failed: {str(e)}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise
        return metadata

    async def _check_rate_limit(self, connection_id: str):
        if self.redis:
            current = await self.redis.get(f"ws:ratelimit:{connection_id}")
            if current and int(current) >= self.rate_limit:
                raise RateLimitExceeded()
            await self.redis.incr(f"ws:ratelimit:{connection_id}")
            await self.redis.expire(f"ws:ratelimit:{connection_id}", 60)
        else:
            now = time.time()
            if connection_id not in self.rate_limits:
                self.rate_limits[connection_id] = deque(maxlen=self.rate_limit)

            if len(self.rate_limits[connection_id]) >= self.rate_limit:
                oldest = self.rate_limits[connection_id][0]
                if now - oldest < 60:
                    raise RateLimitExceeded()
                self.rate_limits[connection_id].popleft()

            self.rate_limits[connection_id].append(now)

    def _validate_message(self, message: Union[str, bytes]):
        if isinstance(message, bytes):
            if len(message) > self.max_message_size:
                raise ValueError("Message size exceeds limit")
            return message

        if isinstance(message, str):
            if self.message_model:
                parsed = json.loads(message)
                return self.message_model(**parsed)
            return message

        raise ValueError("Unsupported message type")

    async def broadcast(self, message: Union[str, bytes, BaseModel]):
        if isinstance(message, BaseModel):
            message = message.model_dump_json()
        for conn in self.active_connections.values():
            await conn.websocket.send_text(message)

    async def handle_websocket(
        self,
        websocket: WebSocket,
        *,
        on_connect: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
    ):
        connection_id = str(uuid.uuid4())
        metadata = await self.connect(websocket, connection_id)

        try:
            await self.authenticate(websocket, metadata)

            if on_connect:
                await on_connect(metadata)

            while True:
                try:
                    message = await websocket.receive()
                    raw_data = message.get("text") or message.get("bytes")

                    await self._check_rate_limit(connection_id)

                    validated = self._validate_message(raw_data)

                    if on_message:
                        response = await on_message(metadata, validated)
                        if response:
                            await websocket.send_json(response)

                except RateLimitExceeded:
                    await websocket.send_json(
                        {"type": "error", "data": "Rate limit exceeded"}
                    )
                    await self.disconnect(
                        connection_id, status.WS_1008_POLICY_VIOLATION
                    )
                    break
                except ValidationError as e:
                    await websocket.send_json({"type": "error", "data": e.errors()})
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                    await websocket.send_json(
                        {"type": "error", "data": "Internal server error"}
                    )
                    break
        finally:
            if on_disconnect:
                await on_disconnect(metadata)
            await self.disconnect(connection_id)


def websocket_handler(
    manager: WebSocketManager,
    on_connect: Optional[Callable] = None,
    on_message: Optional[Callable] = None,
    on_disconnect: Optional[Callable] = None,
):
    def decorator(func):
        @wraps(func)
        async def wrapper(websocket: WebSocket):
            await manager.handle_websocket(
                websocket,
                on_connect=on_connect,
                on_message=on_message,
                on_disconnect=on_disconnect,
            )

        return wrapper

    return decorator
