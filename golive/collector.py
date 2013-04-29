# from django.conf import settings
# from fabric.state import env
#
#
# class TaskCollector(object):
#     TASKS = ["golive.layers.base.UserSetup",
#              "golive.layers.base.BaseSetup",
#              "golive.layers.db.PostgresSetup",
#              "golive.layers.app.PythonSetup",
#              "golive.layers.web.NginxSetup",
#              "golive.layers.app.ProjectDeployment",
#              ]
#
#
#     @staticmethod
#     def run(**kwargs):
#         env_id = kwargs.get('env_id', None)
#         job = kwargs.get('job', None)
#         specified_task = kwargs.get('task', None)
#         if env_id is None:
#             raise Exception("env_id not specified")
#         config = ConfigLoader.get(env_id)
#         # tasks
#         tasks = []
#
#         # job mode
#         config.update({'JOB': job})
#
#         # get options
#         host = kwargs.get('host', None)
#         hosts = kwargs.get('hosts', None)
#         role = kwargs.get('role', None)
#
#         # default
#         config.update({'ROLES': []})
#         # general
#         roles = config['roles']
#
#         if host:
#             config.update({'MODE': "HOST"})
#             config.update({'HOSTS': [host]})
#             for role in roles:
#                 if host in roles[role]:
#                     if role not in config['ROLES']:
#                         config['ROLES'].append(role)
#         #
#         elif hosts:
#             config.update({'MODE': "HOSTS"})
#             config.update({'HOSTS': hosts})
#             for role in roles:
#                 for host in hosts:
#                     if host in roles[role]:
#                         config['ROLES'].append(role)
#         #
#         elif role:
#             # check that role exists in configuration
#             if role not in config['roles'].keys():
#                 raise Exception("Role %s does not exist" % role)
#             config.update({'MODE': "ROLE"})
#             config.update({'ROLES': [role]})
#             if role in roles.keys():
#                 config.update({'HOSTS': roles[role]})
#
#         else:
#             hosts = []
#             for role in roles.keys():
#                 hosts.append(roles[role][0])
#             config.update({'MODE': "ROLE"})
#             config.update({'ROLES': config['roles'].keys()})
#             config.update({'HOSTS': hosts})
#
#         # collect tasks
#         for task in TaskCollector.TASKS:
#
#             # load task
#             modlist = task.split(".")
#             tt = modlist.pop(-1)
#             modpath = ".".join(modlist)
#             try:
#                 module = __import__(modpath, fromlist=[tt])
#                 task_class = getattr(module, tt)
#                 t = task_class
#             except AttributeError, e:
#                 print "cannot find class %s: %s" % (tt, e)
#             except ImportError, e:
#                 print "cannot import task %s: %s" % (tt, e)
#             except Exception, e:
#                 print "unexpected error %s: %s" % (tt, e)
#
#             if hasattr(t, "ROLES"):
#                 if t.ROLES == "ALL" or t.ROLES in config['ROLES']:
#                     if t not in tasks:
#                         # only specified task
#                         if specified_task:
#                             if tt == specified_task:
#                                 tasks.append(t)
#                         # all tasks
#                         else:
#                             tasks.append(t)
#                         print "- " + task
#             else:
#                 raise Exception("Configures task is missing ROLES attribute")
#
#         config.update({'TASKS': tasks})
#         return TaskManager(config)
#
#
# class TaskManager(object):
#     config = None
#
#     def __init__(self, config):
#         self.config = config
#
#     def run(self):
#         self._prepare_env()
#         for task in self.tasks:
#             print self.job + " " + str(task)
#             t = task(self.config)
#             if self.job == "INIT":
#                 t.install()
#             elif self.job == "UPDATE":
#                 if hasattr(t, "update"):
#                     t.update()
#             elif self.job == "CHECK":
#                 t.check()
#             else:
#                 raise Exception("Unknow job mode")
#
#     def _prepare_env(self):
#         """
#         Setup env dictionary for Fabric with roles and their hosts.
#         """
#         env.roledefs.update({self.roles[0]: [1, 2]})
#         env.hosts = self.hosts
#
#     @property
#     def job(self):
#         return self.config['JOB']
#
#     @property
#     def tasks(self):
#         return self.config['TASKS']
#
#     @property
#     def hosts(self):
#         return self.config['HOSTS']
#
#     @property
#     def mode(self):
#         return self.config['MODE']
#
#     @property
#     def roles(self):
#         if self.mode == "HOST":
#             return self.config['ROLES'][0]
#         return self.config['ROLES']
#
#
# class ConfigLoader(object):
#     @staticmethod
#     def get(env_key):
#         full_config = settings.DEPLOYMENT
#         # load defaults
#         config = full_config['defaults']
#         # load for env
#         env_config = full_config[env_key]
#         config.update(env_config)
#         config.update({'ENV_ID': env_key})
#         return config