from flask_login import current_user
from flask_socketio import SocketIO, emit, join_room, disconnect
from project import socketio
from flask import Flask, session
from project.models import User

# Assuming 'socketio' is initialized in your __init__.py

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        print(f'Client connected {current_user.username}')
        join_room(current_user.username)
    else:
        print('Unauthorized connection')
        disconnect()


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


# @socketio.on('message')
# def handle_message(data):
#     print('Received message:', data)
#     recipient_username = data['recipient']
#     recipient = User.query.filter_by(username=recipient_username).first()
#     if recipient:
#         print(f'Recipient {recipient_username} received')
#         emit('message', {'data': data['message'], 'sender': current_user.username}, room=recipient)
#     else:
#         print(f'Recipient {recipient_username} not found')

@socketio.on('message')
def handle_message(data):
    recipient_username = data['recipient']

    try:
        recipient = User.query.filter_by(username=recipient_username).first()
        if recipient:
            print(f"Sending message to {recipient_username}")
            emit('message', {'data': data['message'], 'sender': current_user.username}, room=recipient_username)
            emit('message', {'data': data['message'], 'sender': current_user.username}, room=current_user.username)
        else:
            print(f"Recipient '{recipient_username}' not found.")
            emit('error', {'message': 'Recipient not found.'}, room=current_user.username)
    except Exception as e:
        print(f"Error sending message: {e}")
        emit('error', {'message': 'An error occurred while sending the message.'}, room=current_user.username)