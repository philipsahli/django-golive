import tempfile
from django.test import TestCase
import yaml
from mock import patch
from golive.layers.base import UserSetup
from golive.stacks.stack import StackFactory, Stack


def read_userconfigfile():

    testconfig = """CONFIG:
    PLATFORM: DEDICATED
    STACK: CLASSIC

ENVIRONMENTS:
    DEFAULTS:
        INIT_USER: fatrix
        PROJECT_NAME: django_example
        PUBKEY: $HOME/user.pub
        # TODO: add pip packages not in requirements
        # TODO: add custom debian packages
        #
    TESTING:
        SERVERNAME: golive-sandbox1
        ROLES:
            APP_HOST:
                - testbox1
            DB_HOST:
                - testbox1
            WEB_HOST:
                - testbox1"""

    f, environment_configfile = tempfile.mkstemp()
    config = open(environment_configfile, 'w')
    config.write(testconfig)
    config.close()
    config1 = open(environment_configfile, 'r')

    # return created file
    return config1

# class TaskCollectorTest(TestCase):
#     DEPLOYMENT = {
#         'stack': "classic",
#         'defaults': {
#             'INIT_USER': "fatrix",
#             'PROJECT_NAME': "django_example",
#             'USER': "xcore",
#             'PUBKEY': "/Volumes/Data/Users/fatrix/.ssh/id_dsa.pub"
#         },
#         'test': {
#             'roles': {'APP_HOST': ["xcore", "xcore2"],
#                       'DB_HOST': ["xcoredb"],
#                       'CACHE_HOST': ["xcoredb"],
#                       'WEB_HOST': ["xcore1"]}
#         }
#     }
#
#     def setUp(self):
#         super(TaskCollectorTest, self).setUp()
#
#     @override_settings(DEPLOYMENT=DEPLOYMENT)
#     @patch("fabric.tasks._execute")
#     def test_init_tasks_for_one_host(self, mock_execute):
#         mock_execute.return_value = "", "", True
#         kwargs = {'env_id': "test", 'host': "xcore", 'job': "INIT"}
#         task_manager = TaskCollector.run(**kwargs)
#         self.assertIsInstance(task_manager, TaskManager)
#         self.assertEqual(task_manager.roles, 'APP_HOST')
#         self.assertEqual(task_manager.hosts, ['xcore'])
#         self.assertEqual(task_manager.mode, "HOST")
#         self.assertEqual(4, len(task_manager.tasks))
#         task_manager.run()
#
#     @override_settings(DEPLOYMENT=DEPLOYMENT)
#     @patch("fabric.tasks._execute")
#     def test_update_tasks_for_one_host(self, mock_execute):
#         mock_execute.return_value = "", "", True
#         kwargs = {'env_id': "test", 'host': "xcore", 'job': "UPDATE"}
#         task_manager = TaskCollector.run(**kwargs)
#         self.assertIsInstance(task_manager, TaskManager)
#         self.assertEqual(task_manager.roles, 'APP_HOST')
#         self.assertEqual(task_manager.hosts, ['xcore'])
#         self.assertEqual(task_manager.mode, "HOST")
#         self.assertEqual(4, len(task_manager.tasks))
#         task_manager.run()
#
#
#     @override_settings(DEPLOYMENT=DEPLOYMENT)
#     @patch("fabric.tasks._execute")
#     def test_check_tasks_for_one_host(self, mock_execute):
#         mock_execute.return_value = "", "", True
#         kwargs = {'env_id': "test", 'host': "xcore", 'job': "CHECK"}
#         task_manager = TaskCollector.run(**kwargs)
#         self.assertIsInstance(task_manager, TaskManager)
#         self.assertEqual(task_manager.roles, 'APP_HOST')
#         self.assertEqual(task_manager.hosts, ['xcore'])
#         self.assertEqual(task_manager.mode, "HOST")
#         self.assertEqual(4, len(task_manager.tasks))
#         task_manager.run()
#
#     @override_settings(DEPLOYMENT=DEPLOYMENT)
#     @patch("fabric.tasks._execute")
#     def test_init_tasks_for_multiple_host(self, mock_execute):
#         mock_execute.return_value = "", "", True
#         kwargs = {'env_id': "test", 'hosts': ["xcore", "xcoreb"], 'job': "INIT"}
#         task_manager = TaskCollector.run(**kwargs)
#         self.assertIsInstance(task_manager, TaskManager)
#         self.assertEqual(task_manager.roles, ['APP_HOST'])
#         self.assertEqual(task_manager.hosts, ['xcore', 'xcoreb'])
#         self.assertEqual(task_manager.mode, "HOSTS")
#         self.assertEqual(4, len(task_manager.tasks))
#         task_manager.run()
#
#     @override_settings(DEPLOYMENT=DEPLOYMENT)
#     @patch("fabric.tasks._execute")
#     def test_collector_for_one_role(self, mock_execute):
#         mock_execute.return_value = "", "", True
#         kwargs = {'env_id': "test", 'role': "APP_HOST", 'job': "INIT"}
#         tasks = TaskCollector.run(**kwargs)
#         task_manager = TaskCollector.run(**kwargs)
#         self.assertIsInstance(task_manager, TaskManager)
#         self.assertEqual(task_manager.mode, "ROLE")
#         self.assertEqual(task_manager.roles, ['APP_HOST'])
#         self.assertEqual(task_manager.hosts, ['xcore', 'xcore2'])
#         self.assertEqual(4, len(task_manager.tasks))
#         task_manager.run()
#
#     @override_settings(DEPLOYMENT=DEPLOYMENT)
#     @patch("fabric.tasks._execute")
#     def test_collector_for_one_environment(self, mock_execute):
#         mock_execute.return_value = "", "", True
#         kwargs = {'env_id': "test", 'job': "INIT"}
#         tasks = TaskCollector.run(**kwargs)
#         task_manager = TaskCollector.run(**kwargs)
#         self.assertIsInstance(task_manager, TaskManager)
#         self.assertEqual(task_manager.mode, "ROLE")
#         self.assertEqual(4, len(task_manager.hosts))
#         self.assertEqual(task_manager.roles, ['CACHE_HOST', 'APP_HOST', 'DB_HOST', 'WEB_HOST'])
#         self.assertEqual(task_manager.hosts, ['xcoredb', 'xcore', 'xcoredb', 'xcore1'])
#         self.assertEqual(6, len(task_manager.tasks))
#         task_manager.run()
#


class StackFactoryTest(TestCase):

    @patch.object(Stack, "_read_userconfigfile")
    def setUp(self, mock_method):
    #def setUp(self, mock_method):
        super(StackFactoryTest, self).setUp()

        #print golive.utils.resolve_host("asdf")

        mock_method.return_value = read_userconfigfile()
        #mock_method_resolve.return_value = "1.2.3.4"

        self.environment_config_temp = yaml.load(read_userconfigfile())['CONFIG']['STACK']

        self.stack = StackFactory.get("CLASSIC")
        self.stack.setup_environment("testing")

        # called in stack.do, otherwise environment var is missing
        self.stack._set_stack_config()

    def test_stack_loaded(self):
        self.assertEqual(3, self.stack.role_count)
        self.assertEqual(4, len(self.stack.tasks_for_role("APP_HOST")))
        self.assertEqual(4, len(self.stack.get_role("APP_HOST").tasks))
        self.assertEqual(1, len(self.stack.hosts_for_role("APP_HOST")))

        self.assertEqual(3, len(self.stack.get_role("DB_HOST").tasks))
        self.assertEqual(1, len(self.stack.hosts_for_role("DB_HOST")))

        self.assertEqual(3, len(self.stack.get_role("WEB_HOST").tasks))
        self.assertEqual(1, len(self.stack.hosts_for_role("WEB_HOST")))

    @patch("fabric.tasks._execute")
    @patch.object(UserSetup, "readfile")
    def test_install_stack(self, mock_readfile, mock_execute):
        mock_execute.return_value = "", "", True
        mock_readfile.return_value = "filecontent"
        self.stack.do(Stack.INIT)
        self.assertEqual(65, mock_execute.call_count)

    @patch("fabric.tasks._execute")
    @patch("golive.utils.resolve_host")
    def test_update_stack(self, mock_method_resolve, mock_execute):
        mock_method_resolve.return_value = "1.2.3.4"
        mock_execute.return_value = "", "", True
        self.stack.do(Stack.DEPLOY)
        self.assertEqual(55, mock_execute.call_count)

    @patch("fabric.tasks._execute")
    def test_update_stack_task_selected(self, mock_execute):
        mock_execute.return_value = "", "", True
        self.stack.do(Stack.DEPLOY, task="golive.layers.app.DjangoSetup")
        self.assertEqual(20, mock_execute.call_count)


class ManagementCommandTest(TestCase):
    @patch("fabric.tasks._execute")
    def test_stack_loaded(self, mock_execute):
        mock_execute.return_value = "", "", True
        pass


