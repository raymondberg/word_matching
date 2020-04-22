from flask import redirect, session

from .models import Cardset, Game

def _is_gamemaster():
    return session.get('is_gamemaster', False)


def require_gamemaster(f):
    def require_gamemaster_(*args, **kwargs):
        if _is_gamemaster():
            return f(*args, **kwargs)
        return redirect('/')
    return require_gamemaster_


def require_username_or_except(exception_type):
    def require_username(f):
        def require_username_(*args,**kwargs):
            username = session.get('username')

            if not username:
                if exception_type:
                    raise Exception('Login Required')
                return redirect('/')

            return f(*args, **kwargs, username=username)
        return require_username_
    return require_username

require_username = require_username_or_except(None)


def require_valid_game(f):
    def require_valid_game_(data, *args,**kwargs):
        room_id = data.get('room_id')

        if not room_id or not Game.slug_exists(room_id):
            raise ConnectionRefusedError(f'Room ID {room_id} unknown')
        return f(data, *args, **kwargs, game=Game.from_slug(room_id))

    return require_valid_game_
