from project import create_app, socketio, init_db
import os

app = create_app()

if not os.path.isfile('instance/db.sqlite'):
    init_db.create_db()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5002)