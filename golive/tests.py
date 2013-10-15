import tempfile
from django.test import TestCase
#from unittest import skip
import yaml
from mock import patch
import golive
from golive.addons.newrelic import NewRelicPythonAddon
from golive.layers.base import UserSetup, IPTablesSetup, Rule, BaseTask
from golive.stacks.stack import StackFactory, Stack
from golive.addons import registry


def read_userconfigfile():

    testconfig = """CONFIG:
    PLATFORM: DEDICATED
    STACK: CLASSIC
    ADDONS:
        - NEW_RELIC_PYTHON

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


class BaseTestCase(TestCase):

    @patch.object(Stack, "_read_userconfigfile")
    def setUp(self, mock_method):
        super(TestCase, self).setUp()

        mock_method.return_value = read_userconfigfile()

        self.environment_config_temp = yaml.load(read_userconfigfile())['CONFIG']['STACK']

        self.stack = StackFactory.get("CLASSIC")
        self.stack.setup_environment("testing")

        # called in stack.do, otherwise environment var is missing
        self.stack._set_stack_config()


class StackFactoryTest(BaseTestCase):

    @patch.object(Stack, "_read_userconfigfile")
    def setUp(self, mock_method):
        super(StackFactoryTest, self).setUp()

    def test_stack_config(self):
        self.assertEqual(5, len(self.stack.tasks_for_role("APP_HOST")))
        self.assertEqual("DEDICATED", self.stack.platform)
        self.assertEqual([NewRelicPythonAddon], registry.objects)

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
        self.assertEqual(90, mock_execute.call_count)


    #@patch("golive.utils.resolve_host")
    #@patch("fabric.tasks._execute")
    #@patch.object(UserSetup, "readfile")
    #def test_deploy_stack(self, mock_readfile, mock_execute, mock_method_resolve):
    #    mock_method_resolve.return_value = "1.2.3.4"
    #    #mock_execute.return_value = "", "", True
    #    mock_execute.return_value = ""
    #    mock_readfile.return_value = "filecontent"
    #    self.stack.do(Stack.DEPLOY)
    #    self.assertEqual(37, mock_execute.call_count)

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


class RegistryTest(TestCase):

    def setUp(self):
        self.registry = golive.addons.registry
        self.addon = NewRelicPythonAddon
        self.registry.registered = []

        super(RegistryTest, self).setUp()

    def test_registry_empty_on_creation(self):
        self.assertIs(0, len(self.registry.objects))
        self.assertIs(0, len(self.registry.objects_active))

    def test_register_object(self):

        self.registry.register(self.addon)

        self.assertIs(1, len(self.registry.objects))
        self.assertIs(self.addon, self.registry.objects[0])
        self.assertIs(self.addon.NAME, self.registry.objects[0].NAME)

    def test_activate_object(self):

        self.registry.register(self.addon)
        self.registry.activate(self.addon.NAME)

        self.assertIs(1, len(self.registry.objects_active))

        self.assertRaises(Exception, self.registry.activate, "TestAddon")

    def tearDown(self):
        reload(golive.addons)
        super(RegistryTest, self).setUp()

class IPTableTest(BaseTestCase):


    @patch.object(Stack, "_read_userconfigfile")
    def setUp(self, mock_method):
        super(TestCase, self).setUp()

        mock_method.return_value = read_userconfigfile()

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

    @patch('golive.stacks.stack.config', {'USER': "usera", 'PROJECT_NAME': "django_example", 'ENV_ID': "TEST"})
    @patch.object(BaseTask, "run")
    @patch.object(BaseTask, "execute_on_host")
    def test_rules_set_on_hosts_new(self, mock_execute_on_host, mock_run):
        mock_run.return_value = {'golive1': '1'}
        mock_execute_on_host.return_value = {'golive1': '0'}

        allow = [(['hosta', 'hostb'], IPTablesSetup.DESTINATION_ALL, "1111")]

        iptables = IPTablesSetup()
        iptables.prepare_rules(allow)
