from peewee import *
from user import db, User

db.connect()
db.create_tables([User])