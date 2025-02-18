from tortoise import fields

from src.base import BaseModel, BaseUser


class User(BaseModel, BaseUser):
    name = fields.CharField(max_length=50, null=True)
    username = fields.CharField(max_length=50, unique=True)
    is_active = fields.BooleanField(default=True)
    mobile = fields.CharField(max_length=20, null=True)
    group = fields.ForeignKeyField("models.Group", related_name="user")
    # image = fields.ManyToManyField("models.File", related_name="user_profile")
