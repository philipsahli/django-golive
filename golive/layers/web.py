import hashlib
import tempfile
import sys
from fabric.operations import sudo, local
import time
from golive.layers.base import TemplateBasedSetup, DebianPackageMixin, IPTablesSetup
from golive.stacks.stack import config, environment


class NginxSetup(DebianPackageMixin, TemplateBasedSetup):
    package_name = 'nginx'
    configfile = 'golive/nginx.conf'

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
        self.put_sudo(file_local, "/etc/nginx/sites-enabled/%s.conf" % nginx_configfile)

        # TODO: add autostart
        self.execute(sudo, "/etc/init.d/nginx reload")
        self.execute(sudo, "/etc/init.d/nginx start")

        if "test" not in sys.argv:
            time.sleep(2)

        self._call()

    def _call(self):
        if "test" not in sys.argv:
            print local("curl -I http://%s" % config['SERVERNAME'], capture=True)

    def update(self):
        self._call()

    def status(self):
        print self.run("ps -ef|egrep -i nginx")
        print self._call()

    def _port(self):
        h = hashlib.sha256("%s_%s" % (config['PROJECT_NAME'], config['ENV_ID']))
        return "8%s" % str(int(h.hexdigest(), base=16))[:3]


class NginxProxySetup(NginxSetup):
    configfile = 'golive/nginx_proxy.conf'
