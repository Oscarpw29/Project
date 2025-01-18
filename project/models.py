from flask_login import current_user, UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(64))
    group = db.Column(db.String(68))
    access_level = db.Column(db.Integer)
    profilePicture = db.Column(db.String(255))
    last_seen = db.Column(db.DateTime)
    bio = db.Column(db.String(255))

