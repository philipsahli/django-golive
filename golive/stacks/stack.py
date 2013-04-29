from collections import OrderedDict
import sys
from fabric.state import env
import yaml
from golive.utils import nprint

config = None
environment = None


class StackFactory(object):
    @classmethod
    def get(cls, stackname):

        if "CLASSIC" in stackname:
            return Stack(stackname)
        #elif stackname == "CLASSIC-GUNICORNED":
        #    return Stack(stackname)

        else:
            raise Exception("Stack '%s' not found" % stackname)


class Task(object):
    module_string = None

    def __init__(self, module):
        super(Task, self).__init__()
        self.module_string = module

    def __str__(self):
        return "Task: %s" % self.module_string

    def __repr__(self):
        return "Task: %s" % self.module_string

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
        return "Role: %s (Tasks: %s)" % (self.name, self.tasks)

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
        return [item for sublist in hosts for item in sublist]

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
    UPDATE = "update"
    CONFIG = "golive.yml"
    DEFAULTS = "DEFAULTS"

    def __init__(self, name):
        super(Stack, self).__init__()
        self.name = name
        self.environments = []
        self.environment_name = None
        self.environment = None

    def setup_environment(self, environment):
        self.environment_name = environment
        self.environment = Environment(self.environment_name)

        # read it
        self.configfile = self.read_config()

        # parse it
        self.parse()

    def __str__(self):
        return "Stack: %s" % self.name

    def parse(self):
        # load stack config (tasks for roles)
        stack_config = yaml.load(self.configfile)

        # load user config
        environment_configfile = open(Stack.CONFIG, 'r')
        self.environment_config_temp = yaml.load(environment_configfile)['ENVIRONMENTS']

        # load defaults, allows to be overwriten per environment
        self.environment_config = self.environment_config_temp[Stack.DEFAULTS]
        self.environment_config['SERVERNAME'] = self.environment_config_temp[self.environment_name.upper()]['SERVERNAME']

        # add environment roles
        self.environment_config.update({'ROLES': self.environment_config_temp[self.environment_name.upper()]['ROLES']})

        roles = stack_config['ROLES']

        for role, tasks in stack_config['ROLES'].items():
            # create role object
            role_obj = Role(role)
            role_obj.order = tasks['ORDER']

            # add every task
            for task in tasks['TASKS']:
                role_obj.add_task(Task(task))
            self.environment.add_role(role_obj)

        self.host_to_roles()

    def host_to_roles(self):
        for role, hosts in self.environment_config['ROLES'].items():
            if hosts is None:
                hosts = []
            self.get_role(role).hosts = hosts

    def read_config(self):
        pmd = sys.modules['golive.stacks'].__path__[0]
        configfile = file("%s/%s.yaml" % (pmd, self.name.lower()), "r")
        return configfile

    def _set_stack_config(self):
        mod = sys.modules['golive.stacks.stack']
        mod.config = self.environment_config
        mod.config.update({'ENV_ID': self.environment_name})
        mod.config.update({'DB_HOST': self.environment.get_role("DB_HOST").hosts[0]})
        mod.environment = self.environment

    def do(self, job, task=None, role=None):
        # make stack config available to tasks
        self._set_stack_config()

        if job == Stack.INIT:
            self.install_all()
        elif job == Stack.UPDATE:
            if task is not None:
                self.update(selected_task=task)
            elif role is not None:
                self.update(selected_role=role)
            else:
                self.update_all()
        else:
            raise Exception("Job '%s' unknown" % job)

    def install_all(self):
        self._execute_tasks(Stack.INIT)

    def update_all(self):
        self._execute_tasks(Stack.UPDATE)

    #def _cleanout_tasks(self):

    def update(self, selected_task=None, selected_role=None):
        if selected_task:
            self._cleanout_tasks(selected_task)
        if selected_role:
            self._cleanout_role(selected_task)

        self._execute_tasks(Stack.UPDATE)

    def _cleanout_role(self, selected_role):
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


    def _execute_tasks(self, method):
        print "Executing '%s'" % method
        for role in self.environment.roles:
            if role.has_hosts():
                # prepare env for fabric
                self._prepare_env(role)
                print "****************************** "
                print "Role: %s" % str(role.name)
                print "        %s:" % "Hosts"
                for host in role.hosts:
                    print "              %s" % host
                for task in role.tasks:
                    print "        %s" % task
                print "****************************** "
                for task in role.tasks:
                    print "---------- "
                    print str(task)
                    print "---------- "
                    task_class = task._load_module()
                    task_obj = task_class()
                    method_impl = getattr(task_obj, method)
                    method_impl()
                print ""

    def _prepare_env(self, role):
        env.roledefs.update({role: role.hosts})
        env.hosts = role.hosts

    #def install_on_host(self, environment, host):
    #    pass

    #def install_on_role(self, environment, role):
    #    pass

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


