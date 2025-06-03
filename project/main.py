import json

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from project import db, socketio
from project.models import User, Message, Chat
from . import encryption_util

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('index.html')


@main.route('/home')
@login_required
def home():
    # Query recent chats when rendered
    chats = Chat.query.filter((Chat.user1 == current_user) | (Chat.user2 == current_user)).all()

    recent_chat_message = []

    for chat in chats:
        last_message = Message.query.filter_by(chat=chat).order_by(desc(Message.timestamp)).first()
        recipient = chat.user2 if chat.user2 == current_user else chat.user1

        recent_chat_message.append({
            'chat': chat,
            'last_message': last_message,
            'recipient': recipient
        })

    for chat_info in recent_chat_message:
        if chat_info['last_message']:
            decrypted_content = encryption_util.decrypt_message(chat_info['last_message'].message)
            chat_info['last_message'].message = decrypted_content

    return render_template('home.html', user=current_user, recent_chat_message=recent_chat_message)


@main.route('/new_chat', methods=['POST'])
@login_required
def new_chat():
    data = request.get_json()
    recipient_username = data.get('recipient_username')

    if not recipient_username:
        return jsonify({'error': 'You must provide a username!'}), 400

    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        return jsonify({'error': 'No such user!'}), 404

    existing_chat = Chat.query.filter(
        (Chat.user1 == current_user) & (Chat.user2 == recipient) |
        (Chat.user1 == recipient) & (Chat.user2 == current_user)
    ).first()

    if existing_chat:
        return jsonify({'redirect_url': url_for('main.chat', chat_id=existing_chat.id)})

    # Creating a new chat
    new_chat = Chat(user1=current_user, user2=recipient, chat_type="secret")
    db.session.add(new_chat)
    db.session.commit()

    return jsonify({'redirect_url': url_for('main.chat', chat_id=new_chat.id)})


@main.route('/api/e2e_keys/upload', methods=['POST'])
@login_required
def upload_e2e_public_key():
    data = request.get_json()
    public_e2e_key = data.get('public_e2e_key')

    if not public_e2e_key:
        print('--- failed ---')
        return jsonify({'error': 'You must provide a public key!'}), 400

    if current_user.public_e2e_key is None:
        current_user.public_e2e_key = public_e2e_key
        db.session.commit()
        return jsonify({'success': True, 'message': 'Public key uploaded'}), 200
    else:
        current_user.public_e2e_key = public_e2e_key
        db.session.commit()
        return jsonify({'success': True, 'message': 'Public key updated'}), 200


@main.route('/api/e2e_keys/<int:user_id>', methods=['GET'])
@login_required
def get_e2e_public_key(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'No such user!'}), 404
    if not user.public_e2e_key:
        return jsonify({'error': 'No public key found!'}), 404

    return jsonify({
        'user_id': user.id,
        'user_name': user.username,
        'public_e2e_key': user.public_e2e_key,
    }), 200


@main.route('/chat/<int:chat_id>', methods=["GET", "POST"])
@login_required
def chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    recipient = None
    if chat.user1 == current_user:
        recipient = chat.user2
    elif chat.user2 == current_user:
        recipient = chat.user1
    else:
        flash('You don\'t have permission to do that!', 'danger')
        return redirect(url_for('main.home', chat_id=chat_id))

    print(f'--- Chat Route for chat_id: {chat_id}, Type: {chat.chat_type}---')

    if request.method == 'POST':
        message_from_client = request.form.get('message')
        if message_from_client:
            message_to_store = None
            emit_message_content = None

            if chat.chat_type == 'secret':
                try:
                    parsed_client_message_dict = json.loads(message_from_client)
                    if "ciphertext" in parsed_client_message_dict and "nonce" in parsed_client_message_dict:
                        message_to_store = json.dumps(parsed_client_message_dict)
                        emit_message_content = parsed_client_message_dict
                    else:
                        print("Warning: Secret chat POST message was JSON but missing ciphertext or nonce!")
                        message_to_store = message_from_client
                        emit_message_content = message_from_client
                except json.JSONDecodeError:
                    print("Warning: Secret chat POST message was JSON but malformed!")
                    message_to_store = message_from_client
                    emit_message_content = message_from_client
            elif chat.chat_type == 'standard':
                message_to_store = encryption_util.encrypt_message(message_from_client)
                if message_to_store is None:
                    print(f'Error: Service-side encryption failed for standard chat {chat_id}')
                    message_to_store = '[Encryption Failed]'

                emit_message_content = message_from_client
            else:
                print(f'Warning: Unknown chat type: {chat.chat_type}')
                message_to_store = message_from_client
                emit_message_content = message_from_client

            if message_to_store is None:
                print("Error: Message content to store is none")
                return jsonify({'error': 'You must provide a message to store!'}), 400

            new_message = Message(
                sender=current_user,
                recipient=recipient,
                chat=chat,
                message=message_to_store,
            )
            db.session.add(new_message)
            db.session.commit()

            socketio.emit('message', {
                'message': emit_message_content,
                'sender': current_user.username,
                'sender_id': current_user.id,
                'chat_id': chat.id,
                'chat_type': 'secret'
            }, room=f'chat_{chat.id}')
            return '', 200
    messages_response = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.asc()).all()

    display_messages = []
    for msg in messages_response:
        display_content = msg.message
        if chat.chat_type == 'standard':
            print("Chat type is standard, attempting server-side decryption")
            try:
                display_content = encryption_util.decrypt_message(msg.message)
            except Exception as e:
                print(f'Server-side decryption failed for chat {chat_id}, error: {e}')
                display_content = "[Server Decryption Failed]"
        elif chat.chat_type == 'secret':
            display_content = msg.message
        else:
            print("Warning: Unknown chat type!")

        display_messages.append({
            'id': msg.id,
            'sender': msg.sender,
            'recipient': msg.recipient,
            'message': display_content,
            'timestamp': msg.timestamp,
            'chat_type': chat.chat_type,
            'chat_id': msg.chat_id,
        })

    return render_template('chat.html',
                           user=current_user,
                           recipient=recipient,
                           messages=display_messages,
                           chat_id=chat_id,
                           chat_type=chat.chat_type,
                           recipient_id=recipient.id,
                           )


@main.route('/chat_messages/<int:chat_id>', methods=["GET", "POST"])
@login_required
def chat_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user1 == current_user or chat.user2 == current_user:
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.asc()).all()
        return render_template('_chat_messages.html', messages, current_user=current_user)
    else:
        return "Unauthorized", 403


@main.route('/search_users')
@login_required
def search_users():
    query = request.args.get('q')
    if query:
        search_term = f'%{query}%'
        users = User.query.filter(User.username.ilike(search_term)).filter(User.id != current_user.id).all()
        results = [{'username': user.username, 'id': user.id} for user in users]
        return jsonify({'results': results})
    return jsonify({'results': []})
