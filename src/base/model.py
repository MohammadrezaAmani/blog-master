from argon2 import PasswordHasher
from tortoise import fields, models

ph = PasswordHasher()


class BaseModel(models.Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    slug = fields.CharField(unique=True, null=True, max_length=512)

    class Meta:
        abstract = True


class BaseUser(models.Model):
    username = fields.CharField(max_length=20, unique=True)
    password = fields.CharField(max_length=128, null=True)

    class Meta:
        abstract = True

    def verify_password(self, password: str) -> bool:
        try:
            ph.verify(self.password, password)
            return True
        except Exception:
            return False

    async def save(self, *args, password_changed: bool = False, **kwargs):
        if self.id is None or password_changed:
            self.password = BaseUser.hash_password(self.password)
        await super().save(*args, **kwargs)

    def update_from_dict(self, data: dict):
        for field, value in data.items():
            setattr(self, field, value)
        return self

    @staticmethod
    def hash_password(password: str) -> str:
        return ph.hash(password)

    @staticmethod
    def veirfy_password(password: str, hash: str) -> bool:
        try:
            ph.verify(hash, password)
            return True
        except Exception:
            return False
