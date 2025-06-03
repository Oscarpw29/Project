import json
from flask_socketio import join_room, emit
from flask_login import current_user
from . import socketio, db
from .models import Message, Chat
from flask import current_app, request
from . import encryption_util
import time


# Assuming 'socketio' is initialized in your __init__.py

@socketio.on('connect')
def handle_connect():
    print(f'Client connected with {request.sid}')
    emit('my_response', {'data': 'Connected'})


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
    chat_type = data.get('chat_type', 'standard')
    sender_id = data.get('sender_id')

    chat = Chat.query.get_or_404(chat_id)
    recipient = None
    if chat.user1 == current_user:
        recipient = chat.user2
    elif chat.user2 == current_user:
        recipient = chat.user1
    else:
        print(f"Error: Sender ID {sender_id} not found in chat {chat_id}")
        return

    message_for_store = None

    if chat_type == 'secret':
        if isinstance(message, dict):
            try:
                message_for_store = json.dumps(message)
            except TypeError as e:
                print(f'Error: Failed to return JSON.dumps secret message dict for DB: {e}')
                return

        else:
            print(f'Error: Secret-chat message was not a dict')
            message_for_store = message
    elif chat_type == 'standard':
        message_for_store = encryption_util.encrypt_message(message)
        if message_for_store is None:
            print(f'Error: Failed to encrypt message for DB: {message}')
            return
    if message_for_store is None:
        print("Message content to store is None after processing")
        return

    new_message = Message(sender_id=sender_id, recipient_id=recipient.id, chat=chat, message=message_for_store)
    db.session.add(new_message)
    db.session.commit()

    emit_msg_content = message_for_store

    emit('message', {
        'message': emit_msg_content,
        'sender': current_user.username,
        'sender_id': current_user.id,
        'chat_id': chat_id,
        'chat_type': chat_type
    }, room=room)

    # emit('message',{
    #     'message': 'TEST_MESSAGE_RECEIVED',
    #     'sender': 'serverTest',
    #     'sender_id': 0,
    #     'chat_id': data['chat_id'],
    #     'chat_type': data['chat_type']
    # }, room=data['room'])
