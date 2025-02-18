from tortoise import fields

from src.base import BaseModel


class Permission(BaseModel):
    name = fields.CharField(max_length=100, unique=True)
    to = fields.CharField(max_length=100)
    action = fields.CharField(max_length=100)
    description = fields.CharField(max_length=100, null=True, blank=True)

    def __repr__(self):
        return self.__str__()


class Group(BaseModel):
    name = fields.CharField(max_length=100, unique=True)
    parent = fields.ForeignKeyField(model_name="models.Group", null=True, blank=True)

    permissions = fields.ManyToManyField("models.Permission", related_name="group")

    def __repr__(self):
        return self.__str__()


class Access(BaseModel):
    user = fields.ForeignKeyField("models.User")
    role = fields.CharField(max_length=256)

    class Meta:
        table = "access"
