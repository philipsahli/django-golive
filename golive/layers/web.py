import hashlib
import tempfile
from fabric.operations import sudo, local
import time
from golive.layers.base import TemplateBasedSetup, DebianPackageMixin, IPTablesSetup
from golive.stacks.stack import config, environment


class NginxSetup(DebianPackageMixin, TemplateBasedSetup):
    package_name = 'nginx'
    configfile = 'golive/nginx.conf'

    RULE = (None, config['DB_HOST'], 80)

    def init(self, update=True):
        DebianPackageMixin.init(self, update)
        self.execute(sudo, "update-rc.d nginx start")

    def deploy(self):
        self.set_filename(self.__class__.configfile)
        app_hosts = environment.get_role("APP_HOST").hosts
        self.set_context_data(
            SERVERNAME=config['SERVERNAME'],
            USER=config['USER'],
            APP_HOSTS=app_hosts,
            PORT=self._port()
        )
        # render
        file_data = self.load_and_render(self.filename, **self.context_data)

        # create temporary file
        temp = tempfile.NamedTemporaryFile(delete=False)
        file_local = temp.name
        temp.write(file_data)
        temp.flush()
        temp.close()

        # send file
        nginx_configfile = config['SERVERNAME']
        #self.put_sudo(file_local, "/etc/nginx/sites-enabled/%s.conf" % config['SERVERNAME'])
        self.put_sudo(file_local, "/etc/nginx/sites-enabled/%s.conf" % nginx_configfile)

        # TODO: add autostart
        self.execute(sudo, "/etc/init.d/nginx reload")
        self.execute(sudo, "/etc/init.d/nginx start")

        time.sleep(2)

        IPTablesSetup._open(self.__class__.RULE)

        print local("curl -I http://%s" % config['SERVERNAME'], capture=True)

    def _port(self):
        h = hashlib.sha256("%s_%s" % (config['PROJECT_NAME'], config['ENV_ID']))
        return "8%s" % str(int(h.hexdigest(), base=16))[:3]


class NginxProxySetup(NginxSetup):
    configfile = 'golive/nginx_proxy.conf'
