import tempfile
from django.test import TestCase
#from unittest import skip
import yaml
from mock import patch
from golive.layers.base import UserSetup, IPTablesSetup, Rule, BaseTask
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


class BaseTestCase(TestCase):

    @patch.object(Stack, "_read_userconfigfile")
    def setUp(self, mock_method):
        super(TestCase, self).setUp()

        #print golive.utils.resolve_host("asdf")

        mock_method.return_value = read_userconfigfile()
        #mock_method_resolve.return_value = "1.2.3.4"

        self.environment_config_temp = yaml.load(read_userconfigfile())['CONFIG']['STACK']

        self.stack = StackFactory.get("CLASSIC")
        self.stack.setup_environment("testing")

        # called in stack.do, otherwise environment var is missing
        self.stack._set_stack_config()


class StackFactoryTest(BaseTestCase):

    @patch.object(Stack, "_read_userconfigfile")
    def setUp(self, mock_method):
        super(StackFactoryTest, self).setUp()

    def test_stack_loaded(self):
        self.assertEqual(3, self.stack.role_count)
        self.assertEqual(5, len(self.stack.tasks_for_role("APP_HOST")))
        self.assertEqual(5, len(self.stack.get_role("APP_HOST").tasks))
        self.assertEqual(1, len(self.stack.hosts_for_role("APP_HOST")))

        self.assertEqual(4, len(self.stack.get_role("DB_HOST").tasks))
        self.assertEqual(1, len(self.stack.hosts_for_role("DB_HOST")))

        self.assertEqual(4, len(self.stack.get_role("WEB_HOST").tasks))
        self.assertEqual(1, len(self.stack.hosts_for_role("WEB_HOST")))

    @patch("golive.utils.resolve_host")
    @patch("fabric.tasks._execute")
    @patch.object(UserSetup, "readfile")
    def test_install_stack(self, mock_readfile, mock_execute, mock_method_resolve):
        mock_method_resolve.return_value = "1.2.3.4"
        mock_execute.return_value = "", "", True
        mock_readfile.return_value = "filecontent"
        self.stack.do(Stack.INIT)
        self.assertEqual(83, mock_execute.call_count)

    # @skip("disabled")
    # @patch("fabric.tasks._execute")
    # @patch("golive.utils.resolve_host")
    # def test_update_stack(self, mock_method_resolve, mock_execute):
    #     mock_method_resolve.return_value = "1.2.3.4"
    #     mock_execute.return_value = "", "", True
    #     self.stack.do(Stack.DEPLOY)
    #     self.assertEqual(75, mock_execute.call_count)
    #
    # @skip("disabled")
    # @patch("fabric.tasks._execute")
    # def test_update_stack_task_selected(self, mock_execute):
    #     mock_execute.return_value = "", "", True
    #     self.stack.do(Stack.DEPLOY, task="golive.layers.app.DjangoSetup")
    #     self.assertEqual(35, mock_execute.call_count)


class ManagementCommandTest(TestCase):
    @patch("fabric.tasks._execute")
    def test_stack_loaded(self, mock_execute):
        mock_execute.return_value = "", "", True
        pass


class IPTableTest(BaseTestCase):


    @patch.object(Stack, "_read_userconfigfile")
    def setUp(self, mock_method):
        super(TestCase, self).setUp()

        #print golive.utils.resolve_host("asdf")

        mock_method.return_value = read_userconfigfile()
        #mock_method_resolve.return_value = "1.2.3.4"

        self.environment_config_temp = yaml.load(read_userconfigfile())['CONFIG']['STACK']

        self.stack = StackFactory.get("CLASSIC")
        self.stack.setup_environment("testing")

        # called in stack.do, otherwise environment var is missing
        self.stack._set_stack_config()


    def test_rule_objects_and_iptables_line_for_all_destination(self):
        self.allow = [(['hosta', 'hostb'], IPTablesSetup.DESTINATION_ALL, "1111")]
        rules = IPTablesSetup().prepare_rules(self.allow)
        self.assertIsInstance(rules, list)
        self.assertIsInstance(rules[0], Rule)
        self.assertIs(len(rules), 1)
        self.assertEquals(rules[0].line(),
                      "-A INPUT -p tcp --dport 1111 -j ACCEPT -s hosta,hostb -d 0.0.0.0/0")

    def test_rule_objects_and_iptables_line_for_all_source(self):
        self.allow = [(IPTablesSetup.SOURCE_ALL, IPTablesSetup.DESTINATION_ALL, "1111")]

        rules = IPTablesSetup().prepare_rules(self.allow)
        self.assertIsInstance(rules, list)
        self.assertIsInstance(rules[0], Rule)
        self.assertIs(len(rules), 1)
        self.assertEquals(rules[0].line(),
                      "-A INPUT -p tcp --dport 1111 -j ACCEPT -s 0.0.0.0/0 -d 0.0.0.0/0")

    def test_rule_objects_and_iptables_line_from_local_only(self):
        self.allow = [(IPTablesSetup.LOOPBACK, IPTablesSetup.DESTINATION_ALL, "1111")]

        rules = IPTablesSetup().prepare_rules(self.allow)
        self.assertIsInstance(rules, list)
        self.assertIsInstance(rules[0], Rule)
        self.assertIs(len(rules), 1)
        self.assertEquals(rules[0].line(),
                      "-A INPUT -p tcp --dport 1111 -j ACCEPT -s 127.0.0.0/8 -d 0.0.0.0/0")

    @patch.object(BaseTask, "run")
    @patch.object(BaseTask, "execute_on_host")
    def test_rules_set_on_hosts_already_defined(self, mock_execute_on_host, mock_run):

        mock_run.return_value = {'golive1': '0'}
        mock_execute_on_host.return_value = {'golive1': '0'}

        self.allow = [(['hosta', 'hostb'], IPTablesSetup.DESTINATION_ALL, "1111")]
        iptables = IPTablesSetup()
        iptables.prepare_rules(self.allow)
        #counter = iptables.set_rules("TestTask")
        #self.assertIs(counter, 0)

    @patch('golive.stacks.stack.config', {'USER': "usera"})
    @patch.object(BaseTask, "run")
    @patch.object(BaseTask, "execute_on_host")
    def test_rules_set_on_hosts_new(self, mock_execute_on_host, mock_run):
        mock_run.return_value = {'golive1': '1'}
        mock_execute_on_host.return_value = {'golive1': '0'}
        self.allow = [(['hosta', 'hostb'], IPTablesSetup.DESTINATION_ALL, "1111")]
        iptables = IPTablesSetup()
        iptables.prepare_rules(self.allow)
        #counter = iptables.set_rules("TestTask")
        #self.assertIs(counter, 1)
