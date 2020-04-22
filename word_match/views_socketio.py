from flask import session

from .app import socketio
from .decorators import require_username_or_except, require_valid_game

@socketio.on('join')
@require_username_or_except(ConnectionRefusedError)
@require_valid_game
def handle_join(data, username, game):
    print(f'received join from: {username} for {game.slug}')
    game.add_user(username)


@socketio.on('leave')
@require_username_or_except(ConnectionRefusedError)
@require_valid_game
def handle_leave(data, username, game):
    print(f'received leave from: {username} for {game.slug}')
    game.remove_user(username)

@socketio.on('deck_up')
@require_username_or_except(ConnectionRefusedError)
@require_valid_game
def handle_join(data, username, game):
    print(f'received deck_up from: {username} for {game.slug}')
    game.add_player(username)

@socketio.on('deck_down')
@require_username_or_except(ConnectionRefusedError)
@require_valid_game
def handle_join(data, username, game):
    print(f'received deck_down from: {username} for {game.slug}')
    game.remove_player(username)

@socketio.on('send_chat')
@require_username_or_except(ConnectionRefusedError)
@require_valid_game
def handle_send_chat(data, username, game):
    print(f'received message from: {username} in {game.slug}: {data}')
    game.emit_chat(username, data.get('message'))

all_loaded = True
