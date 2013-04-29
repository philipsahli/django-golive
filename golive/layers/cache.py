from golive.base import DjangoBaseTask, DebianPackageMixin

class RedisSetup(DjangoBaseTask, DebianPackageMixin):
    role = 'CACHE_HOST'
    package_name = 'redis-server'
