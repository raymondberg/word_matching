from unittest.mock import patch

import pytest

from word_match.models.cardset import Cardset
from word_match.models.game import Game


@pytest.fixture(autouse=True)
def socketio_emit():
    with patch("word_match.models.game.emit") as mock:
        yield mock


@pytest.fixture(scope="module")
def prompt_cards():
    return ["Vorpal", "Slithy", "Mimsy"]


@pytest.fixture(scope="module")
def response_cards():
    return ["Sword", "Troves", "Toves", "Jubjub Bird"]


@pytest.fixture(scope="module")
def cardset(prompt_cards, response_cards):
    return Cardset(
        name="Jabberwocky",
        prompt_cards=prompt_cards,
        response_cards=response_cards,
    )

@pytest.fixture
def fresh_game(cardset):
    game = Game(
        slug="test",
        cardset=cardset,
        usernames=["Player1", "Player2"],
    )
    game.CARD_COUNT = 1
    return game


def test_game_throws_error_without_cardset(cardset, response_cards):
    game = Game("test", cardset=cardset)

    pytest.xfail("no way to implement db yet")
    with pytest.raises(ValueError):
        Game(cardset="not_a_real_slug")


def test_game_has_reasonable_defaults(cardset, response_cards):
    game = Game("test", cardset=cardset)

    assert game.state == Game.State.NOT_STARTED
    assert game.cardset == cardset
    assert game.prompt_cards_played == []
    assert game.response_cards_played == []
    assert game.response_cards_remaining == set(response_cards)
    assert game.players == []
    assert game.player_hands == {}
    assert game.play_pile == {}


def test_chat_emits_chat(fresh_game, socketio_emit):
    fresh_game.chat("Player1", "a message")
    socketio_emit.assert_called_with("chat", "Player1: a message", room=fresh_game.slug)


@pytest.mark.parametrize("game_user", ['game', 'GaMe'])
def test_chat_doesnt_work_for_game(game_user, fresh_game, socketio_emit):
    fresh_game.chat(game_user, "a message")
    socketio_emit.assert_not_called()


def test_game_starts_with_two_players(fresh_game, prompt_cards, socketio_emit):
    fresh_game.add_player("Player1")
    fresh_game.add_player("Player2")

    assert fresh_game.state == Game.State.RESPONDING
    assert fresh_game.chooser == "Player1"
    assert fresh_game.prompt_card in prompt_cards

    event_emitted, data = socketio_emit.call_args_list[-1].args
    assert event_emitted == 'game_state'
    assert data["chooser"] == "Player1"
    assert not data["play_pile"]
    assert not data["players_responded"]
    assert data["players"] == data["users"] == ["Player1", "Player2"]
    assert data["state"] == Game.State.RESPONDING


def test_dealt_cards_removed_from_game(fresh_game, prompt_cards, socketio_emit):
    fresh_game.add_player("Player1")
    fresh_game.deal_cards("Player1")
    fresh_game.add_player("Player2")
    fresh_game.deal_cards("Player2")

    p1_cards = set(fresh_game.player_hand("Player1"))
    assert p1_cards.intersection(fresh_game.response_cards_played)
