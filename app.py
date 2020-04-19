import os
import re
import string
import random

from flask import (
    Flask,
    redirect,
    request,
    render_template,
    session
)

from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['GAMEMASTER_CODE'] = os.environ['GAMEMASTER_CODE']
socketio = SocketIO(app)

games = {}

def alphanumeric_only(value):
    return re.sub(r'[^A-Za-z0-9_ -]', '', value)

def random_string(length=5):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for x in range(length))

class Game:
    def __init__(self, slug):
        self.slug = slug

    def to_session(self):
        return {}

@app.route('/')
def home():
    return render_template('home.html', games=games)


@app.route('/login', methods=['GET','POST'])
def login():
    if request.form.get('username'):
        username = alphanumeric_only(request.form.get('username')).strip()
        if username:
            print(f'{username} is logging in')
            session['username'] = username
    else:
        session.pop('username', None)

    if request.form.get('game_code'):
        code = alphanumeric_only(request.form.get('game_code'))
        if code == app.config['GAMEMASTER_CODE']:
            print(f'User is gamemaster')
            session['is_gamemaster'] = True
        elif session.get('is_gamemaster'):
            session.pop('is_gamemaster', None)
    else:
        session.pop('is_gamemaster', None)

    return redirect('/')


@app.route('/games/create', methods=['POST'])
def create_game():
    while True:
        slug = random_string()
        if slug in games:
            continue
        print(f"Saving game {slug}")
        games[slug] = Game(slug=slug)
        print(games)
        return redirect('/')

@app.route('/games/<string:game_slug>')
def play(game_slug):
    if not session.get('username'):
        return redirect('/')

    safe_slug = alphanumeric_only(game_slug)
    if safe_slug not in games:
        return redirect('/')

    return render_template('play.html', game=games[safe_slug])

## SOCKET IO STUFF ##

def require_username(f):
    def require_username_(*args,**kwargs):
        username = session.get('username')

        if not username:
            raise ConnectionRefusedError('unauthorized!')

        return f(*args, **kwargs, username=username)
    return require_username_

def require_valid_game(f):
    def require_valid_game_(data, *args,**kwargs):
        room_id = data.get('room_id')

        if not room_id or room_id not in games:
            raise ConnectionRefusedError('unauthorized!')
        return f(data, *args, **kwargs, game=games[room_id])

    return require_valid_game_

@socketio.on('join')
@require_username
@require_valid_game
def handle_my_custom_event(data, username, game):
    print(f'received join from: {username} for {game.slug}')
    join_room(game.slug)
    emit("chat", username + ' has joined the room.', room=game.slug)

@socketio.on('leave')
@require_username
@require_valid_game
def handle_my_custom_event(data):
    leave_room(room_id)
    emit("chat", username + ' has left the room.', room=game.slug)

@socketio.on('join')
@require_username
@require_valid_game
def handle_my_custom_event(data, username, game):
    print(f'received join from: {username} for {game.slug}')
    join_room(game.slug)
    emit("chat", username + ' has joined the room.', room=game.slug)

@socketio.on('send_chat')
@require_username
@require_valid_game
def handle_my_custom_event(data, username, game):
    print(f'received message from: {username} in {game.slug}: {data}')
    message = data.get('message')
    if message:
        emit('chat', f'{username}: {message}', room=game.slug)

if __name__ == '__main__':
    socketio.run(app)
