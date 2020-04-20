import random
import re
import string


unambiguous_characters = [
  c for c in string.ascii_uppercase + string.digits if c not in 'B8G6I1l0OQDS5Z2'
]


def alphanumeric_only(value):
    return re.sub(r'[^A-Za-z0-9_ -]', '', value)


def random_string(length=5):
    return ''.join(random.choice(unambiguous_characters) for x in range(length))


def slug_for_resource(resource):
    while True:
        slug = random_string()
        if not resource.slug_exists(slug):
            return slug
