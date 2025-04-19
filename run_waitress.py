from waitress import serve
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

# ... your Flask application routes and SocketIO event handlers here

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=False) 