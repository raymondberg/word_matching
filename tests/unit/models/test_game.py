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
    assert game.cards_played == []
    assert game.cards_remaining == set(response_cards)
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
    socketio_emit.assert_called_with({})
