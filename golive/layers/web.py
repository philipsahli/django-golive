import tempfile
from fabric.operations import sudo
from golive.layers.base import TemplateBasedSetup, DebianPackageMixin
from golive.stacks.stack import config, environment


class NginxSetup(DebianPackageMixin, TemplateBasedSetup):
    package_name = 'nginx'

    def init(self, update=True):
        DebianPackageMixin.init(self, update)
        self.execute(sudo, "update-rc.d nginx start")
        self.set_filename("golive/nginx.conf")
        app_hosts = environment.get_role("APP_HOST").hosts
        # TODO: backendid must be unique
        # TODO: listen port must be unique or on ip
        self.set_context_data(
            #SERVERNAME=environment.get_role("WEB_HOST").hosts[0],
            SERVERNAME=config['SERVERNAME'],
            USER=config['USER'],
            APP_HOSTS=app_hosts
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
        self.put_sudo(file_local, "/etc/nginx/sites-enabled/%s.conf" % config['SERVERNAME'])

        # TODO: add autostart
        self.execute(sudo, "/etc/init.d/nginx reload")
        self.execute(sudo, "/etc/init.d/nginx start")
