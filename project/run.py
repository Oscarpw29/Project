from flask import Flask
from flask_socketio import SocketIO

from . import socketio, create_app

if __name__ == '__main__':
    socketio.run(create_app(), debug=True)