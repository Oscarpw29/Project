from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLAlchemy()

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002

socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = '<KEY>'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # blueprint for auth routes in app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for main routes in app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app)

    print("socketio initialized")

    from . import sockets

    return app
