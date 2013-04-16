from django.conf import settings as django_settings
import tempfile
from fabric.api import run as remote_run
from fabric.context_managers import prefix, cd, settings
from fabric.contrib.files import exists, append
from fabric.operations import sudo, run, os, put
from django.template import loader, Context
from fabric.state import env
from fabric.tasks import execute
from golive.utils import nprint


class BaseTask(object):

    def __init__(self, config):
        self.config = config
        super(BaseTask, self).__init__()

    def run(self, command, fail_silently=False):
        if fail_silently:
            with settings(warn_only=True):
                return execute(remote_run, command)
        return execute(remote_run, command)

    def sudo(self, command):
        return execute(sudo, command)

    def mkdir(self, path):
        if not self.execute(exists, path):
            # create dir
            self.run("mkdir %s" % path, fail_silently=True)

    def rmdir(self, path):
        if self.execute(exists, path):
            # rm dir
            self.run("rm -rf %s" % path)

    def append(self, *args):
        execute(append, *args, use_sudo=True, hosts=env.hosts)

    def append_with_inituser(self, *args, **kwargs):
        hosts = []
        env.hosts_orig = env.hosts
        for host in env.hosts:
            hosts.append("%s@%s" % (kwargs['user'], host))

        execute(append, *args, use_sudo=True, hosts=hosts)
        env.hosts = env.hosts_orig

    def execute(self, f, *args):
        execute(f, *args, hosts=env.hosts)

    #def execute_role_only(self, f, *args):
    #    nprint(self.config)
    #    env.roledefs.update({ self.config['ROLE']: self.config['HOSTS'] })
    #    nprint(env)
    #    execute(f, *args, roles=[self.config['ROLES']])

    def put(self, local_filepath, remote_filepath):
        self.execute(put, local_filepath, remote_filepath)

    def put_sudo(self, local_filepath, remote_filepath):
        temp_remote_filepath = "/tmp/aa"
        self.execute(put, local_filepath, temp_remote_filepath)
        self.execute(sudo, "mv %s %s" % (temp_remote_filepath, remote_filepath))

    def check(self):
        print "No check actions defined"


class DjangoBaseTask(BaseTask):
    def manage(self, command):
        with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
            with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                self.run("python manage.py %s" % command)


class DebianPackageMixin():

    def install(self, update=True):
        if getattr(self.__class__, 'package_name', None):
            with settings(warn_only=True):
                o = self.execute(run, 'dpkg -l %s' % self.__class__.package_name)
                if update:
                    self.execute(sudo, "apt-get update")
                return self.execute(sudo, "apt-get -y install %s" % self.__class__.package_name)

    def remove(self):
        self.execute(sudo, "apt-get remove -y %s" % self.__class__.package_name)
        self.execute(sudo, "apt-get --purge autoremove -y -q")


class BaseSetup(BaseTask, DebianPackageMixin):
    ROLES = "ALL"
    # for deployment
    package_name = 'rsync git'
    # for PIL
    package_name += ' gcc python-dev libjpeg-dev libfreetype6-dev'


class TemplateBasedSetup(BaseTask):

    def load_and_render(self, template_name, **kwargs):
        t = loader.get_template(template_name)
        c = Context(kwargs)
        self.content = t.render(c)
        print self.content
        return self.content


class SupervisorSetup(DebianPackageMixin, TemplateBasedSetup):
    package_name = 'supervisor'

    def set_context_data(self, **kwargs):
        self.context_data = kwargs

    def set_filename(self, filename):
        self.supervisor_filename = filename

    def install(self, update=True):
        DebianPackageMixin.install(self, update)

        # render
        file_data = self.load_and_render(self.supervisor_filename, **self.context_data)

        # create temporary file
        temp = tempfile.NamedTemporaryFile(delete=False)
        file_local = temp.name
        temp.write(file_data)
        temp.flush()
        temp.close()

        # send file
        self.put_sudo(file_local, "/etc/supervisor/conf.d/django.conf")

        # reload supervisor
        self.execute(sudo, "supervisorctl reread")


class UserSetup(BaseTask):

    ROLES = "ALL"
    env.user = django_settings.DEPLOYMENT['defaults']['USER']

    def _useradd(self):
        user = self.config['USER']
        sudo("useradd -s /bin/bash -m %s" % user)

    def install(self):
        # create baseuser
        env.user = self.config['INIT_USER']
        env.project_name = self.config['PROJECT_NAME']
        user = self.config['USER']

        with settings(warn_only=True):
            # create user
            self.execute(self._useradd)
            # add to sudo
            self.append_with_inituser("/etc/sudoers", "%s ALL=NOPASSWD: ALL" % user, user=env.user)
            # send pub key

        # setup ssh pub-auth for user
        pubkey_file = self.config['PUBKEY']
        with settings(warn_only=True):
            self.sudo("mkdir /home/%s/.ssh/" % user)
            self.sudo("chmod 700 /home/%s/.ssh/" % user)
            self.sudo("chown %s:%s /home/%s/.ssh/" % (user, user, user))
            self.sudo("touch /home/%s/.ssh/authorized_keys2" % user)
            self.sudo("chmod 600 /home/%s/.ssh/authorized_keys2" % user)
            self.sudo("chown %s:%s /home/%s/.ssh/authorized_keys2" % (user, user, user))

        self.append("/home/%s/.ssh/authorized_keys2" % user, open(pubkey_file, 'r').readline())

        env.user = self.config['USER']
        # reset user in env
        #env.user = self.config['USER']
        #env.host_string = "%s@%s" % (env.user, self.__class__.host_string)
