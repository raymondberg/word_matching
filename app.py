import json
import os
import re
import random
import string

from flask import (
    Flask,
    redirect,
    request,
    render_template,
    session
)

from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['GAMEMASTER_CODE'] = os.environ['GAMEMASTER_CODE']
socketio = SocketIO(app)

games = {}
cardsets = {}
unambiguous_characters = [
  c for c in string.ascii_uppercase + string.digits if c not in 'B8G6I1l0OQDS5Z2'
]

def alphanumeric_only(value):
    return re.sub(r'[^A-Za-z0-9_ -]', '', value)

def is_gamemaster():
    return session.get('is_gamemaster', False)

def random_string(length=5):
    return ''.join(random.choice(unambiguous_characters) for x in range(length))

def slug_for_resource(resource):
    while True:
        slug = random_string()
        if slug not in resource:
            return slug

def require_gamemaster(f):
    def require_gamemaster_(*args, **kwargs):
        if is_gamemaster():
            return f(*args, **kwargs)
        return redirect('/')
    return require_gamemaster_

class Cardset:
    def __init__(self, slug, name, prompt_cards, response_cards):
        self.slug = slug
        self.name = name
        self.prompt_cards = [c for c in prompt_cards if "PICK " not in c]
        self.response_cards = response_cards

class Game:
    def __init__(self, slug, cardset):
        self.slug = slug
        self.cardset = cardset
        self.users = set()

    def add_user(self, username):
        join_room(self.slug)
        if username not in self.users:
            self.users.add(username)
            self.emit("chat", username + ' has joined the room.')
        self.emit_roster()

    def remove_user(self, username):
        leave_room(self.slug)
        if username in self.users:
            self.users.pop(username)
            self.emit("chat", username + ' has left the room.')
        self.emit_roster()

    def emit(self, *args, **kwargs):
        print(f"emitting: {args} {kwargs} room={self.slug}")
        emit(*args, **kwargs, room=self.slug)

    def emit_chat(self, username, message):
        if message:
            self.emit('chat', f'{username}: {message}')

    def emit_roster(self):
        self.emit("roster", list(self.users))


@app.route('/')
def home():
    return render_template('home.html', cardsets=cardsets, games=games)


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

@require_gamemaster
@app.route('/cardsets/create', methods=['POST'])
def cardsets_create():
    upload = request.files.get('cardset-file')
    if upload and upload.filename and upload.filename.endswith('.json'):
        cardset_data = json.load(upload)
        if cardset_data.get('response_cards') and cardset_data.get('prompt_cards'):
            slug = slug_for_resource(cardsets)
            print(f"Saving cardset {slug}")
            cardsets[slug] = Cardset(
                slug,
                name=request.form.get('name') or random_string(4),
                prompt_cards=cardset_data['prompt_cards'],
                response_cards=cardset_data['response_cards']
            )
    return redirect('/')

@require_gamemaster
@app.route('/games/create', methods=['POST'])
def create_game():
    slug = slug_for_resource(games)
    cardset = cardsets.get(request.form.get('cardset'))
    if cardset:
        print(f"Saving game {slug} for cardset {cardset.name}")
        games[slug] = Game(slug=slug, cardset=cardset)
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
def handle_join(data, username, game):
    print(f'received join from: {username} for {game.slug}')
    game.add_user(username)

@socketio.on('leave')
@require_username
@require_valid_game
def handle_leave(data, username, game):
    print(f'received leave from: {username} for {game.slug}')
    game.remove_user(username)

@socketio.on('send_chat')
@require_username
@require_valid_game
def handle_send_chat(data, username, game):
    print(f'received message from: {username} in {game.slug}: {data}')
    game.emit_chat(username, data.get('message'))

if __name__ == '__main__':
    socketio.run(app)
