import hashlib
import tempfile
import sys
from fabric.operations import sudo, local
import time
from golive.layers.base import TemplateBasedSetup, DebianPackageMixin, IPTablesSetup
from golive.stacks.stack import config, environment
from golive.utils import info, debug, error

OK="OK"
NOK="NOK"


class NginxSetup(DebianPackageMixin, TemplateBasedSetup):
    package_name = 'nginx'
    configfile = 'golive/nginx.conf'

    STATE_OK = "HTTP/1.1 200 OK"
    CMD_RC = "update-rc.d nginx start"
    CMD_STOP = "/etc/init.d/nginx stop"
    CMD_START = "/etc/init.d/nginx start"
    CMD_CURL = "curl -I"
    CMD_PS = "ps -ef|egrep -i nginx|egrep -v grep"

    ROLE = "APP_HOST"

    def init(self, update=True):
        DebianPackageMixin.init(self, update)
        self.execute(sudo, self.CMD_RC)

    def deploy(self):
        self.set_filename(self.__class__.configfile)
        app_hosts = environment.get_role(self.ROLE).hosts
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

        self.execute(sudo, self.CMD_STOP)
        self.execute(sudo, self.CMD_START)

        return self._call()

    def _call(self):
        if "test" not in sys.argv:
            out = local("%s http://%s" % (self.CMD_CURL, config['SERVERNAME']), capture=True)
            return out

    def update(self):
        self._call()

    def status(self, state=OK):
        info("NGINX: Processes on webservers")
        for item in self.run(self.CMD_PS).iteritems():
            num = len(item[1].splitlines())
            if num < 2:
                state = NOK
            info("NGINX: %s: %s" % (item[0], state))
            debug("NGINX: %s:\r\n%s" % (item[0], item[1]))
        out = self._call()
        http_line = out.partition("\r\n")[0]
        if "200" in http_line:
            info("SITE: %s" % http_line)
        else:
            error("SITE: %s" % http_line)
            error(out)

    def _port(self):
        h = hashlib.sha256("%s_%s" % (config['PROJECT_NAME'], config['ENV_ID']))
        return "8%s" % str(int(h.hexdigest(), base=16))[:3]


class NginxProxySetup(NginxSetup):
    configfile = 'golive/nginx_proxy.conf'
