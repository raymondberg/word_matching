import json

from ..app import app

STORE = app.config['SESSION_REDIS']

class RedisModel:
    @classmethod
    def all_slugs(cls):
        return [s.decode('utf-8').replace(f'{cls.REDIS_PREFIX}_', '') for s in STORE.scan_iter(f'{cls.REDIS_PREFIX}_*')]

    @classmethod
    def from_slug(cls, slug):
        raw = STORE.get(cls.real_slug(slug))
        if not raw:
            return
        return cls(**json.loads(raw))

    @classmethod
    def slug_exists(cls, slug):
        return STORE.exists(cls.real_slug(slug))

    @classmethod
    def real_slug(cls, slug):
        return f'{cls.REDIS_PREFIX}_{slug}'

    @classmethod
    def store(cls, obj):
        STORE.set(
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



