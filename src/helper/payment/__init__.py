"""
Payment Gateway Integration for Iranian Gateways (ZarinPal Example)
با معماری Enterprise-Level و رعایت تمام استانداردهای امنیتی
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import AnyUrl, BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from tortoise import fields
from tortoise.contrib.fastapi import register_tortoise
from tortoise.models import Model

logger = logging.getLogger("payment_gateway")
logger.setLevel(logging.INFO)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


class settings:
    ZARINPAL_MERCHANT_ID = "your_merchant_id"
    API_KEY = "your_secret_key"
    DATABASE_URL = "sqlite://db.sqlite3"


class Transaction(Model):
    id = fields.UUIDField(pk=True)
    amount = fields.DecimalField(max_digits=12, decimal_places=0)  # به ریال
    user_id = fields.IntField()
    status = fields.CharField(max_length=20, default="pending")
    gateway = fields.CharField(max_length=20)
    gateway_transaction_id = fields.CharField(max_length=100, null=True)
    verification_code = fields.UUIDField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    metadata = fields.JSONField(null=True)


class PaymentInitiateRequest(BaseModel):
    amount: int = Field(..., gt=1000, le=100000000, description="Amount in Rials")
    callback_url: AnyUrl
    user_id: uuid.UUID
    description: Optional[str] = Field(None, max_length=255)


class PaymentCallback(BaseModel):
    Authority: str
    Status: str


class BasePaymentGateway:
    def __init__(self):
        self.merchant_id: str
        self.sandbox: bool
        self.base_url: str

    async def _send_request(self, endpoint: str, data: dict): ...
    async def initiate_payment(
        self, amount: int, callback_url: str, description: str
    ) -> dict: ...
    async def verify_payment(self, authority: str, amount: int) -> dict: ...


class ZarinPalPaymentGateway:
    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.sandbox = settings.DEBUG
        self.base_url = (
            "https://sandbox.zarinpal.com/pg/rest/WebGate/"
            if self.sandbox
            else "https://api.zarinpal.com/pg/v4/payment/"
        )

    async def _send_request(self, endpoint: str, data: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

    async def initiate_payment(
        self, amount: int, callback_url: str, description: str
    ) -> dict:
        data = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "callback_url": str(callback_url),
            "description": description,
            "metadata": {"mobile": None, "email": None},
        }

        try:
            result = await self._send_request("request.json", data)

            if result["Status"] == 100:
                return {
                    "authority": result["Authority"],
                    "payment_url": f"https://{'sandbox' if self.sandbox else 'www'}.zarinpal.com/pg/StartPay/{result['Authority']}",
                }
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Payment gateway error: {result['Status']}",
            )
        except httpx.HTTPError as e:
            logger.error(f"Gateway connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment gateway unavailable",
            )

    async def verify_payment(self, authority: str, amount: int) -> dict:
        data = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "authority": authority,
        }

        try:
            result = await self._send_request("verify.json", data)

            if result["Status"] == 100:
                return {
                    "ref_id": result["RefID"],
                    "status": "success",
                    "verification": result,
                }
            return {"status": "failed", "details": result}
        except httpx.HTTPError as e:
            logger.error(f"Verification failed: {str(e)}")
            return {"status": "verification_error"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Payment Gateways
    app.state.zarinpal = ZarinPalPaymentGateway()
    yield
    # Cleanup resources
    await app.state.zarinpal.close()


app = FastAPI(lifespan=lifespan)

# Security Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )
    return api_key


@app.post("/payment/initiate", status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    request: PaymentInitiateRequest, api_key: str = Depends(get_api_key)
):
    # Generate unique verification code
    verification_code = uuid.uuid4()

    # Save transaction to DB
    transaction = await Transaction.create(
        id=uuid.uuid4(),
        amount=request.amount,
        user_id=request.user_id,
        gateway="zarinpal",
        verification_code=verification_code,
        metadata={
            "description": request.description,
            "callback_url": str(request.callback_url),
        },
    )

    # Initiate payment
    try:
        payment_data = await app.state.zarinpal.initiate_payment(
            amount=request.amount,
            callback_url=request.callback_url,
            description=request.description or "No description",
        )
    except HTTPException as e:
        await transaction.update_from_dict({"status": "failed"})
        raise e

    # Update transaction with gateway data
    await transaction.update_from_dict(
        {"gateway_transaction_id": payment_data["authority"], "status": "redirected"}
    )

    return {
        "payment_url": payment_data["payment_url"],
        "verification_code": str(verification_code),
        "transaction_id": str(transaction.id),
    }


@app.get("/payment/verify")
async def verify_payment(authority: str, status: str, verification_code: uuid.UUID):
    # Find transaction
    transaction = await Transaction.get_or_none(
        gateway_transaction_id=authority, verification_code=verification_code
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    if transaction.status != "redirected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid transaction state"
        )

    # Verify payment
    verification = await app.state.zarinpal.verify_payment(
        authority=authority, amount=int(transaction.amount)
    )

    # Update transaction
    await transaction.update_from_dict(
        {
            "status": verification["status"],
            "metadata": {**transaction.metadata, "verification_response": verification},
        }
    )

    return {
        "status": verification["status"],
        "ref_id": verification.get("ref_id"),
        "transaction_id": str(transaction.id),
    }


# -------------------- Database Config --------------------
register_tortoise(
    app,
    db_url=settings.DATABASE_URL,
    modules={"models": ["main"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
