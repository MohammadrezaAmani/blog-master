from enum import Enum

from src.config import USER_MODEL
from src.helper.user.model import User
from tortoise import fields, models


class ActionEnum(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"


class Log(models.Model):
    id = fields.BigIntField(pk=True)
    user: User = fields.ForeignKeyField(
        USER_MODEL, related_name="log", on_delete=fields.CASCADE, null=True
    )
    action = fields.CharEnumField(ActionEnum, max_length=20, null=True)
    db_model = fields.CharField(max_length=255, null=True)
    db_model_id = fields.CharField(max_length=255, null=True)
    ip_address = fields.CharField(max_length=45, null=True)
    mac_address = fields.CharField(max_length=17, null=True)
    browser = fields.CharField(max_length=255, null=True)
    user_agent = fields.TextField(null=True)
    location = fields.CharField(max_length=255, null=True)
    last_value = fields.JSONField(null=True)
    is_success = fields.BooleanField(deafult=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "log"
