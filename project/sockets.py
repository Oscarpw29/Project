from flask_socketio import join_room, emit
from flask_login import current_user
from . import socketio, db
from .models import Message, Chat
from flask import current_app, request


# Assuming 'socketio' is initialized in your __init__.py

@socketio.on('connect')
def handle_connect():
    print(f'Client connected with {request.sid}')
    emit('my_response', {'data': 'Connected'})
    print("handle_connect function is being executed!")


@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    print(f'{current_user.username} joined room {room}')


@socketio.on('client_ready')
def handle_client_ready(data):
    room = data['room']
    print(f'Client in room {room} is ready to receive messages.')


@socketio.on('message')
def handle_message(data):
    message = data['message']
    room = data['room']
    chat_id = int(room.split('_')[1])

    chat = Chat.query.get_or_404(chat_id)
    recipient = None
    if chat.user1 == current_user:
        recipient = chat.user2
    elif chat.user2 == current_user:
        recipient = chat.user1

    if recipient:
        new_message = Message(sender=current_user, recipient=recipient, message=message, chat=chat)
        db.session.add(new_message)
        db.session.commit()

        emit('message', {'message': message, 'sender': current_user.username, 'chat_id': chat_id}, room=room)
        print(f'Emitted message to room {room}: {message}')
