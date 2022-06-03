from peewee import *

db = SqliteDatabase('db/public.db')


class User(Model):
    telegram_id = CharField(null=False)
    template = TextField(null=True)

    class Meta:
        database = db
