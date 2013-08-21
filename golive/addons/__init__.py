from golive.utils import debug

SLOT_AFTER = "AFTER"
SLOT_BEFORE = "BEFORE"


class Registry(object):
    registered = list()
    activated = list()

    def register(self, cls):
        debug("REGISTRY: register addon %s (%s)" % (cls.NAME, cls))
        self.registered.append(cls)

    def activate(self, name):
        for item in self.registered:
            if item.NAME == name:
                if item not in self.activated:
                    self.activated.append(item)
                return
        raise Exception("REGISTRY: Object '%s' not registered" % name)

    def is_active(self, name):
        for item in self.objects_active:
            if item.NAME == name:
                return True
        return False

    @property
    def objects(self):
        return self.registered

    @property
    def objects_active(self):
        return self.activated

    @property
    def objects_active_name(self):
        names = []
        for item in self.objects_active:
            names.append(item.NAME)
        return names


class AddonRegistry(Registry):
    pass

registry = AddonRegistry()


