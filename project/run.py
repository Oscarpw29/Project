from project import *

if __name__ == '__main__':
    socketio.run(create_app(), debug=True, allow_unsafe_werkzeug=True)