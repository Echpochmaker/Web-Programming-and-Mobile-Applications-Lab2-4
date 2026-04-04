from app.core.cache import cache
cache.set('test:key', 'hello world')
print(cache.get('test:key'))