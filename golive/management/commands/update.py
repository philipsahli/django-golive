from golive.management import CoreCommand


class Command(CoreCommand):

    pass


    #def _on_role_only(self, f, role):
    #    @roles(role)
    #    def do():
    #        f(self.config)
    #    do()


    #@roles('CACHE_HOST')
    #def _on_cache_host(self):
    #    print "SETUP CACHE"
    #    redis = RedisSetup().install()
#
#    @roles('DB_HOST')
#    def _on_db_host(self):
#        ###### DB only
#        # install, configure db (postgres)
#        db = DbEngineFactory.setup()
#        if db is not None:
#            db.install()
#            db.create()

        # install redis
        #cache = RedisSetup()
        #cache.install()

