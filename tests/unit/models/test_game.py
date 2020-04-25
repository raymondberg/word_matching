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
    return Game(
        slug="test",
        cardset=cardset,
        usernames=["Player1", "Player2"],
    )


def test_game_throws_error_without_cardset(cardset, response_cards):
    game = Game("test", cardset=cardset)

    pytest.xfail("no way to implement db yet")
    with pytest.raises(ValueError):
        Game(cardset="not_a_real_slug")


def test_game_has_reasonable_defaults(cardset, response_cards):
    game = Game("test", cardset=cardset)

    assert game.state == Game.State.NOT_STARTED
    assert game.cardset == cardset
    assert game.cards_played == []
    assert game.cards_remaining == set(response_cards)
    assert game.players == []
    assert game.player_hands == {}
    assert game.play_pile == {}


def test_chat_emits_chat(fresh_game, socketio_emit):
    fresh_game.emit_chat("Player1", "a message")
    socketio_emit.assert_called_with("chat", "Player1: a message", room=fresh_game.slug)
