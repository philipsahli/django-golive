import socket
import tempfile

from fabric.api import run as remote_run
from fabric.context_managers import prefix, cd, settings, hide
from fabric.contrib.files import exists, append
from fabric.operations import sudo, put, get
from fabric.state import env
from fabric.tasks import execute

from django.conf import settings as django_settings
from django.template import loader, Context
from golive.stacks.stack import config, environment


class BaseTask(object):

    def __init__(self):
        # TODO: allow custom packages to be installed
        super(BaseTask, self).__init__()

    def update(self):
        #print "! not implemented !"
        pass

    def run(self, command, fail_silently=False):
        #with hide('running'):
        if fail_silently:
            with settings(warn_only=True):
                return execute(remote_run, command)
        return execute(remote_run, command)

    def sudo(self, command):
        #with hide('running'):
        return execute(sudo, command)

    def mkdir(self, path):
        self.execute_silently(remote_run, "mkdir %s" % path)

    def rmdir(self, path):
        if self.execute(exists, path):
            # rm dir
            self.run("rm -rf %s" % path)

    def append(self, *args):
        #with hide('running'):
        execute(append, *args, use_sudo=True, hosts=env.hosts)

    def append_with_inituser(self, *args, **kwargs):
        hosts = []
        env.hosts_orig = env.hosts
        for host in env.hosts:
            hosts.append("%s@%s" % (kwargs['user'], host))

        execute(append, *args, use_sudo=True, hosts=hosts)
        env.hosts = env.hosts_orig

    def execute(self, f, *args):
        #with hide('running'):
        return execute(f, *args, hosts=env.hosts)

    def execute_silently(self, f, *args):
        with settings(warn_only=True):
            return execute(f, *args, hosts=env.hosts)

    def execute_once(self, f, *args):
        # only on first host
        host=env['hosts'][0]
        return execute(f, *args, hosts=[host])

    def get(self, remote_filepath):
        self.execute(get, remote_filepath)

    def put(self, local_filepath, remote_filepath):
        self.execute(put, local_filepath, remote_filepath)

    def put_sudo(self, local_filepath, remote_filepath):
        temp_remote_filepath = "/tmp/aa"
        self.execute(put, local_filepath, temp_remote_filepath)
        self.execute(sudo, "mv %s %s" % (temp_remote_filepath, remote_filepath))

    def check(self):
        print "No check actions defined"


class DjangoBaseTask():
    def manage(self, command):
        with prefix('. %s/.virtualenvs/%s/bin/activate' % (env.remote_home, env.project_name)):
            with cd("%s/code/%s" % (env.remote_home, env.project_name)):
                self.run("python manage.py %s" % command)


class DebianPackageMixin():

    def init(self, update=True):
        if getattr(self.__class__, 'package_name', None):
            with settings(warn_only=True):
                #o = self.execute(run, 'dpkg -l %s' % self.__class__.package_name)
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
    package_name += ' gcc python-dev libjpeg-dev libfreetype6-dev postgresql-client'
    # for daily operations
    package_name += ' htop curl lsof sysstat'

    def init(self, update=True):
        DebianPackageMixin.init(self, update=True)
        self._setup_hostfile()

    def _setup_hostfile(self):
        for host in environment.hosts:
            ip = socket.gethostbyname(host)
            self.append("/etc/hosts", "%s %s" % (ip, host))


class TemplateBasedSetup(BaseTask):

    def set_filename(self, filename):
        self.filename = filename

    def load_and_render(self, template_name, **kwargs):
        t = loader.get_template(template_name)
        c = Context(kwargs)
        self.content = t.render(c)
        return self.content

    def set_context_data(self, **kwargs):
        self.context_data = kwargs


class SupervisorSetup(DebianPackageMixin, TemplateBasedSetup):
    package_name = 'supervisor'

    def set_local_filename(self, filename):
        self.local_filename = filename

    def set_destination_filename(self, filename):
        self.destination_filename = filename

    def init(self, update=True):
        DebianPackageMixin.init(self, update)

        # render
        file_data = self.load_and_render(self.local_filename, **self.context_data)

        # create temporary file
        temp = tempfile.NamedTemporaryFile(delete=False)
        file_local = temp.name
        temp.write(file_data)
        temp.flush()
        temp.close()

        # send file
        self.put_sudo(file_local, self.destination_filename)

        # sed pattern
        #self.execute(sudo, "HOSTNAME=`uname -n` ; sed \"s/%.*HOST.*%/$HOSTNAME/g\" -i " + self.destination_filename)
        # must be set to the interface for this domain or on a different port
        self.execute(sudo, "HOSTNAME='"+env.hosts[0]+"' ; sed \"s/%.*HOST.*%/$HOSTNAME/g\" -i " + self.destination_filename)

        # initial daemon start
        self.execute(sudo, "pgrep supervisor || /etc/init.d/supervisor start")

        # reload supervisor
        self.execute(sudo, "supervisorctl reread")
        self.execute(sudo, "supervisorctl reload")


class UserSetup(BaseTask):

    ROLES = "ALL"

    def _useradd(self):
        user = config['USER']
        with hide("warnings"):
            sudo("useradd -s /bin/bash -m %s" % user)

    def init(self):
        # create baseuser
        from golive.stacks.stack import config
        #print config
        env.user = config['INIT_USER']
        env.project_name = config['PROJECT_NAME']
        user = config['USER']

        with settings(warn_only=True):
            # create user
            self.execute(self._useradd)
            # add to sudo
            self.append_with_inituser("/etc/sudoers", "%s ALL=NOPASSWD: ALL" % user, user=env.user)

        # setup ssh pub-auth for user
        pubkey_file = config['PUBKEY']
        with settings(warn_only=True):
            with hide("warnings"):
                self.sudo("mkdir /home/%s/.ssh/" % user)
            self.sudo("chmod 700 /home/%s/.ssh/" % user)
            self.sudo("chown %s:%s /home/%s/.ssh/" % (user, user, user))
            self.sudo("touch /home/%s/.ssh/authorized_keys2" % user)
            self.sudo("chmod 600 /home/%s/.ssh/authorized_keys2" % user)
            self.sudo("chown %s:%s /home/%s/.ssh/authorized_keys2" % (user, user, user))

        self.append("/home/%s/.ssh/authorized_keys2" % user, open(pubkey_file, 'r').readline())

        env.user = config['USER']
