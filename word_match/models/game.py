from .base import RedisModel
from .cardset import Cardset

import random

from flask_socketio import join_room, leave_room, emit

class Game(RedisModel):
    REDIS_PREFIX = 'games'
    FIELDS = [
        'slug',
        'cardset_slug',
        'chooser',
        'play_pile',
        'player_hands',
        'players',
        'prompt_card',
        'prompt_cards_played',
        'response_cards_played',
        'state',
        'usernames',
    ]
    CARD_COUNT = 5

    class State:
        NOT_STARTED = 'not_started'
        RESPONDING = 'responding'
        REVIEWING = 'reviewing'

    def __init__(self,
                 slug,
                 cardset=None,
                 cardset_slug=None,
                 chooser=None,
                 play_pile=None,
                 player_hands=None,
                 players=None,
                 prompt_card=None,
                 prompt_cards_played=None,
                 response_cards_played=None,
                 state=None,
                 usernames=None,
    ):
        self.slug = slug

        self.chooser = chooser
        self.play_pile = play_pile or {}
        self.player_hands = player_hands or {}
        self.players = players or []
        self.prompt_card = prompt_card or None
        self.prompt_cards_played = prompt_cards_played or []
        self.response_cards_played = response_cards_played or []
        self.state = state or self.__class__.State.NOT_STARTED
        self.usernames = usernames or []

        if cardset_slug:
            self.cardset = Cardset.from_slug(cardset_slug)
        else:
            self.cardset = cardset
        if not self.cardset:
            raise ValueError("Missing cardset")
        self.prompt_cards_remaining = set(self.cardset.prompt_cards) - set(self.prompt_cards_played)
        self.response_cards_remaining = set(self.cardset.response_cards) - set(self.response_cards_played)

    @property
    def cardset_slug(self):
        return self.cardset.slug

    def deal_cards(self, player):
        ## Deal random cards from the deck
        if player not in self.player_hands:
            print("setting up player hand")
            self.player_hands[player] = []

        cards_dealt = set(
            random.sample(
                self.response_cards_remaining,
                self.CARD_COUNT - len(self.player_hands[player])
            )
        )

        if cards_dealt:
            print("dealt cards")
            self.response_cards_remaining = self.response_cards_remaining - cards_dealt
            self.player_hands[player].extend(cards_dealt)

    def play_card(self, player, card):
        if player in self.play_pile:
            print("you've already played")
            return
        if player == self.chooser:
            print("choosers can't play")
            return
        elif card not in self.player_hands.get(player, []):
            print("no such card")
            return

        print(f"{player} has {self.player_hands[player]}")
        self.player_hands[player].remove(card)
        print(f"{player} has {self.player_hands[player]}")
        self.play_pile[player] = card
        self.deal_cards(player)
        self.save()
        self.emit_state()
        self.send_deck()

    def add_player(self, player):
        if player not in self.players:
            self.players.append(player)
            self.deal_cards(player)
            self.start_if_ready()
            self.save()
            self.emit_state()

    def start_if_ready(self):
        if len(self.players) > 1 and self.state == Game.State.NOT_STARTED:
            self.start_responding(self.players[0])
        elif self.state == Game.State.RESPONDING and (self.chooser is None or self.prompt_card is None):
            self.start_responding(self.players[0])

    def enter_review_and_save(self, player):
        if self.chooser != player:
            print("not the chooser")
            return
        elif self.state != Game.State.RESPONDING or len(self.play_pile) < 1:
            print(f"Not ready ({self.state}) for flip {len(self.play_pile)}")
            return
        self.state = Game.State.REVIEWING
        self.save()
        self.emit(f"{self.chooser} has started reviewing")
        self.emit_state()

    def choose_card(self, player, card):
        if self.chooser != player:
            print("not the chooser")
            return
        elif card not in self.play_pile.values():
            print("no such card")

        winning_player = next(p for p,c in self.play_pile.items() if c == card)
        self.play_pile = {}
        self.start_responding(winning_player)
        self.save()
        self.emit(f"{self.chooser} has won best card! It's their turn to choose")
        self.emit_state()

    def start_responding(self, choosing_player):
        self.chooser = choosing_player
        self.state = Game.State.RESPONDING
        self.prompt_card = random.sample(self.prompt_cards_remaining, 1)[0]
        self.prompt_cards_played.append(self.prompt_card)
        self.emit(f"{self.chooser} is ready for your cards!")

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
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

    def send_deck(self, username):
        return emit('send_deck', self.player_hands.get(username, {}))

    def emit(self, *args, **kwargs):
        print(f'emitting: {args} {kwargs} room={self.slug}')
        emit(*args, **kwargs, room=self.slug)

    def emit_refresh(self):
        self.emit("reload")

    def chat(self, username, message):
        if message and username.upper() != "GAME":
            self.emit('chat', f'{username}: {message}')

    def emit_state(self):
        self.emit('game_state', self._state_details())

    def reset(self, username):
        self.chooser = None
        self.play_pile = {}
        self.players = []
        self.player_hands = {}
        self.state = None
        self.usernames = []
        self.response_cards_played = []
        self.response_cards_remaining = []
        self.save()
        self.emit(f"{username} has reset the game")
        self.emit_refresh()

    def _state_details(self):
        if self.state == Game.State.REVIEWING:
            play_pile = [c for c in self.play_pile.values()]
        else:
            play_pile = [None for c in self.play_pile.values()]
        return {
            'chooser': self.chooser,
            'play_pile': play_pile,
            'players': self.players,
            'prompt_card': self.prompt_card,
            'state': self.state,
            'users': self.usernames,
        }
