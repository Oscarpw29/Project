from project import db, create_app, models

with create_app().app_context():
    db.create_all()