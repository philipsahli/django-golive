import glob
import sys
import datetime
from fabric.contrib.files import append, contains, sed
from fabric.operations import run, get, put, prompt, os
from fabric.state import env, output
import yaml
from fabric.tasks import execute
from golive.utils import info, debug, error

config = None
environment = None


class StackFactory(object):
    @classmethod
    def get(cls, stackname):

        #if "CLASSIC" in stackname:
        try:
            return Stack(stackname)
        #elif stackname == "GUNICORNED":
        #    return Stack(stackname)
        #elif stackname == "GUNICELERY":
        #    return Stack(stackname)
        #else:
        except Exception:
            raise Exception("Stack '%s' not found" % stackname)


class Task(object):
    module_string = None

    def __init__(self, module):
        super(Task, self).__init__()
        self.module_string = module

    def __str__(self):
        return "%s" % self.module_string

    def __repr__(self):
        return "%s" % self.module_string

    @property
    def module(self):
        return self._load_module()

    def _load_module(self):

        # load task
        modlist = self.module_string.split(".")
        tt = modlist.pop(-1)
        modpath = ".".join(modlist)
        try:
            module = __import__(modpath, fromlist=[tt])
            task_class = getattr(module, tt)
            t = task_class
        except AttributeError, e:
            print "cannot find class %s: %s" % (tt, e)
        except ImportError, e:
            print "cannot import task %s: %s" % (tt, e)
        except Exception, e:
            print "unexpected error %s: %s" % (tt, e)
        return t


class Role(object):
    name = None
    order = 0

    def __init__(self, name):
        super(Role, self).__init__()
        self.name = name
        self.tasks = []
        self.hosts = []

    def __str__(self):
        return "%s (Tasks: %s)" % (self.name, self.tasks)

    def add_task(self, task):
        self.tasks.append(task)

    def add_task_beginning(self, task):
        self.tasks.insert(0, task)

    def add_host(self, host):
        self.hosts.append(host)

    def has_hosts(self):
        return len(self.hosts) > 0


class Environment(object):

    def __init__(self, name):
        super(Environment, self).__init__()
        self.name = name
        self.roles = list()

    @property
    def hosts(self):
        hosts = []
        for role in self.roles:
            hosts.append(role.hosts)
        hosts = self._unique(hosts)
        return hosts

    def _unique(self, ls):
        lt = []
        lt += set([item for sublist in ls for item in sublist])
        return lt

    def get_role(self, role):
        for drole in self.roles:
            if role == drole.name:
                return drole
        return None

    def add_role(self, role):
        """
        Respects the order of the role.
        """
        self.roles.insert(role.order - 1, role)


class Stack(object):

    # Constants
    INIT = "init"
    DEPLOY = "deploy"
    UPDATE = "update"
    STATUS = "status"
    SET_VAR = "set_var"
    BACKUP = "backup"
    RESTORE = "restore"

    CONFIG = "golive.yml"
    DEFAULTS = "DEFAULTS"

    def __init__(self, name):
        super(Stack, self).__init__()
        self.name = name
        self.environments = []
        self.environment_name = None
        self.environment = None

        # setup output for fabric

        output['warnings'] = False
        output['status'] = False
        output['user'] = False
        output['running'] = False

    def setup_environment(self, environment):
        self.environment_name = environment
        self.environment = Environment(self.environment_name)

        self._set_configfile()

        # parse it
        self._parse()

    def __str__(self):
        return "Stack: %s" % self.name

    def _set_configfile(self):
        self.configfile = self._read_stackconfigfile()

    def _read_userconfigfile(self):
        return  open(Stack.CONFIG, 'r')

    def _parse(self):
        # load stack config (tasks for roles)
        stack_config = yaml.load(self.configfile)

        # load user config
        environment_configfile = self._read_userconfigfile()
        self.environment_config_temp = yaml.load(environment_configfile)['ENVIRONMENTS']

        # load defaults, allows to be overwriten per environment
        self.environment_config = self.environment_config_temp[Stack.DEFAULTS]
        self.environment_config['SERVERNAME'] = self.environment_config_temp[self.environment_name.upper()]['SERVERNAME']

        # add environment roles
        self.environment_config.update({'ROLES': self.environment_config_temp[self.environment_name.upper()]['ROLES']})

        # set remote user in the environment
        self._set_user()

        for role, tasks in stack_config['ROLES'].items():
            # create role object
            role_obj = Role(role)
            role_obj.order = tasks['ORDER']

            # add every task
            for task in tasks['TASKS']:
                role_obj.add_task(Task(task))
            self.environment.add_role(role_obj)

        self.host_to_roles()

        # put timestamp to environment
        now = datetime.datetime.now()
        ts = now.strftime("%Y%m%d%H%M%S")
        self.environment_config['TS'] = ts

    def _set_user(self):
        # custom uer is defined in DEFAULTS no further action needed
        if 'USER' in self.environment_config:
            return
        # custom user is defined in environment
        if 'USER' in self.environment_config_temp[self.environment_name.upper()]:
            self.environment_config['USER'] = self.environment_config_temp[self.environment_name.upper()]['USER']
            return
        # normal behaviour is to use a username in form:
        #    PROJECT_NAME_ENVIRONMENT
        # this allows to separate all data in $HOME, multiple environments of the same project can be deployed
        #    to the same server.
        self.environment_config['USER'] = "%s_%s" % (self.environment_config['PROJECT_NAME'], self.environment_name)

    def host_to_roles(self):
        for role, hosts in self.environment_config['ROLES'].items():
            if hosts is None:
                hosts = []
            self.get_role(role).hosts = hosts

    def _read_stackconfigfile(self):
        pmd = sys.modules['golive.stacks'].__path__[0]
        configfile = file("%s/%s.yaml" % (pmd, self.name.lower()), "r")
        return configfile

    def _set_stack_config(self):
        mod = sys.modules['golive.stacks.stack']
        mod.config = self.environment_config
        mod.config.update({'ENV_ID': self.environment_name})
        mod.config.update({'DB_HOST': self.environment.get_role("DB_HOST").hosts[0]})
        mod.environment = self.environment

        # set options to mod.config
        mod.config['OPTIONS'] = self.options
        #import pdb; pdb.set_trace()

    def do(self, job, task=None, role=None, full_args=None):
        # make stack config available to tasks
        self._set_stack_config()

        if job == Stack.INIT:
            self.initialize()
        elif job == Stack.DEPLOY:
            if task is not None:
                self.deploy(selected_task=task)
            elif role is not None:
                self.deploy(selected_role=role)
            else:
                self.deploy_all()
        elif job == Stack.UPDATE:
            self.update()
        elif job == Stack.STATUS:
            self.status()
        elif job == Stack.SET_VAR:
            self.set_var(full_args)
        elif job == Stack.BACKUP:
            self.backup()
        elif job == Stack.RESTORE:
            source_env = self.options['source_env']
            self.restore(source_env)
        else:
            raise Exception("Job '%s' unknown" % job)

    def set_var(self, full_args):
        key, value = "GOLIVE_%s" % full_args[1], full_args[2]
        env.user = config['USER']
        for host in list(set(self.environment.hosts)):

            print "configure variable %s on host %s with value: %s" % (key, host, value)

            # check if key already defined
            args = ("$HOME/.golive.rc", "export %s=" % key, False)
            defined = execute(contains, *args, host=host)

            if defined[host]:
                # we have to sed the line
                args = ("$HOME/.golive.rc", "export %s=.*$" % key, "export %s=%s" % (key, value))
                execute(sed, *args, host=host)
            else:
                # append it
                args = ("$HOME/.golive.rc", "export %s=%s" % (key, value))
                execute(append, *args, host=host)

    ######
    # TASKS
    ######
    def initialize(self):
        self._execute_tasks(Stack.INIT)

    def deploy_all(self):
        self._execute_tasks(Stack.DEPLOY)

    def update(self):
        self._execute_tasks(Stack.UPDATE)

    def status(self):
        self._execute_tasks(Stack.STATUS)

    def backup(self):
        self._execute_tasks(Stack.BACKUP)

        # finally pack and download
        # at the moment only from database server
        # we assume that uploads or media files are on shared storage like S3

        ts = config['TS']
        backup_dir = config['BACKUP_DIR']
        backup_file = "backup_%s_%s-%s.tgz" % (config['PROJECT_NAME'], config['ENV_ID'], ts)
        host = self.environment.get_role("DB_HOST").hosts[0]

        info("BACKUP: Pack and download backup to %s" % os.path.join(os.path.curdir, backup_file))
        from golive.layers.base import BaseTask
        BaseTask.execute_on_host(run, host, "cd %s && tar -zcvf ../%s ." % (backup_dir, backup_file))
        # delete temp directory
        BaseTask.execute_on_host(run, host, "rm -rf %s" % backup_dir)
        # get backup tgz
        BaseTask.execute_on_host(get, host, backup_file, ".")

    def restore(self, source_env):
        # capable to restore from another environment,
        # if not None, operator wishs to operate on the same one
        # as the backup has been taken from
        if source_env is None:
            source_env = config['ENV_ID']
        else:
            config['SOURCE_ENV'] = source_env
        self.ts = config['TS']
        env.user = config['USER']
        self.backup_dir = "$HOME/tmp_%s" % self.ts
        config['BACKUP_DIR'] = self.backup_dir

        # get all tgz files
        file_list = glob.glob("backup*%s*tgz" % source_env)
        sfile_list = ""
        for index, file in enumerate(file_list):
            if index > 0:
                sfile_list += "\r\n"
            sfile_list += "[%s] %s" % (index + 1, file)

        if len(sfile_list) < 1:
            error("Restore: No backup files found to work with.")
            sys.exit(1)
        else:
            print sfile_list

        try:
            selected = int(prompt("Which backup should be applied?")) - 1
        except ValueError:
            print "No file selected"
            sys.exit(0)

        file_path = file_list[selected]
        config['FILE_PATH'] = file_path

        ts = config['TS']
        host = self.environment.get_role("DB_HOST").hosts[0]

        from golive.layers.base import BaseTask
        # upload backup file and extract
        info("DB: upload and extract dump %s" % file_path)
        BaseTask.execute_on_host(put, host, file_path)
        BaseTask.execute_on_host(run, host, "tar -zxvf %s " % os.path.basename(file_path))

        # create and save dumpfilename
        config['BACKUP_DUMPFILE'] = file_path.replace("backup_", "db_").replace("tgz", "dump")

        info("DB: start restore of dump %s" % config['BACKUP_DUMPFILE'])

        # restore
        self._execute_tasks(Stack.RESTORE)

    def deploy(self, selected_task=None, selected_role=None):
        if selected_task:
            self._cleanout_tasks(selected_task)
        if selected_role:
            self._cleanout_role(selected_task)

        self._execute_tasks(Stack.DEPLOY)

    #####
    # Cleanup
    #####
    def _cleanout_role(self, selected_role):
        """
        Removes a role from the environment
        """
        selected_roles = []
        for role_idx, role in enumerate(environment.roles):
            if role.name == selected_role:
                selected_roles.append(role)
        environment.roles = selected_roles

    def _cleanout_tasks(self, selected_task):
        selected_roles_for_task = []
        for role_idx, role in enumerate(environment.roles):
            selected_tasklist = []
            for i in range(len(role.tasks)):
                task = role.tasks[i]
                if task.module_string == selected_task:
                    selected_tasklist.append(task)

            if len(selected_tasklist) != 0:
                role.tasks = selected_tasklist
                selected_roles_for_task.append(role)
            environment.roles = selected_roles_for_task

    ######
    # Execution
    ######
    def _execute_tasks(self, method):
        #d = {
        #    'environment_name': config['ENV_ID'],
        #    'method': method,
        #}
        debug("config: "+str(config))
        debug("environment_config: "+str(self.environment_config))
        info("***** START")
        for role in self.environment.roles:
            info("* ROLE %s" % role)
            mod = sys.modules['golive.stacks.stack']
            mod.config.update({'ROLE': role})
            if role.has_hosts():
                # prepare env for fabric
                self._prepare_env(role)
                info("** HOSTS %s" % role.hosts)
                for task in role.tasks:
                    try:
                        task_class = task._load_module()
                        task_obj = task_class()
                        # try to get method
                        try:
                            # execute pre
                            method_impl_pre = self._get_method(task_obj, "pre_" + method)
                            if method_impl_pre:
                                debug("EXECUTE %s" % method_impl_pre.__name__)
                                method_impl_pre()
                        except AttributeError:
                            pass
                        try:
                            # execute
                            method_impl = self._get_method(task_obj, method)
                            if method_impl:
                                info("*** TASK %s" % task)
                                debug("EXECUTE %s" % method_impl.__name__)
                                method_impl()
                        except AttributeError:
                            pass
                        try:
                            method_impl_post = self._get_method(task_obj, "post_" + method)
                            if method_impl_post:
                                debug("EXECUTE %s" % method_impl_post.__name__)
                                method_impl_post()
                        except AttributeError, e:
                            raise e
                    except UnboundLocalError, e:
                        raise e
        info("***** END")

    def _prepare_env(self, role):
        env.roledefs.update({role: role.hosts})
        env.hosts = role.hosts

    def _get_method(self, obj, method):
        method_impl = getattr(obj, method, None)
        return method_impl

    @property
    def role_count(self):
        return len(self.environment.roles)

    def tasks_for_role(self, role):
        return self.get_role(role).tasks

    def get_role(self, role):
        for drole in self.environment.roles:
            if role == drole.name:
               return drole
        return None

    def hosts_for_role(self, role):
        return self.get_role(role).hosts


