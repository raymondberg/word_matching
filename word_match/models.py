import json
from flask_socketio import join_room, leave_room, emit
from .app import app

redis = app.config['SESSION_REDIS']

class RedisModel:
    @classmethod
    def all_slugs(cls):
        return [s.decode('utf-8').replace(f'{cls.REDIS_PREFIX}_', '') for s in redis.scan_iter(f'{cls.REDIS_PREFIX}_*')]

    @classmethod
    def from_slug(cls, slug):
        raw = redis.get(cls.real_slug(slug))
        if not raw:
            return
        return cls(**json.loads(raw))

    @classmethod
    def slug_exists(cls, slug):
        return redis.exists(cls.real_slug(slug))

    @classmethod
    def real_slug(cls, slug):
        return f'{cls.REDIS_PREFIX}_{slug}'

    @classmethod
    def store(cls, obj):
        redis.set(
            cls.real_slug(obj._storage_slug),
            json.dumps(dict(obj)),
        )

    def save(self):
        print(f'Storing {self._storage_slug}')
        self.__class__.store(self)

    @property
    def _storage_slug(self):
        return self.slug

    def keys(self):
        return self.FIELDS

    def __getitem__(self, key):
        if key in self.keys():
            return getattr(self, key)

class Cardset(RedisModel):
    REDIS_PREFIX = 'cardsets'
    FIELDS = ['name', 'prompt_cards', 'response_cards']

    def __init__(self, name, prompt_cards, response_cards):
        self.name = name
        self.prompt_cards = [c for c in prompt_cards if 'PICK ' not in c]
        self.response_cards = response_cards

    @property
    def slug(self):
        return self.name


class Game(RedisModel):
    REDIS_PREFIX = 'games'
    FIELDS = ['slug', 'state', 'cardset_slug', 'usernames', 'players']

    class State:
        NOT_STARTED = 'not_started'
        WAIT_FOR_ROUND = 'wait_for_round'
        RESPONDING = 'responding'
        REVIEWING = 'reviewing'

    def __init__(self, slug, cardset=None, cardset_slug=None, usernames=None, players=None, state=None):
        self.slug = slug
        self.state = state or self.__class__.State.NOT_STARTED

        if cardset_slug:
            self.cardset = Cardset.from_slug(cardset_slug)
        else:
            self.cardset = cardset

        if not self.cardset:
            raise ValueError("Missing cardset")

        self.usernames = usernames or []
        self.players = players or []

    @property
    def cardset_slug(self):
        return self.cardset.slug

    def add_player(self, username):
        if username not in self.players:
            self.players.append(username)
            self.save()
            self.emit_state()

    def remove_player(self, username):
        if username in self.players:
            self.players.remove(username)
            self.save()
            self.emit_state()

    def add_user(self, username):
        join_room(self.slug)
        if username not in self.usernames:
            self.usernames.append(username)
            self.save()
            self.emit('chat', username + ' has joined the room.')
        self.emit_state()

    def remove_user(self, username):
        leave_room(self.slug)
        if username in self.usernames:
            self.usernames.remove(username)
            self.emit('chat', username + ' has left the room.')
        self.emit_state()

    def emit(self, *args, **kwargs):
        print(f'emitting: {args} {kwargs} room={self.slug}')
        emit(*args, **kwargs, room=self.slug)

    def emit_chat(self, username, message):
        if message:
            self.emit('chat', f'{username}: {message}')

    def emit_state(self):
        self.emit('game_state', self._state_details())

    def _state_details(self):
        return {'state': self.state, 'users': self.usernames, 'players': self.players}
