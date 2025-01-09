import flask
import sqlite3
import bcrypt

from flask import request, flash, session
from werkzeug.exceptions import abort

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

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
            print(username, password)
    return flask.render_template('login.html')
