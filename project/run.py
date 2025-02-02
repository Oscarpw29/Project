from project import create_app
from flask_socketio import SocketIO

# Create the Flask app instance
app = create_app()

# Initialize Flask-SocketIO with the app instance
socketio = SocketIO(app)

# Run the app with SocketIO
if __name__ == '__main__':
    socketio.run(app, debug=True)
