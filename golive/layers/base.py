import tempfile
import sys
import time

from fabric.api import run as remote_run
from fabric.context_managers import settings, hide
from fabric.contrib.files import exists, append, sed, first
from fabric.decorators import parallel
from fabric.operations import sudo, put, get, os, run, local
from fabric.state import env
from fabric.tasks import execute
from django.template import loader, Context
from django.template.base import TemplateDoesNotExist
from django.core.management import call_command

from golive.stacks.stack import config, environment
from golive.utils import info, debug, error, warn


class BaseTask(object):

    def __init__(self):
        # TODO: allow custom packages to be installed
        super(BaseTask, self).__init__()

    # Tasks
    def pre_init(self):
        pass

    def init(self):
        pass

    def post_init(self):
        pass

    def pre_deploy(self):
        pass

    def deploy(self):
        pass

    def post_deploy(self):
        pass

    def pre_update(self):
        pass

    def post_backup(self):
        pass

    def backup(self):
        pass

    def restore(self):
        pass

    def update(self):
        pass

    def post_update(self):
        pass

    # End Tasks

    def run(self, command, fail_silently=False):
        if fail_silently:
            with settings(warn_only=True):
                return execute(remote_run, command)
        return execute(remote_run, command)

    @classmethod
    def run(cls, command, fail_silently=False):
        if fail_silently:
            with settings(warn_only=True):
                return execute(remote_run, command)
        return execute(remote_run, command)

    def sudo(self, command):
        return execute(sudo, command)

    @classmethod
    def sudo(cls, command):
        if env.user == 'root':
            return execute(run, command)
        return execute(sudo, command)

    def mkdir(self, path):
        info("BASE: create directory %s" % path)
        print env.hosts
        if env.hosts[0] == "localhost":
            local("mkdir %s" % path)
        else:
            self.execute_silently(remote_run, "mkdir %s" % path)

    def rmdir(self, path):
        if self.execute(exists, path):
            # rm dir
            self.run("rm -rf %s" % path)

    def append(self, *args):
        execute(append, *args, use_sudo=True, hosts=env.hosts)

    def first_file(self, host, *args):
        print host
        print args
        execute(first, *args, host=host)

    @classmethod
    def append(cls, *args):
        execute(append, *args, use_sudo=True, hosts=env.hosts)

    def append_with_inituser(self, *args, **kwargs):
        hosts = []
        env.hosts_orig = env.hosts
        for host in env.hosts:
            hosts.append("%s@%s" % (kwargs['user'], host))

        execute(append, *args, use_sudo=True, hosts=hosts)
        env.hosts = env.hosts_orig

    @parallel
    def execute(self, f, *args):
        out = {}
        for host in env.hosts:
            out.update(execute(f, *args, host=host))
            debug("%s: %s" % (f.__name__, args), host)
        return out

    @classmethod
    @parallel
    def execute(cls, f, *args):
        out = {}
        for host in env.hosts:
            out.update(execute(f, *args, host=host))
            debug("%s: %s" % (f.__name__, args), host)
        return out

    def execute_on_host(self, f, host, *args):
        env.saved = env.hosts
        env.hosts = [host]

        if env.hosts[0] == "localhost":
            if f == run:
                local(args)
            else:
                error("local function not supported, run only.")
        out = self.execute(f, *args)
        env.hosts = env.saved
        return out

    @classmethod
    def execute_on_host(cls, f, host, *args):
        env.saved = env.hosts
        env.hosts = [host]
        if env.hosts[0] == "localhost" or host == "localhost":
            out = local(*args)
        else:
            out = cls.execute(f, *args)
        env.hosts = env.saved
        return out

    @parallel
    def execute_silently(self, f, *args):
        with settings(warn_only=True):
            return execute(f, *args, hosts=env.hosts)

    def execute_once(self, f, *args):
        # only on first host
        host = env['hosts'][0]
        print host
        if host == "localhost":
            if f == run:
                return local(*args)
            elif f == sed:
                print args
                return local("sed -i'.bk' 's/%s/%s/g' %s" % (args[1], args[2], args[0]))
            else:
                print "No method found"
                return


        return execute(f, *args, hosts=[host])

    def get(self, remote_filepath):
        self.execute(get, remote_filepath)

    def put(self, local_filepath, remote_filepath):
        self.execute(put, local_filepath, remote_filepath)

    @parallel
    def put_sudo(self, local_filepath, remote_filepath):
        temp_remote_filepath = "/tmp/aa"
        self.execute(put, local_filepath, temp_remote_filepath)
        self.execute(sudo, "mv %s %s" % (temp_remote_filepath, remote_filepath))

    def check(self):
        print "No check actions defined"

    @parallel
    def chown(self, filename, user):
        self.execute(sudo, "chown %s %s" % (user, filename))

    def _check_output(self, output, expected_string, msg):
        for host, result in output.items():
            if expected_string in result:
                info("%s on %s: OK" % (msg, host))
            else:
                error("%s on %s: NOK" % (msg, host))
            debug(result, host=host)


    def execute_local(self, command):
        local(command)


class TemplateBasedSetup(BaseTask):

    def __init__(self):
        # set default data available in templates
        self.context_data = {}

        # reimport config
        from golive.stacks.stack import config

        home = os.path.join("/home", config['USER'])
        self.context_data.update(
                    {
                        'USER': config['USER'],
                        'HOME': home,
                        'LOGDIR': os.path.join(home, "log"),
                        'PYTHON': os.path.join(home, ".virtualenvs/%s/bin/python"
                                                     % config['PROJECT_NAME']),
                        'PROJECT': config['PROJECT_NAME'],
                        'ENVIRONMENT': config['ENV_ID'],
                    }
        )

        self.filename = None
        self.local_filename = None
        self.destination_filename = None
        self.content = None

        super(TemplateBasedSetup, self).__init__()

    def set_filename(self, filename):
        self.filename = filename

    def set_local_filename(self, filename):
        self.local_filename = filename

    def set_destination_filename(self, filename):
        self.destination_filename = filename

    def load_and_render(self, template_name, **kwargs):
        t = loader.get_template(template_name)
        c = Context(kwargs)
        self.content = t.render(c)
        return self.content

    def load_and_render_to_tempfile(self, template_name, **kwargs):
        content = self.load_and_render(template_name, **kwargs)
        # create temporary file
        file_local = self._to_temporary_file(content)
        return file_local

    def set_context_data(self, **kwargs):
        self.context_data = dict(kwargs.items() + self.context_data.items())

    def _to_temporary_file(self, file_data):
        temp = tempfile.NamedTemporaryFile(delete=False)
        file_local = temp.name
        temp.write(file_data)
        temp.flush()
        temp.close()
        return file_local


class DebianPackageMixin():

    def init(self, update=True):
        from golive.stacks.stack import config
        env.user = config['INIT_USER']
        if getattr(self.__class__, 'package_name', None):
            with settings(warn_only=True):
                if update:
                    self.sudo("apt-get update")
                    info("INSTALL: %s" % self.__class__.package_name)
                return self.sudo("apt-get -y install %s" % self.__class__.package_name)

    #def remove(self):
    #    self.execute(sudo, "apt-get remove -y %s" % self.__class__.package_name)
    #    self.execute(sudo, "apt-get --purge autoremove -y -q")


class PyPackageMixin():

    def init(self, update=True):
        if getattr(self.__class__, 'package_name', None):
            with settings(warn_only=True):
                if update:
                    self.execute(sudo, "apt-get update")
                return self.execute(sudo, "apt-get -y install %s" % self.__class__.package_name)

    #def remove(self):
    #    self.execute(sudo, "apt-get remove -y %s" % self.__class__.package_name)
    #    self.execute(sudo, "apt-get --purge autoremove -y -q")


class BaseSetup(BaseTask, DebianPackageMixin, PyPackageMixin):
    ROLES = "ALL"
    # for deployment
    package_name = 'rsync git'
    # for PIL
    package_name += ' gcc python-dev libjpeg-dev libfreetype6-dev postgresql-client mercurial'
    # for daily operations
    package_name += ' htop curl lsof sysstat'
    # for process management
    package_name += ' supervisor'

    def init(self, update=True):
        DebianPackageMixin.init(self, update=True)

        self._setup_hostfile()

        with settings(warn_only=True):
            self.sudo("mkdir %s" % IPTablesSetup.CONFIG_DIR)
            self.sudo("mkdir %s" % IPTablesSetup.SERVICES_CONFIG_DIR)

        allow = [(environment.hosts, IPTablesSetup.DESTINATION_ALL, "1111")]
        iptables = IPTablesSetup()
        iptables.prepare_rules(allow)
        iptables.set_rules(self.__class__.__name__)
        iptables.activate()

        self._secure()

        # install addons
        if "NEW_RELIC" in environment.stack.addons:
            from golive.addons.newrelic import NewRelicServerAgentAddon
            agent = NewRelicServerAgentAddon()
            agent.init()

    def deploy(self):
        self._secure()

    def _secure(self):
        # secure sshd
        self._secure_sshd()

    def _secure_sshd(self):
        # don't allow authentication with passwords
        from golive.stacks.stack import config
        env.user = config['USER']
        self.append("/etc/ssh/sshd_config", "PasswordAuthentication no")
        # reload
        self.sudo("/etc/init.d/ssh reload")

    def _setup_hostfile(self):
        """
        Add every host in environment to the hostfile on the server(s).
        """
        from golive.stacks.stack import environment
        # import here to enable mocking
        from golive.utils import resolve_host
        for host in environment.hosts:
            ip = resolve_host(host)
            self.append("/etc/hosts", "%s %s" % (ip, host))


class CrontabSetup(TemplateBasedSetup):
    TEMPLATE = "golive/cron/base.crontab"
    CRONDIR = "/etc/cron.d"

    def deploy(self):
	env.user = self.stack.environment_config['USER']
        from golive.stacks.stack import config
        self.local_filename = self.TEMPLATE.replace("base", config['ROLE'].name.lower())
        if self.local_filename is None:
            return
        # render
        try:
            self.context_data = {'USER': config['USER'],
                                 'LOGDIR':  os.path.join("/home", config['USER']) + "/log"
            }

            info("CRONTAB: setup crontab")
            tmp_file = self.load_and_render_to_tempfile(self.local_filename, **self.context_data)

            # send file
            self.destination_filename = "%s_%s_%s" % (config['PROJECT_NAME'], config['ENV_ID'],
                                                      os.path.basename(self.local_filename.replace(".crontab", "")))
            destination_filename_path = os.path.join(self.CRONDIR, self.destination_filename)
            self.put_sudo(tmp_file, destination_filename_path)
            info("CRONTAB: %s saved to %s" % (self.local_filename, self.CRONDIR))
        except TemplateDoesNotExist, e:
            warn("Template %s does not exist" % self.local_filename)
        except Exception, e:
            error(e)

    def update(self):
        self.deploy()


class SupervisorSetup(DebianPackageMixin, TemplateBasedSetup):
    #package_name = 'supervisor'

    def init(self, update=True):
        DebianPackageMixin.init(self, update)

    def deploy(self):
        # render
        tempfile = self.load_and_render_to_tempfile(self.local_filename, **self.context_data)

        # send file
        self.put_sudo(tempfile, self.destination_filename)

    def post_deploy(self):
        # sed pattern
        # must be set to the interface for this domain or on a different port

        # initial daemon start
        self.execute(sudo, "pgrep supervisor || /etc/init.d/supervisor start")

        # reload supervisor
        self.execute(sudo, "supervisorctl reread ; supervisorctl reload ")
        if "test" not in sys.argv:
            time.sleep(5)        # let supervisor do his work first


class UserSetup(BaseTask, DebianPackageMixin):
    package_name = 'sudo'
    ROLES = "ALL"

    def _useradd(self):
        from golive.stacks.stack import config
        env.user = config['INIT_USER']
        info("USER: create user %s" % config['USER'])
        with hide("warnings"):
            self.sudo("useradd -s /bin/bash -m %s" % config['USER'])

    def init(self):
        # create baseuser
        from golive.stacks.stack import config

        env.user = config['INIT_USER']
        DebianPackageMixin.init(self, update=True)

        env.project_name = config['PROJECT_NAME']
        user = config['USER']

        info("SUDO: configure for user %s" % env.user)
        with settings(warn_only=True):
            # create user
            self.execute(self._useradd)
            # add to sudo
            self.append_with_inituser("/etc/sudoers", "%s ALL=NOPASSWD: ALL" % user, user=env.user)


        pip_cache_dir = "/var/cache/pip"
        debug("PIP: Create cache dir %s" % pip_cache_dir)
        with settings(warn_only=True):
            with hide("warnings"):
                self.sudo("mkdir %s" % pip_cache_dir)
                self.sudo("chmod 777 %s" % pip_cache_dir)

        # create rc file
        with settings(warn_only=True):
            self.execute(sudo, "touch /home/%s/.golive.rc" % user)
            self.execute(sudo, "chmod 600 /home/%s/.golive.rc" % user)
            self.execute(sudo, "chown %s:%s /home/%s/.golive.rc" % (user, user, user))
            self.append("/home/%s/.bashrc" % user, ". .golive.rc")
            self.append("/home/%s/.bash_profile" % user, ". .golive.rc")

        # setup ssh pub-auth for user
        pubkey_file = config['PUBKEY']
        info("PUBKEY: Put %s to authorized_keys2" % pubkey_file)
        with settings(warn_only=True):
            with hide("warnings"):
                self.sudo("mkdir /home/%s/.ssh/" % user)
            self.sudo("chmod 700 /home/%s/.ssh/" % user)
            self.sudo("chown %s:%s /home/%s/.ssh/" % (user, user, user))
            self.sudo("touch /home/%s/.ssh/authorized_keys2" % user)
            self.sudo("chmod 600 /home/%s/.ssh/authorized_keys2" % user)
            self.sudo("chown %s:%s /home/%s/.ssh/authorized_keys2" % (user, user, user))

        self.append("/home/%s/.ssh/authorized_keys2" % user, self.readfile(os.path.expanduser(pubkey_file)))

        env.user = config['USER']

        # set base variables
        from golive.stacks.stack import environment
        for host in environment.hosts:
            args = (config['ENV_ID'], 'HOST', host, True)
            environment.stack.do("set_var", full_args=args)

    def readfile(self, filename):
        return open(filename, 'r').readline()


IPTABLES_UP_RULE = "/etc/iptables.up.rules"


class Rule():

    def __init__(self, source, destination, port):
        self.source = source
        self.destination = destination
        self.port = port

    def line(self, line=None):

        accept_line = "-A INPUT -p tcp --dport %s -j ACCEPT" % self.port
        line = accept_line + " -s %s -d %s" % (self._join_ips(self.source), self.destination)

        return line

    def _join_ips(self, ip_list, ips=""):
        if not isinstance(ip_list, list):
            ip_list = [ip_list]
        for ip in ip_list:
            ips+="%s," % ip
        return ips[:-1]


class IPTablesSetup(TemplateBasedSetup, BaseTask):
    """
    Execute following on the server, when you don't no a port who is used:
    iptables -A INPUT  -j LOG ! -d 10.211.55.255/32 --log-prefix "iptables IN: "
    """

    IPTABLES_BIN = "iptables"
    CONFIG_DIR = "/etc/iptables.conf.d"
    HEADER_BASE_CONFIG = "iptables_header"
    FOOTER_BASE_CONFIG = "iptables_footer"
    SERVICES_CONFIG_DIR = CONFIG_DIR + "/services"

    DESTINATION_ALL = "0.0.0.0/0"
    SOURCE_ALL = "0.0.0.0/0"
    LOOPBACK = "127.0.0.0/8"

    def __init__(self):
        from golive.stacks.stack import config
        env.user = config['USER']
        self.rules = None
        super(IPTablesSetup, self).__init__()

    def prepare_rules(self, allow_list):
        rules = []
        for allow in allow_list:
            rule = Rule(
                allow[0],
                allow[1],
                allow[2]
            )

            rules.append(rule)
        self.rules = rules
        return rules

    def set_rules(self, id):
        from golive.stacks.stack import config
        env.user = config['USER']
        configfile = "%s/%s_%s_%s" % (
            IPTablesSetup.SERVICES_CONFIG_DIR,
            "rules",
            id,
            env.user,
        )

        for rule in self.rules:
            info("IPTABLES: allow %s -> %s, tcp/%s" % (rule.source, rule.destination, rule.port))

        # clear file
        BaseTask.sudo("echo > %s" % configfile)

        for rule in self.rules:
            # append rule to file
            BaseTask.sudo("echo \"%s\" >> %s" % (rule.line(), configfile))

        self.activate()

    def activate(self):
        # add header to global file
        self.set_local_filename("golive/iptables/iptables_basic")
        headerfile = os.path.join(IPTablesSetup.CONFIG_DIR, IPTablesSetup.HEADER_BASE_CONFIG)
        self.set_destination_filename(headerfile)
        tempfile = self.load_and_render_to_tempfile(self.local_filename, **self.context_data)
        self.put_sudo(tempfile, self.destination_filename)
        self.chown(self.destination_filename, "root:root")

        # add footer to global file
        self.set_local_filename("golive/iptables/iptables_last")
        footerfile = os.path.join(IPTablesSetup.CONFIG_DIR, IPTablesSetup.FOOTER_BASE_CONFIG)
        self.set_destination_filename(footerfile)
        tempfile = self.load_and_render_to_tempfile(self.local_filename, **self.context_data)
        self.put_sudo(tempfile, self.destination_filename)
        self.chown(self.destination_filename, "root:root")

        # merge the files
        mergedfile = os.path.join(IPTablesSetup.CONFIG_DIR, "all")
        self.sudo("cat %s > %s" % (headerfile, mergedfile))
        self.sudo("cat %s/* >> %s" % (IPTablesSetup.SERVICES_CONFIG_DIR, mergedfile))
        self.sudo("cat %s >> %s" % (footerfile, os.path.join(IPTablesSetup.CONFIG_DIR, "all")))

        # activate the configuration
        self.sudo("iptables-restore < %s" % mergedfile)

    def init(self):

        # initialize the basic iptables setup only once
        self.deploy()
        self.post_deploy()

    def deploy(self):
        env.user = config['USER']

        # create temporary local file
        tempfile = self.load_and_render_to_tempfile(self.local_filename, **self.context_data)

        # add last
        self.set_local_filename("golive/iptables/iptables_last")
        content = self.load_and_render(self.local_filename, **self.context_data)
        open(tempfile, "a").write(content)

        # send file
        self.put_sudo(tempfile, self.destination_filename)

    def post_deploy(self):
        self.sudo("iptables-restore < %s" % self.destination_filename)
