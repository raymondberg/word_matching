from flask import session

from .app import games

def _is_gamemaster():
    return session.get('is_gamemaster', False)

def require_gamemaster(f):
    def require_gamemaster_(*args, **kwargs):
        if _is_gamemaster():
            return f(*args, **kwargs)
        return redirect('/')
    return require_gamemaster_


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


