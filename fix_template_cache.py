from fastapi.templating import Jinja2Templates
import sys

# Создаём заглушку для кэша
class NoCache:
    def get(self, key):
        return None
    def set(self, key, value):
        pass
    def __getitem__(self, key):
        return None
    def __setitem__(self, key, value):
        pass

# Патчим Jinja2Templates
original_init = Jinja2Templates.__init__
def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    self.env.cache = NoCache()

Jinja2Templates.__init__ = patched_init

print("Cache disabled via monkey patch")