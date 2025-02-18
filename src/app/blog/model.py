from tortoise import fields

from src.base import BaseModel


class Post(BaseModel):
    title = fields.CharField()
    body = fields.TextField(null=True)
    user = fields.ForeignKeyField("models.User", related_name="post")
    react = fields.ManyToManyField("models.React", related_name="post")
    comment = fields.ManyToManyField("models.Comment", related_name="post")
    category = fields.ManyToManyField("models.Category", related_name="post")
    tag = fields.ManyToManyField("models.Tag", related_name="post")
    related_post = fields.ManyToManyField("models.Post", related_name="related")

    def __repr__(self):
        return self.__str__()

    class Meta:
        table = "post"
