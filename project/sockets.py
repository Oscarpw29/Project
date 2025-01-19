from flask_socketio import SocketIO, emit
from project import socketio


# Assuming 'socketio' is initialized in your __init__.py

@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    recipient = data['recipient']
    emit('message', {'data': data['message'], 'sender': data['sender']}, room=recipient)
