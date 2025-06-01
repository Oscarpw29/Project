from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from project import db, socketio
from project.models import User, Message, Chat

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('index.html')


@main.route('/home')
@login_required
def home():
    recent_chats = get_recent_chats(current_user)
    active_chat = current_user.last_chat_open if current_user.last_chat_open else None
    recipient_for_active_chat = None
    if active_chat:
        recipient_for_active_chat = active_chat.user2 if active_chat.user1 == current_user else active_chat.user1
    return render_template('home.html', active_chat=active_chat, recent_chats=recent_chats, current_user=current_user,
                           recipient_for_active_chat=recipient_for_active_chat)


def get_recent_chats(user):

    chats = Chat.query.filter((Chat.user1 == user) | (Chat.user2 == user)).all()

    recent_chat_message = []

    for chat in chats:
        last_message = Message.query.filter_by(chat=chat).order_by(desc(Message.timestamp)).first()
        recipient = chat.user2 if chat.user2 == user else chat.user1
        recent_chat_message.append({
            'chat': chat,
            'last_message': last_message,
            'recipient': recipient
        })

    recent_chat_message.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else x['chat'].timestamp,
                             reverse=True)

    return recent_chat_message


@main.route('/update_last_chat', methods=['POST'])
@login_required
def update_last_chat():
    data = request.get_json()
    chat_id = data.get('chat_id')
    if chat_id:
        chat = Chat.query.get(chat_id)
        if chat and (chat.user1 == current_user or chat.user2 == current_user):
            current_user.last_chat_open_id = chat_id
            db.session.commit()
            return jsonify({'success': True}), 200
        return jsonify({'error': 'Chat not found'}), 400
    return jsonify({'error': 'missing chat_id'}), 400


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
    new_chat = Chat(user1=current_user, user2=recipient)
    db.session.add(new_chat)
    db.session.commit()

    return jsonify({'redirect_url': url_for('main.chat', chat_id=new_chat.id)})


@main.route('/chat_messages/<int:chat_id>')
@login_required
def get_chat_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    messages = Message.query.filter_by(chat=chat).order_by(Message.timestamp).all()
    return render_template('_chat_messages.html', messages=messages) # Render a partial template


@main.route('/search_users')
@login_required
def search_users():
    query = request.args.get('q')
    if query:
        users = User.query.filter(User.username.like(f'%{query}%')).all()
        results = [{'username': user.username, 'id': user.id} for user in users]
        return jsonify(results)
    return jsonify([])
