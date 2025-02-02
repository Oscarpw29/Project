from waitress import serve
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

# ... your Flask application routes and SocketIO event handlers here

if __name__ == '__main__':
    try:
        serve(app, host='0.0.0.0', port=5001)
    except Exception as e:
        print(f"Error starting server: {e}")