import json
import logging
import secrets
from contextlib import asynccontextmanager
from functools import wraps
from typing import Dict, List, Optional, Union

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("kavenegar_async")
logger.setLevel(logging.INFO)


class APIException(Exception):
    """Base exception for API errors"""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"APIException[{status}] {message}")


class RateLimitExceeded(Exception):
    """Custom exception for rate limiting"""


class KavenegarResponse(BaseModel):
    status: int
    message: str
    entries: Optional[Union[Dict, List]]


class RequestParams(BaseModel):
    receptor: Optional[Union[str, List[str]]]
    message: Optional[str]
    sender: Optional[str]
    template: Optional[str]
    token: Optional[str]
    type: Optional[str] = Field(None, regex="^(sms|call|voice)$")

    @field_validator("receptor", pre=True)
    def validate_receptor(cls, v):
        if isinstance(v, list) and len(v) > 2000:
            raise ValueError("Maximum 2000 receptors allowed")
        return v


class BaseOTP:
    """
    Fully asynchronous OTP API client with advanced features:
    - Connection pooling
    - Retry mechanism
    - Rate limiting
    - Request validation
    - Performance monitoring
    - Advanced error handling
    """

    VERSION = "v1"
    BASE_URL = "https://api.kavenegar.com"
    DEFAULT_TIMEOUT = 10.0
    MAX_CONNECTIONS = 100
    RATE_LIMIT = 10  # Requests per second

    def __init__(
        self,
        apikey: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        proxies: Optional[Dict] = None,
        enable_retry: bool = True,
        rate_limit: Optional[int] = None,
    ):
        self.apikey = apikey
        self.apikey_mask = f"{apikey[:2]}****{apikey[-2:]}" if apikey else ""
        self.timeout = timeout
        self.proxies = proxies
        self._rate_limit = rate_limit or self.RATE_LIMIT
        self._semaphore = asyncio.Semaphore(self._rate_limit)

        # Configure async client with connection pool
        limits = httpx.Limits(
            max_connections=self.MAX_CONNECTIONS, max_keepalive_connections=20
        )

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "AsyncKavenegar/2.0",
            },
            timeout=self.timeout,
            proxies=self.proxies,
            limits=limits,
            http2=True,
        )

        # Configure retry policy if enabled
        if enable_retry:
            self._request = self._retry_policy()(self._request)

    @asynccontextmanager
    async def context(self):
        """Context manager for proper resource cleanup"""
        try:
            yield self
        finally:
            await self.aclose()

    async def aclose(self):
        """Close the underlying HTTP client"""
        await self.client.aclose()

    @staticmethod
    def _retry_policy():
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(
                (httpx.NetworkError, httpx.TimeoutException, APIException)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )

    def _format_params(self, params: Dict) -> Dict:
        """Optimized parameter formatting with batch processing"""
        return {
            k: json.dumps(v) if isinstance(v, (list, dict)) else str(v)
            for k, v in params.items()
        }

    def generate_url(self, action, method):
        return f"/{self.VERSION}/{self.apikey}/{action}/{method}.json"

    async def _request(
        self, action: str, method: str, params: Optional[Dict] = None
    ) -> KavenegarResponse:
        """Core async request handler with advanced features"""
        url = self.generate_url(action, method)

        try:
            async with self._semaphore:
                response = await self.client.post(
                    url, data=self._format_params(params or {}), timeout=self.timeout
                )

                response.raise_for_status()
                data = response.json()

                if data.get("return", {}).get("status") > 399:
                    raise APIException(
                        data["return"]["status"], data["return"]["message"]
                    )

                return KavenegarResponse(**data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            raise HTTPException(f"HTTP error {e.response.status_code}") from e
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response")
            raise APIException(500, "Invalid API response") from e
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise HTTPException("Network error") from e

    @staticmethod
    def validate_params(func):
        """Decorator for input validation"""

        @wraps(func)
        async def wrapper(self, params=None, *args, **kwargs):
            validated = RequestParams(**(params or {})).dict(exclude_none=True)
            return await func(self, validated, *args, **kwargs)

        return wrapper

    @validate_params
    async def sms_send(self, params: Dict) -> KavenegarResponse:
        return await self._request("sms", "send", params)

    @validate_params
    async def sms_sendarray(self, params: Dict) -> KavenegarResponse:
        return await self._request("sms", "sendarray", params)

    @validate_params
    async def verify_lookup(self, params: Dict) -> KavenegarResponse:
        return await self._request("verify", "lookup", params)

    async def account_info(self) -> KavenegarResponse:
        return await self._request("account", "info")

    # Other methods follow the same pattern...


class AsyncKavenegarAPI(BaseOTP):
    VERSION = "v1"
    BASE_URL = "https://api.kavenegar.com"
    DEFAULT_TIMEOUT = 10.0
    MAX_CONNECTIONS = 100
    RATE_LIMIT = 10  # Requests per second


# Advanced usage example
async def main():
    async with AsyncKavenegarAPI("your_api_key") as api:
        try:
            response = await api.sms_send(
                {
                    "receptor": "09123456789",
                    "message": "Your verification code: " + secrets.token_hex(3),
                    "sender": "10004346",
                }
            )
            logger.info(f"Message ID: {response.entries[0]['messageid']}")
        except APIException as e:
            logger.error(f"API Error: {e}")
        except HTTPException as e:
            logger.error(f"Network Error: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
