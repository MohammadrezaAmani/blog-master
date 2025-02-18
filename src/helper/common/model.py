from tortoise import fields

from src.base import BaseModel


class Language(BaseModel):
    name = fields.CharField(max_length=256)
    description = fields.TextField(null=True)
    data = fields.JSONField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        table = "language"


class Tag(BaseModel):
    name = fields.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        table = "tag"


class Action(BaseModel):
    name = fields.CharField(max_length=128, unique=True)
    user = fields.ForeignKeyField("models.User", related_name="action")
    to = fields.ForeignKeyField("models.User", related_name="to_action")
    description = fields.TextField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        table = "action"


class React(BaseModel):
    name = fields.CharField(max_length=128, unique=True)
    user = fields.ForeignKeyField("models.User", related_name="react")
    description = fields.TextField(null=True)

    def __str__(self):
        return self.emoji

    class Meta:
        table = "react"


class Comment(BaseModel):
    text = fields.TextField()
    user = fields.ForeignKeyField("models.User", related_name="comment")
    react = fields.ManyToManyField("models.React", related_name="comment")
    tag = fields.ManyToManyField("models.Tag", related_name="comment")
    vote = fields.IntField(null=True)

    def __str__(self):
        return f"Comment {self.id} by User {self.user_id}"

    class Meta:
        table = "comment"


class Category(BaseModel):
    name = fields.CharField(max_length=128, unique=True)
    user = fields.ForeignKeyField("models.User", related_name="category")
    react = fields.ManyToManyField("models.React", related_name="category")
    tag = fields.ManyToManyField("models.Tag", related_name="category")
    parent = fields.ManyToManyField("models.Category", related_name="child")
    comment = fields.ManyToManyField("models.Comment", related_name="category")
    description = fields.TextField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        table = "category"
