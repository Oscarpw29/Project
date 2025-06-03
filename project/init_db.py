from project import db, create_app, models

def create_db():
    with create_app().app_context():
        db.create_all()