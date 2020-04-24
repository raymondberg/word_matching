from flask import session

from .decorators import in_game_action

@in_game_action('join')
def handle_join(data, username, game):
    print(f'received join from: {username} for {game.slug}')
    game.add_user(username)
    game.send_deck(username)


@in_game_action('leave')
def handle_leave(data, username, game):
    print(f'received leave from: {username} for {game.slug}')
    game.remove_user(username)
    game.send_deck(username)

@in_game_action('deck_up')
def handle_deck_up(data, username, game):
    print(f'received deck_up from: {username} for {game.slug}')
    game.add_player(username)
    game.send_deck(username)

@in_game_action('deck_down')
def handle_deck_down(data, username, game):
    print(f'received deck_down from: {username} for {game.slug}')
    game.remove_player(username)
    game.send_deck(username)

@in_game_action('chat')
def handle_send_chat(data, username, game):
    print(f'received message from: {username} in {game.slug}: {data}')
    game.emit_chat(username, data.get('message'))

@in_game_action('play_card')
def handle_play_card(data, username, game):
    print(f'received card from: {username} in {game.slug}: {data.get("card")}')
    game.play_card(username, data.get('card'))

@in_game_action('review_cards')
def handle_review_cards(data, username, game):
    print(f'received review_cards from: {username} in {game.slug}')
    game.enter_review_and_save(username)

@in_game_action('choose_card')
def handle_review_cards(data, username, game):
    print(f'received choose_cards from: {username} in {game.slug}: {data.get("card")}')
    game.choose_card(username, data.get("card"))

@in_game_action('reset')
def handle_review_cards(data, username, game):
    print(f'received choose_cards from: {username} in {game.slug}: {data.get("card")}')
    game.reset(username)

all_loaded = True
