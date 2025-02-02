from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from project import db, socketio
from project.models import User, Message

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('index.html')

@main.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)

@main.route('/chat/<recipient_username>', methods=['GET', 'POST'])
@login_required
def chat(recipient_username):
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        flash('Recipient not found.', 'error')
        return redirect(url_for('main.home'))
    message = request.form.get('message')
    if request.method == 'POST':
        message = request.form.get('message')
        print('Received message:', message)
        if message:
            new_message = Message(sender=current_user, recipient=recipient, message=message)
            db.session.add(new_message)
            db.session.commit()  # Commit the changes to the database

            print('saving ',new_message)

            socketio.emit('message', {'message': message, 'sender': current_user.username},
                         room=recipient_username)
            return '', 200  # Return an empty response with 200 OK status

    messages = Message.query.filter(
        (Message.sender == current_user) & (Message.recipient == recipient) |
        (Message.recipient == current_user) & (Message.sender == recipient)
    ).order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', user=current_user, recipient=recipient, messages=messages)