import flask
import sqlite3
import bcrypt
import gunicorn
import socket
from threading import Thread

from flask import request, flash, session
from werkzeug.exceptions import abort

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

test_pass = 'pass'
test_user = 'test'

def clear_flashes():
    session.pop('flashes', None)


@app.route('/')
def index():
    clear_flashes()
    return flask.render_template('index.html')


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title:
            flash('Title is required.')
        else:
            hashed = bcrypt.hashpw(title.encode('utf-8'), bcrypt.gensalt())
            print(hashed)
    return flask.render_template('create.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Username and password are required.')
        else:
            if username == 'test' and password == 'pass':
                print('Login successful')
                return (home(),flask.url_for('home'))
            else:
                flash('Invalid username or password.')
    return flask.render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        if not email or not username or not password:
            flash('Email and username and password are required.')
        else:
            print(email, username, password)
    return flask.render_template('register.html')

@app.route('/home')
def home():
    try:
        return flask.render_template('home.html', variable=username, title='Home')
    except Exception as e:
        return flask.render_template('login.html', variable=username, title='Login')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
