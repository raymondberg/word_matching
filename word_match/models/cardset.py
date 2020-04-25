from ..utils import random_string
from .base import RedisModel

class Cardset(RedisModel):
    REDIS_PREFIX = 'cardsets'
    FIELDS = ['name', 'prompt_cards', 'response_cards']

    def __init__(self, name, prompt_cards, response_cards):
        self.name = name or random_string(4)
        self.prompt_cards = [c for c in prompt_cards if 'PICK ' not in c]
        self.response_cards = response_cards

    @property
    def slug(self):
        return self.name
