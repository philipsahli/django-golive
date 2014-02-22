from golive.base import DjangoBaseTask, DebianPackageMixin


class RedisSetup(DjangoBaseTask, DebianPackageMixin):
    # TODO: redis-server should be installed from squeeze-backports
    package_name = 'redis-server'
    roles = 'CACHE_HOST'
