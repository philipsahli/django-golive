from golive.base import DjangoBaseTask, DebianPackageMixin


class RedisSetup(DjangoBaseTask, DebianPackageMixin):
    role = 'CACHE_HOST'
    # TODO: redis-server should be installed from squeeze-backports
    package_name = 'redis-server'
