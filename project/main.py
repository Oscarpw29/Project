from flask import Blueprint,render_template
import gunicorn
import socket
from threading import Thread
from flask_login import current_user, login_required
from flask import request, flash, session
from werkzeug.exceptions import abort

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/home')
@login_required
def home():
    return render_template('home.html', name=current_user.username)