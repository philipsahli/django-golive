import hashlib
import tempfile
import sys
from fabric.operations import sudo, local, os
from golive.layers.base import TemplateBasedSetup, DebianPackageMixin
from golive.stacks.stack import config, environment
from golive.utils import info, debug, error

OK = "OK"
NOK = "NOK"


class NginxSetup(DebianPackageMixin, TemplateBasedSetup):
    package_name = 'nginx'

    STATE_OK = "HTTP/1.1 200 OK"
    CMD_RC = "update-rc.d nginx start"
    CMD_STOP = "/etc/init.d/nginx stop"
    CMD_START = "/etc/init.d/nginx start"
    CMD_RESTART = "/etc/init.d/nginx restart"
    CMD_CURL = "curl -I"
    CMD_PS = "ps -ef|egrep -i nginx:|egrep -v grep"

    BACKEND_ROLE = "APP_HOST"

    CONFIGFILE = 'golive/nginx.conf'
    TEMPLATE_DEFAULT = "golive/nginx_default.conf"
    SITES_ENABLED_DIR = "/etc/nginx/sites-enabled/"

    def init(self, update=True):
        DebianPackageMixin.init(self, update)
        self._configure_default()
        self.execute(sudo, self.CMD_RC)

    def _configure_default(self):
        self.local_filename = self.TEMPLATE_DEFAULT
        tmp_file = self.load_and_render_to_tempfile(self.local_filename, **self.context_data)

        # send file
        self.destination_filename = "default"
        destination_filename_path = os.path.join(self.SITES_ENABLED_DIR, self.destination_filename)
        self.put_sudo(tmp_file, destination_filename_path)
        self.execute(sudo, self.CMD_RESTART)

    def deploy(self):
        # template filename
        self.set_filename(self.CONFIGFILE)

        # context data for template
        app_hosts = environment.get_role(self.BACKEND_ROLE).hosts
        self.set_context_data(
            SERVERNAME=config['SERVERNAME'],
            USER=config['USER'],
            APP_HOSTS=app_hosts,
            PORT=self._port()
        )
        # render
        tmp_file = self.load_and_render_to_tempfile(self.filename, **self.context_data)

        # send file
        nginx_configfile = config['SERVERNAME']
        self.put_sudo(tmp_file, "/etc/nginx/sites-enabled/%s.conf" % nginx_configfile)

        self.execute(sudo, self.CMD_STOP)
        self.execute(sudo, self.CMD_START)

        return self._call()

    def _call(self):
        if "test" not in sys.argv:
            cmd = "%s http://%s" % (self.CMD_CURL, config['SERVERNAME'])
            out = local(cmd, capture=True)
            debug("SITE: checked with: %s " % cmd)
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
