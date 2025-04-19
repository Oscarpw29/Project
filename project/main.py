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

    recent_chat_message.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else x['chat'].timestamp,
                             reverse=True)

    return render_template('home.html', user=current_user, receent_chat_message=recent_chat_message)


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

    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            new_message = Message(sender=current_user, recipient=recipient, chat=chat, message=message)
            db.session.add(new_message)
            db.session.commit()
            socketio.emit('message', {'message': message, 'sender': current_user.username, 'chat_id': chat_id},
                          room=f'chat_{chat_id}')

            return '', 200
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', user=current_user, recipient=recipient, messages=messages, chat_id=chat_id)


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
