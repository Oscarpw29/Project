from flask import Blueprint, render_template, url_for, redirect, flash, session
import gunicorn
import socket
from threading import Thread
from flask_login import current_user, login_required
from flask import request, flash, session
from werkzeug.exceptions import abort

from project.models import User

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/home')
@login_required
def home():
    return render_template('home.html', name=current_user.username)


@main.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        recipient_username = request.form['recipient']
        if recipient_username:
            recipient = User.query.filter_by(username=recipient_username).first()
            if recipient:
                session['recipient'] = recipient_username
                return redirect(url_for('main.chat'))
            else:
                flash('Recipient not found.', 'error')
        else:
            flash('Please enter a username', 'error')
    recipient_name = session.get('recipient')
    return render_template('chat.html', user=current_user.username, recipient=recipient_name)
