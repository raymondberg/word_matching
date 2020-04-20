from flask_socketio import join_room, leave_room, emit

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
