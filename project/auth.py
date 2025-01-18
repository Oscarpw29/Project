from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
import bcrypt

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('login.html')


@auth.route('/login', methods=['GET', 'POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(username=username).first()

    if not username or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
        flash('Invalid username or password.')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)

    return redirect(url_for('main.home'))


@auth.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('register.html')


@auth.route('/register', methods=['GET', 'POST'])
def register_post():
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']

    dupe_email = User.query.filter_by(email=email).first()
    user = User.query.filter_by(username=username).first()

    if user or dupe_email:
        flash('Email/Username already registered.')
        return redirect(url_for('auth.register'))

    if not email or not username or not password:
        flash('Please enter your email, username and password.')
        return redirect(url_for('auth.register'))
    new_user = User(email=email, username=username, password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()))

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
