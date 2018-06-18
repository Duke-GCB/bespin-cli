from __future__ import absolute_import
from unittest import TestCase
from bespin.commands import Commands, Table, WorkflowDetails, JobFile, JobFileLoader, JobQuestionnaire, \
    USER_VALUE_PLACEHOLDER, USER_FILE_PLACEHOLDER, IncompleteJobFileException
from mock import patch, call, Mock
import yaml
import json


class CommandsTestCase(TestCase):
    def setUp(self):
        self.version_str = 'v1'
        self.user_agent_str = 'user_agent'

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.WorkflowDetails')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_workflows_list(self, mock_print, mock_table, mock_workflow_details, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflows_list()
        workflow_details = mock_workflow_details.return_value
        mock_table.assert_called_with(workflow_details.column_names,
                                      workflow_details.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_jobs_list(self, mock_print, mock_table, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.jobs_list()

        mock_table.assert_called_with(["id", "name", "state", "step", "fund_code", "created", "last_updated"],
                                      mock_bespin_api.return_value.jobs_list.return_value)
        mock_print.assert_called_with(mock_table.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobQuestionnaire')
    @patch('bespin.commands.print')
    def test_init_job(self, mock_print, mock_job_questionnaire, mock_bespin_api, mock_config_file):
        mock_outfile = Mock()

        commands = Commands(self.version_str, self.user_agent_str)
        commands.init_job(tag='rnaseq/v1/human', outfile=mock_outfile)

        mock_bespin_api.return_value.questionnaires_list.assert_called_with(tag='rnaseq/v1/human')
        mock_job_file = mock_job_questionnaire.return_value.create_job_file_with_placeholders.return_value
        mock_outfile.write.assert_called_with(mock_job_file.yaml_str.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobFileLoader')
    @patch('bespin.commands.print')
    def test_create_job(self, mock_print, mock_job_file_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()
        mock_job_file_loader.return_value.create_job_file.return_value.create_job.return_value = {'id': 1}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.create_job(infile=mock_infile)

        mock_job_file_loader.assert_called_with(mock_infile)
        mock_print.assert_called_with("Created job 1")

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    def test_start_job_with_token(self, mock_print, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.start_job(job_id=1, token='secret')

        mock_bespin_api.return_value.authorize_job.assert_called_with(1, 'secret')
        mock_bespin_api.return_value.start_job.assert_called_with(1)
        mock_print.assert_has_calls([
            call('Set run token for job 1'),
            call('Started job 1')
        ])

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    def test_start_job_no_token(self, mock_print, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.start_job(job_id=1)

        self.assertFalse(mock_bespin_api.return_value.authorize_job.called)
        mock_bespin_api.return_value.start_job.assert_called_with(1)
        mock_print.assert_has_calls([
            call("Started job 1")
        ])

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    def test_cancel_job(self, mock_print, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.cancel_job(job_id=2)

        self.assertFalse(mock_bespin_api.return_value.authorize_job.called)
        mock_bespin_api.return_value.cancel_job.assert_called_with(2)
        mock_print.assert_has_calls([
            call("Canceled job 2")
        ])

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    def test_restart_job(self, mock_print, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.restart_job(job_id=2)

        self.assertFalse(mock_bespin_api.return_value.authorize_job.called)
        mock_bespin_api.return_value.restart_job.assert_called_with(2)
        mock_print.assert_has_calls([
            call("Restarted job 2")
        ])

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    def test_delete_job(self, mock_print, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.delete_job(job_id=3)

        self.assertFalse(mock_bespin_api.return_value.authorize_job.called)
        mock_bespin_api.return_value.delete_job.assert_called_with(3)
        mock_print.assert_has_calls([
            call("Deleted job 3")
        ])


class TableTestCase(TestCase):
    @patch('bespin.commands.tabulate')
    def test_str(self, mock_tabulate):
        table = Table(column_names=['col_1', 'col_2'], items=[
            {'col_1': 'A', 'col_2': 'B'},
            {'col_1': 'C', 'col_2': 'D'},
        ])
        self.assertEqual(table.__str__(), mock_tabulate.return_value)
        mock_tabulate.assert_called_with([['A', 'B'], ['C', 'D']], headers=['Col 1', 'Col 2'])


class WorkflowDetailsTestCase(TestCase):
    def test_get_column_data(self):
        mock_api = Mock()
        mock_api.workflows_list.return_value = [
            {'id': 1, 'name': 'exome', 'versions': [1, 2]}
        ]
        mock_api.questionnaires_list.return_value = [
            {'tag': 'exome/v2/human'}
        ]
        details = WorkflowDetails(mock_api)
        expected_data = [{'id': 1,
                          'latest version tag': 'exome/v2/human',
                          'name': 'exome',
                          'versions': [1, 2]}]
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 1)
        self.assertEqual(column_data, expected_data)
        mock_api.questionnaires_list.assert_called_with(workflow_version=2)


class JobFileTestCase(TestCase):
    def test_yaml_str(self):
        job_file = JobFile(workflow_tag='sometag', name='myjob', fund_code='001', job_order={})
        yaml_str = job_file.yaml_str()
        expected_dict = {
            'fund_code': '001',
            'job_order': {},
            'name': 'myjob',
            'workflow_tag': 'sometag'
        }
        self.assertEqual(yaml.load(yaml_str), expected_dict)

    def test_create_user_job_order_json(self):
        job_file = JobFile(workflow_tag='sometag', name='myjob', fund_code='001', job_order={
            'myfile': {
                'class': 'File',
                'path': 'dds://project_somepath.txt'
            },
            'myint': 123
        })
        user_job_order = json.loads(job_file.create_user_job_order_json())
        self.assertEqual(user_job_order['myint'], 123)
        self.assertEqual(user_job_order['myfile'], {
            'class': 'File',
            'path': 'dds_project_somepath.txt'
        })

    def test_format_file_path(self):
        self.assertEqual(JobFile.format_file_path('/tmp/data'), '_tmp_data')
        self.assertEqual(JobFile.format_file_path('dds://project/somepath.txt'), 'dds_project_somepath.txt')
        self.assertEqual(JobFile.format_file_path('dds://project/dir/somepath.txt'), 'dds_project_dir_somepath.txt')

    @patch('bespin.commands.DDSFileUtil')
    def test_get_dds_files_details(self, mock_dds_file_util):
        mock_dds_file_util.return_value.find_file_for_path.return_value = 'filedata1'
        job_file = JobFile(workflow_tag='sometag', name='myjob', fund_code='001', job_order={
            'myfile': {
                'class': 'File',
                'path': 'dds://project_somepath.txt'
            },
            'myint': 123
        })
        file_details = job_file.get_dds_files_details()
        self.assertEqual(file_details, [('filedata1', 'dds_project_somepath.txt')])

    @patch('bespin.commands.DDSFileUtil')
    def test_create_job(self, mock_dds_file_util):
        mock_dds_file_util.return_value.find_file_for_path.return_value = 'filedata1'
        mock_api = Mock()
        mock_api.dds_user_credentials_list.return_value = [{'id': 111, 'dds_id': 112}]
        mock_api.questionnaires_list.return_value = [
            {
                'id': 222
            }
        ]
        mock_api.stage_group_post.return_value = {
            'id': 333
        }
        mock_api.job_answer_set_post.return_value = {
            'id': 444
        }
        job_file = JobFile(workflow_tag='sometag', name='myjob', fund_code='001', job_order={
            'myfile': {
                'class': 'File',
                'path': 'dds://project_somepath.txt'
            },
            'myint': 555
        })
        job_file.get_dds_files_details = Mock()
        mock_file = Mock(project_id=666)
        mock_file.id = 777
        job_file.get_dds_files_details.return_value = [[mock_file, 'somepath']]

        job_file.create_job(mock_api)

        mock_api.questionnaires_list.assert_called_with(tag='sometag')
        mock_api.dds_job_input_files_post.assert_called_with(666, 777, 'somepath', 0, 0, 111, stage_group_id=333)
        json_payload = '{"myfile": {"class": "File", "path": "dds_project_somepath.txt"}, "myint": 555}'
        mock_api.job_answer_set_post.assert_called_with('myjob', '001', json_payload, 222, 333)
        mock_api.job_answer_set_create_job.assert_called_with(444)
        mock_dds_file_util.return_value.give_download_permissions.assert_called_with(666, 112)


class JobFileLoaderTestCase(TestCase):
    @patch('bespin.commands.yaml')
    def test_create_job_file(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': 'myjob',
            'fund_code': '0001',
            'job_order': {},
            'workflow_tag': 'mytag',
        }
        job_file_loader = JobFileLoader(Mock())
        job_file_loader.validate_job_file_data = Mock()
        job_file = job_file_loader.create_job_file()

        self.assertEqual(job_file.name, 'myjob')
        self.assertEqual(job_file.fund_code, '0001')
        self.assertEqual(job_file.job_order, {})
        self.assertEqual(job_file.workflow_tag, 'mytag')

    @patch('bespin.commands.yaml')
    def test_validate_job_file_data_ok(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': 'myjob',
            'fund_code': '0001',
            'job_order': {},
            'workflow_tag': 'mytag',
        }
        job_file_loader = JobFileLoader(Mock())
        job_file_loader.validate_job_file_data()

    @patch('bespin.commands.yaml')
    def test_validate_job_file_data_invalid_name_and_fund_code(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': USER_VALUE_PLACEHOLDER,
            'fund_code': USER_VALUE_PLACEHOLDER,
            'job_order': {},
            'workflow_tag': 'mytag',
        }
        job_file_loader = JobFileLoader(Mock())
        with self.assertRaises(IncompleteJobFileException) as raised_exception:
            job_file_loader.validate_job_file_data()
        self.assertEqual(str(raised_exception.exception), 'Please fill in TODO field(s): name, fund_code')

    @patch('bespin.commands.yaml')
    def test_validate_job_file_data_invalid_job_order_params(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': 'myjob',
            'fund_code': '0001',
            'job_order': {
                'intval': USER_VALUE_PLACEHOLDER,
                'fileval': {
                    'class': 'File',
                    'path': USER_FILE_PLACEHOLDER
                },
                'otherint': 123,
                'otherfile': {
                    'class': 'File',
                    'path': 'somefile.txt'
                },
            },
            'workflow_tag': 'mytag',
        }
        job_file_loader = JobFileLoader(Mock())
        with self.assertRaises(IncompleteJobFileException) as raised_exception:
            job_file_loader.validate_job_file_data()
        self.assertEqual(str(raised_exception.exception),
                         'Please fill in TODO field(s): job_order.intval, job_order.fileval')

    def test_value_contains_placeholder(self):
        data = [
            ('somevalue', False),
            (USER_VALUE_PLACEHOLDER, True),
            (USER_FILE_PLACEHOLDER, True),
            ({'class': 'File', 'path': USER_FILE_PLACEHOLDER}, True),
        ]
        for value, expected_result in data:
            self.assertEqual(JobFileLoader.value_contains_placeholder(value), expected_result)

        unknown_class_dict = {
            'class': 'StrangeData',
            'value': 'StrangeValue'
        }
        with self.assertRaises(ValueError) as raised_value_exception:
            JobFileLoader.value_contains_placeholder(unknown_class_dict)
        self.assertEqual(str(raised_value_exception.exception), 'Unknown class StrangeData')


class JobQuestionnaireTestCase(TestCase):
    def test_create_job_file_with_placeholders(self):
        questionnaire = JobQuestionnaire({
            'tag': 'mytag',
            'user_fields_json': '{}'
        })
        job_file = questionnaire.create_job_file_with_placeholders()
        self.assertEqual(job_file.workflow_tag, 'mytag')
        self.assertEqual(job_file.name, USER_VALUE_PLACEHOLDER)
        self.assertEqual(job_file.fund_code, USER_VALUE_PLACEHOLDER)
        self.assertEqual(job_file.job_order, {})

    def test_format_user_fields(self):
        user_fields_str = """
            [
                {"type":"int", "name":"myint"},
                {"type":"string", "name":"mystr"},
                {"type": {"type": "array",  "items":"int"}, "name":"intary"}
            ]
        """
        questionnaire = JobQuestionnaire({
            'tag': 'mytag',
            'user_fields_json': user_fields_str
        })
        user_fields = questionnaire.format_user_fields()
        self.assertEqual(user_fields, {
            'intary': [USER_VALUE_PLACEHOLDER], 'myint': USER_VALUE_PLACEHOLDER, 'mystr': USER_VALUE_PLACEHOLDER
        })

    def test_create_placeholder_value(self):
        questionnaire = JobQuestionnaire({
            'tag': 'mytag',
            'user_fields_json': '{}'
        })
        self.assertEqual(
            questionnaire.create_placeholder_value(type_name='string', is_array=False),
            USER_VALUE_PLACEHOLDER)
        self.assertEqual(
            questionnaire.create_placeholder_value(type_name='int', is_array=False),
            USER_VALUE_PLACEHOLDER)
        self.assertEqual(
            questionnaire.create_placeholder_value(type_name='int', is_array=True),
            [USER_VALUE_PLACEHOLDER])
        self.assertEqual(
            questionnaire.create_placeholder_value(type_name='File', is_array=False),
                {
                    "class": "File",
                    "path": USER_FILE_PLACEHOLDER
                })
        self.assertEqual(
            questionnaire.create_placeholder_value(type_name='File', is_array=True),
                [{
                    "class": "File",
                    "path": USER_FILE_PLACEHOLDER
                }])
        self.assertEqual(
            questionnaire.create_placeholder_value(type_name='NamedFASTQFilePairType', is_array=False),
            {
                "name": USER_VALUE_PLACEHOLDER,
                "file1": {
                    "class": "File",
                    "path": USER_FILE_PLACEHOLDER
                },
                "file2": {
                    "class": "File",
                    "path": USER_FILE_PLACEHOLDER
                }
            })
