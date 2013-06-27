from fabric.context_managers import settings
from golive.layers.app import get_remote_envvar
from golive.layers.base import BaseTask, DebianPackageMixin, IPTablesSetup
from golive.stacks.stack import environment


class RabbitMqSetup(BaseTask, DebianPackageMixin):
    package_name = "rabbitmq-server"
    GUEST_USER = "guest"
    RABBITMQ_CONFIGFILE = "/etc/rabbitmq/rabbitmq.config"
    RABBIT_INITSCRIPT = "/etc/init.d/rabbitmq-server"

    def init(self, update=True):
        # add repo for rabbitmq
        self._add_repo()
        self.sudo("apt-get update")

        DebianPackageMixin.init(self, update)

        self._set_listen_port()

        allow = [
                (environment.hosts, IPTablesSetup.DESTINATION_ALL, "9101:9105"),
                (environment.hosts, IPTablesSetup.DESTINATION_ALL, "4369"),
                (environment.hosts, IPTablesSetup.DESTINATION_ALL, "8612"),
                (environment.hosts, IPTablesSetup.DESTINATION_ALL, "5672"),
            ]
        iptables = IPTablesSetup()
        iptables.prepare_rules(allow)
        iptables.set_rules(self.__class__.__name__)
        iptables.activate()
        self._delete_user(self.__class__.GUEST_USER)

    def deploy(self):
        self._create_user()

    def status(self):
        print self.run("sudo %s status" % self.__class__.RABBIT_INITSCRIPT)

    def _set_listen_port(self):
        self.append(self.__class__.RABBITMQ_CONFIGFILE,
                    "[{kernel, [ {inet_dist_listen_min, 9100}, {inet_dist_listen_max, 9105} ]}].")

    def _add_repo(self):
        # as described at http://www.rabbitmq.com/install-debian.html
        self.append("/etc/apt/sources.list", "deb http://www.rabbitmq.com/debian/ testing main")
        self.sudo("wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc")
        self.sudo("apt-key add rabbitmq-signing-key-public.asc")

    def _create_user(self):
        username = get_remote_envvar('GOLIVE_BROKER_USER', environment.get_role("QUEUE_HOST").hosts[0])
        password = get_remote_envvar('GOLIVE_BROKER_PASSWORD', environment.get_role("QUEUE_HOST").hosts[0])
        with settings(warn_only=True):
            self.sudo("rabbitmqctl add_user %s %s" % (username, password))
            self.sudo("rabbitmqctl set_permissions -p / %s \".*\" \".*\" \".*\"" % username)
            # TODO: create vhost

    def _delete_user(self, username):
        with settings(warn_only=True):
            self.sudo("rabbitmqctl delete_user %s" % username)
