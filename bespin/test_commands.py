from __future__ import absolute_import
from unittest import TestCase
from bespin.commands import Commands, Table, WorkflowDetails, JobFile, JobFileLoader, JobConfiguration, \
    STRING_VALUE_PLACEHOLDER, INT_VALUE_PLACEHOLDER, FILE_PLACEHOLDER, IncompleteJobFileException, \
    JobOrderWalker, JobOrderPlaceholderCheck, JobOrderFormatFiles, JobOrderFileDetails, JobsList
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
    def test_workflows_list_latest_versions(self, mock_print, mock_table, mock_workflow_details, mock_bespin_api,
                                            mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflows_list(all_versions=False)
        workflow_details = mock_workflow_details.return_value
        mock_table.assert_called_with(workflow_details.column_names,
                                      workflow_details.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)
        mock_workflow_details.assert_called_with(mock_bespin_api.return_value, False)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.WorkflowDetails')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_workflows_list_all_versions(self, mock_print, mock_table, mock_workflow_details, mock_bespin_api,
                                         mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflows_list(all_versions=True)
        workflow_details = mock_workflow_details.return_value
        mock_table.assert_called_with(workflow_details.column_names,
                                      workflow_details.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)
        mock_workflow_details.assert_called_with(mock_bespin_api.return_value, True)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobsList')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_jobs_list(self, mock_print, mock_table, mock_jobs_list, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.jobs_list()
        mock_jobs_list.assert_called_with(mock_bespin_api.return_value)
        mock_table.assert_called_with(mock_jobs_list.return_value.column_names,
                                      mock_jobs_list.return_value.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobConfiguration')
    @patch('bespin.commands.print')
    def test_init_job(self, mock_print, mock_job_configuration, mock_bespin_api, mock_config_file):
        mock_outfile = Mock()
        mock_bespin_api.return_value.init_job_file.return_value = {}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.init_job(tag='rnaseq/v1/human', outfile=mock_outfile)

        mock_bespin_api.return_value.init_job_file.assert_called_with('rnaseq/v1/human')
        mock_outfile.write.assert_called_with('{}\n')

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobFileLoader')
    @patch('bespin.commands.print')
    def test_create_job(self, mock_print, mock_job_file_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()
        mock_job_file_loader.return_value.create_job_file.return_value.create_job.return_value = {'id': 1}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.create_job(infile=mock_infile, dry_run=False, share_group=1)

        mock_job_file_loader.assert_called_with(mock_infile)
        mock_print.assert_has_calls([
            call("Created job 1"),
            call("To start this job run `bespin jobs start 1` .")])
        mock_job_file = mock_job_file_loader.return_value.create_job_file.return_value
        mock_job_file.create_job.assert_called_with(mock_bespin_api.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobFileLoader')
    @patch('bespin.commands.print')
    def test_create_job_dry_run(self, mock_print, mock_job_file_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()

        commands = Commands(self.version_str, self.user_agent_str)
        commands.create_job(infile=mock_infile, dry_run=True, share_group=1)

        mock_job_file_loader.assert_called_with(mock_infile)
        mock_job_file = mock_job_file_loader.return_value.create_job_file.return_value
        mock_job_file.verify_job.assert_called_with(mock_bespin_api.return_value)
        mock_print.assert_called_with('Job file is valid.')

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobFileLoader')
    @patch('bespin.commands.print')
    def test_create_job_with_vm_strategy(self, mock_print, mock_job_file_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()
        mock_job_file_loader.return_value.create_job_file.return_value.create_job.return_value = {'id': 1}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.create_job(infile=mock_infile, dry_run=False, share_group=1, vm_strategy=2)

        mock_job_file_loader.assert_called_with(mock_infile)
        mock_print.assert_has_calls([
            call("Created job 1"),
            call("To start this job run `bespin jobs start 1` .")])
        mock_job_file = mock_job_file_loader.return_value.create_job_file.return_value
        mock_job_file.create_job.assert_called_with(mock_bespin_api.return_value)

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

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    def test_workflow_configuration_show(self, mock_print, mock_bespin_api, mock_config_file):
        mock_outfile = Mock()
        mock_bespin_api.return_value.workflow_configurations_list.return_value = [
            {}
        ]
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflow_configuration_show(tag='mytag', outfile=mock_outfile)
        mock_outfile.write.assert_called_with('{}\n')


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
        def make_tag(num):
            return {'tag': 'v{}'.format(num)}

        mock_api = Mock()
        mock_api.workflows_list.return_value = [
            {'id': 1, 'name': 'exome', 'versions': [1, 2], 'tag': 'exome'}
        ]
        mock_api.workflow_version_get = make_tag
        mock_api.workflow_configurations_list.return_value = [
            {'tag': 'human'}
        ]
        details = WorkflowDetails(mock_api, all_versions=False)
        expected_data = [{'id': 1,
                          'version tag': 'exome/v2/human',
                          'tag': 'exome',
                          'name': 'exome',
                          'versions': [1, 2]}]
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 1)
        self.assertEqual(column_data, expected_data)
        mock_api.workflow_configurations_list.assert_called_with(workflow_version=2)

        mock_api.workflow_configurations_list.reset_mock()
        mock_api.workflow_configurations_list.side_effect = [
            [{'tag': 'human'}],
            [{'tag': 'human'}]
        ]
        details = WorkflowDetails(mock_api, all_versions=True)
        expected_data = [
            {
                'id': 1,
                'version tag': 'exome/v1/human',
                'name': 'exome',
                'tag': 'exome',
                'versions': [1, 2]
            },
            {
                'id': 1,
                'version tag': 'exome/v2/human',
                'name': 'exome',
                'tag': 'exome',
                'versions': [1, 2]
            },
        ]
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 2)
        self.assertEqual(column_data, expected_data)
        mock_api.workflow_configurations_list.assert_has_calls([
            call(workflow_version=1),
            call(workflow_version=2),
        ])

    def test_ignores_workflows_without_versions_when_latest(self):
        mock_api = Mock()
        mock_api.workflows_list.return_value = [
            {'id': 1, 'name': 'no-versions', 'versions': []},
        ]
        details = WorkflowDetails(mock_api, all_versions=False)
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 0)
        mock_api.questionnaires_list.assert_not_called()

    def test_ignores_workflows_without_versions_when_all(self):
        mock_api = Mock()
        mock_api.workflows_list.return_value = [
            {'id': 1, 'name': 'no-versions', 'versions': []},
        ]
        details = WorkflowDetails(mock_api, all_versions=True)
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 0)
        mock_api.questionnaires_list.assert_not_called()


class JobFileTestCase(TestCase):
    def test_to_dict(self):
        job_file = JobFile(workflow_tag='sometag', name='myjob', fund_code='001', job_order={})
        expected_dict = {
            'fund_code': '001',
            'job_order': {},
            'name': 'myjob',
            'workflow_tag': 'sometag'
        }
        self.assertEqual(job_file.to_dict(), expected_dict)

    def test_create_user_job_order_json(self):
        job_file = JobFile(workflow_tag='sometag', name='myjob', fund_code='001', job_order={
            'myfile': {
                'class': 'File',
                'path': 'dds://project/somepath.txt'
            },
            'my_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'my_url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
            'myint': 123,
            'myfileary': [
                {
                    'class': 'File',
                    'path': 'dds://project/somepath1.txt'
                },
                {
                    'class': 'File',
                    'path': 'dds://project/somepath2.txt'
                },
            ],
            'myfastq_pairs': [
                {'file1':
                     {'class': 'File',
                      'path': 'dds://myproject/rawData/SAAAA_R1_001.fastq.gz'
                      },
                 'file2': {
                     'class': 'File',
                     'path': 'dds://myproject/rawData/SAAAA_R2_001.fastq.gz'
                 },
                 'name': 'Sample1'}]
        })
        user_job_order = job_file.create_user_job_order()
        self.assertEqual(user_job_order['myint'], 123)
        self.assertEqual(user_job_order['myfile'], {
            'class': 'File',
            'path': 'dds_project_somepath.txt'
        })
        self.assertEqual(user_job_order['myfileary'], [
            {
                'class': 'File',
                'path': 'dds_project_somepath1.txt'
            },
            {
                'class': 'File',
                'path': 'dds_project_somepath2.txt'
            },
        ])
        self.assertEqual(user_job_order['myfastq_pairs'], [
            {'file1':
                 {'class': 'File',
                  'path': 'dds_myproject_rawData_SAAAA_R1_001.fastq.gz'
                  },
             'file2': {
                 'class': 'File',
                 'path': 'dds_myproject_rawData_SAAAA_R2_001.fastq.gz'
             },
             'name': 'Sample1'}])
        self.assertEqual(user_job_order['my_path_file'], {
            'class': 'File',
            'path': '/tmp/data.txt'
        }, "Plain file paths should not be modified.")
        self.assertEqual(user_job_order['my_url_file'], {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
        }, "URL file paths should not be modified.")

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
        mock_api.workflow_configurations_list.return_value = [
            {
                'id': 222
            }
        ]
        mock_api.stage_group_post.return_value = {
            'id': 333
        }
        job_file = JobFile(workflow_tag='sometag', name='myjob', fund_code='001', job_order={
            'myfile': {
                'class': 'File',
                'path': 'dds://project_somepath.txt'
            },
            'myint': 555
        })
        job_file.get_dds_files_details = Mock()
        mock_file = Mock(project_id=666, current_version={'upload': {'size': 4002}})
        mock_file.id = 777
        job_file.get_dds_files_details.return_value = [[mock_file, 'somepath']]

        job_file.create_job(mock_api)

        mock_api.workflow_configurations_list.assert_called_with(tag='sometag')
        mock_api.dds_job_input_files_post.assert_called_with(666, 777, 'somepath', 0, 0, 111, stage_group_id=333,
                                                             size=4002)
        mock_api.create_job.assert_called_with({
            'name': 'myjob',
            'fund_code': '001',
            'job_order': {
                'myfile': {
                    'class': 'File',
                    'path': 'dds_project_somepath.txt'
                },
                'myint': 555
            },
            'workflow_tag': 'sometag',
            'stage_group': 333
        })
        mock_dds_file_util.return_value.give_download_permissions.assert_called_with(666, 112)

    @patch('bespin.commands.DDSFileUtil')
    @patch('bespin.commands.JobOrderFormatFiles')
    def test_verify_job(self, mock_job_order_format_files, mock_dds_file_util):
        mock_dds_file_util.return_value.find_file_for_path.return_value = 'filedata1'
        mock_api = Mock()
        mock_api.dds_user_credentials_list.return_value = [{'id': 111, 'dds_id': 112}]
        mock_api.workflow_configurations_list.return_value = [
            {
                'id': 222
            }
        ]
        mock_api.stage_group_post.return_value = {
            'id': 333
        }
        job_order = {
            'myfile': {
                'class': 'File',
                'path': 'dds://project_somepath.txt'
            },
            'myint': 555
        }
        job_file = JobFile(workflow_tag='sometag', name='myjob', fund_code='001', job_order=job_order)
        job_file.get_dds_files_details = Mock()
        mock_file = Mock(project_id=666, current_version={'upload': {'size': 4002}})
        mock_file.id = 777
        job_file.get_dds_files_details.return_value = [[mock_file, 'somepath']]

        job_file.verify_job(mock_api)
        mock_api.workflow_configurations_list.assert_called_with(tag='sometag')
        job_file.get_dds_files_details.assert_called_with()
        mock_job_order_format_files.return_value.walk.assert_called_with(job_order)


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
        job_file = job_file_loader.create_job_file(share_group_id=1, vm_strategy_id=2)

        self.assertEqual(job_file.name, 'myjob')
        self.assertEqual(job_file.fund_code, '0001')
        self.assertEqual(job_file.job_order, {})
        self.assertEqual(job_file.workflow_tag, 'mytag')
        self.assertEqual(job_file.share_group_id, 1)
        self.assertEqual(job_file.job_vm_strategy_id, 2)

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
            'name': STRING_VALUE_PLACEHOLDER,
            'fund_code': STRING_VALUE_PLACEHOLDER,
            'job_order': {},
            'workflow_tag': 'mytag',
        }
        job_file_loader = JobFileLoader(Mock())
        with self.assertRaises(IncompleteJobFileException) as raised_exception:
            job_file_loader.validate_job_file_data()
        self.assertEqual(str(raised_exception.exception),
                         'Please fill in placeholder values for field(s): fund_code, name')

    @patch('bespin.commands.yaml')
    def test_validate_job_file_data_invalid_job_order_params(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': 'myjob',
            'fund_code': '0001',
            'job_order': {
                'intval': INT_VALUE_PLACEHOLDER,
                'fileval': {
                    'class': 'File',
                    'path': FILE_PLACEHOLDER
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
                         'Please fill in placeholder values for field(s): job_order.fileval, job_order.intval')


class JobConfigurationTestCase(TestCase):
    def test_create_job_file_with_placeholders(self):
        configuration = JobConfiguration({
            'tag': 'mytag',
            'user_fields': {}
        })
        job_file = configuration.create_job_file_with_placeholders()
        self.assertEqual(job_file.workflow_tag, 'mytag')
        self.assertEqual(job_file.name, STRING_VALUE_PLACEHOLDER)
        self.assertEqual(job_file.fund_code, STRING_VALUE_PLACEHOLDER)
        self.assertEqual(job_file.job_order, {})

    def test_format_user_fields(self):
        user_fields = [
            {"type": "int", "name": "myint"},
            {"type": "string", "name": "mystr"},
            {"type": {"type": "array",  "items": "int"}, "name": "intary"}
        ]
        configuration = JobConfiguration({
            'tag': 'mytag',
            'user_fields': user_fields,
        })
        user_fields = configuration.format_user_fields()
        self.assertEqual(user_fields, {
            'intary': [INT_VALUE_PLACEHOLDER], 'myint': INT_VALUE_PLACEHOLDER, 'mystr': STRING_VALUE_PLACEHOLDER
        })

    def test_create_placeholder_value(self):
        configuration = JobConfiguration({
            'tag': 'mytag',
            'user_fields': {}
        })
        self.assertEqual(
            configuration.create_placeholder_value(type_name='string', is_array=False),
            STRING_VALUE_PLACEHOLDER)
        self.assertEqual(
            configuration.create_placeholder_value(type_name='int', is_array=False),
            INT_VALUE_PLACEHOLDER)
        self.assertEqual(
            configuration.create_placeholder_value(type_name='int', is_array=True),
            [INT_VALUE_PLACEHOLDER])
        self.assertEqual(
            configuration.create_placeholder_value(type_name='File', is_array=False),
            {
                "class": "File",
                "path": FILE_PLACEHOLDER
            })
        self.assertEqual(
            configuration.create_placeholder_value(type_name='File', is_array=True),
            [{
                "class": "File",
                "path": FILE_PLACEHOLDER
            }])
        self.assertEqual(
            configuration.create_placeholder_value(type_name='NamedFASTQFilePairType', is_array=False),
            {
                "name": STRING_VALUE_PLACEHOLDER,
                "file1": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                },
                "file2": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                }
            })
        self.assertEqual(
            configuration.create_placeholder_value(type_name='NamedFASTQFilePairType', is_array=True),
            [{
                "name": STRING_VALUE_PLACEHOLDER,
                "file1": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                },
                "file2": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                }
            }])


class JobOrderWalkerTestCase(TestCase):
    def test_walk(self):
        walker = JobOrderWalker()
        walker.on_class_value = Mock()
        walker.on_simple_value = Mock()
        walker.walk({
            'color': 'red',
            'weight': 123,
            'file1': {
                'class': 'File',
                'path': 'somepath'
            },
            'file_ary': [
                {
                    'class': 'File',
                    'path': 'somepath1'
                }, {
                    'class': 'File',
                    'path': 'somepath2'
                },
            ],
            'nested': {
                'a': [{
                    'class': 'File',
                    'path': 'somepath3'
                }]
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        })

        walker.on_simple_value.assert_has_calls([
            call('color', 'red'),
            call('weight', 123),
        ])
        walker.on_class_value.assert_has_calls([
            call('file1', {'class': 'File', 'path': 'somepath'}),
            call('file_ary', {'class': 'File', 'path': 'somepath1'}),
            call('file_ary', {'class': 'File', 'path': 'somepath2'}),
            call('nested', {'class': 'File', 'path': 'somepath3'}),
        ])

    def test_format_file_path(self):
        data = [
            # input    expected
            ('https://placeholder.data/stuff/data.txt', 'https://placeholder.data/stuff/data.txt'),
            ('dds://myproject/rawData/SAAAA_R1_001.fastq.gz', 'dds_myproject_rawData_SAAAA_R1_001.fastq.gz'),
            ('dds://project/somepath.txt', 'dds_project_somepath.txt'),
            ('dds://project/dir/somepath.txt', 'dds_project_dir_somepath.txt'),
        ]
        for input_val, expected_val in data:
            self.assertEqual(JobOrderWalker.format_file_path(input_val), expected_val)


class JobOrderPlaceholderCheckTestCase(TestCase):
    def test_walk(self):
        job_order = {
            'good_str': 'a',
            'bad_str': STRING_VALUE_PLACEHOLDER,
            'good_int': 123,
            'bad_int': INT_VALUE_PLACEHOLDER,
            'good_file': {
                'class': 'File',
                'path': 'somepath.txt',
            },
            'bad_file': {
                'class': 'File',
                'path': FILE_PLACEHOLDER,
            },
            'good_str_ary': ['a', 'b', 'c'],
            'bad_str_ary': ['a', STRING_VALUE_PLACEHOLDER, 'c'],
            'good_file_ary': [{
                'class': 'File',
                'path': 'somepath.txt',
            }],
            'bad_file_ary': [{
                'class': 'File',
                'path': FILE_PLACEHOLDER,
            }],
            'good_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': 'somepath.txt',
                }
            },
            'bad_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': FILE_PLACEHOLDER,
                }
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        }
        expected_keys = [
            'bad_str', 'bad_int', 'bad_file', 'bad_str_ary', 'bad_file_ary', 'bad_file_dict',
        ]

        checker = JobOrderPlaceholderCheck()
        checker.walk(job_order)

        self.assertEqual(checker.keys_with_placeholders, set(expected_keys))


class JobOrderFormatFilesTestCase(TestCase):
    def test_walk(self):
        job_order = {
            'good_str': 'a',
            'good_int': 123,
            'good_file': {
                'class': 'File',
                'path': 'dds://project1/data/somepath.txt',
            },
            'good_str_ary': ['a', 'b', 'c'],
            'good_file_ary': [{
                'class': 'File',
                'path': 'dds://project2/data/somepath2.txt',
            }],
            'good_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': 'dds://project3/data/other/somepath.txt',
                }
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        }

        formatter = JobOrderFormatFiles()
        formatter.walk(job_order)

        self.assertEqual(job_order['good_str'], 'a')
        self.assertEqual(job_order['good_int'], 123)
        self.assertEqual(job_order['good_file'],
                         {'class': 'File', 'path': 'dds_project1_data_somepath.txt'})
        self.assertEqual(job_order['good_str_ary'], ['a', 'b', 'c'])
        self.assertEqual(job_order['good_file_ary'],
                         [{'class': 'File', 'path': 'dds_project2_data_somepath2.txt'}])
        self.assertEqual(job_order['good_file_dict'],
                         {'stuff': {'class': 'File', 'path': 'dds_project3_data_other_somepath.txt'}})


class JobOrderFileDetailsTestCase(TestCase):
    @patch('bespin.commands.DDSFileUtil')
    def test_walk(self, mock_dds_file_util):
        mock_dds_file_util.return_value.find_file_for_path.return_value = 'ddsfiledata'
        job_order = {
            'good_str': 'a',
            'good_int': 123,
            'good_file': {
                'class': 'File',
                'path': 'dds://project1/data/somepath.txt',
            },
            'good_str_ary': ['a', 'b', 'c'],
            'good_file_ary': [{
                'class': 'File',
                'path': 'dds://project2/data/somepath2.txt',
            }],
            'good_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': 'dds://project3/data/other/somepath.txt',
                }
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        }
        expected_dds_file_info = [
            ('ddsfiledata', 'dds_project1_data_somepath.txt'),
            ('ddsfiledata', 'dds_project2_data_somepath2.txt'),
            ('ddsfiledata', 'dds_project3_data_other_somepath.txt')
        ]

        details = JobOrderFileDetails()
        details.walk(job_order)

        self.assertEqual(details.dds_files, expected_dds_file_info)


class JobsListTestCase(TestCase):
    def test_column_names(self):
        jobs_list = JobsList(api=Mock())
        self.assertEqual(jobs_list.column_names, ["id", "name", "state", "step", "last_updated", "elapsed_hours",
                                                  "workflow_tag"])

    def test_get_workflow_tag(self):
        mock_api = Mock()
        mock_api.workflow_configurations_list.return_value = [{'tag': 'sometag/v1/human'}]
        jobs_list = JobsList(api=mock_api)
        workflow_tag = jobs_list.get_workflow_tag(workflow_version=123)
        self.assertEqual(workflow_tag, 'sometag/v1/human')
        mock_api.workflow_configurations_list.assert_called_with(workflow_version=123)

    def test_get_elapsed_hours(self):
        mock_api = Mock()
        jobs_list = JobsList(api=mock_api)
        cpu_hours = jobs_list.get_elapsed_hours({'vm_hours': 1.25})
        self.assertEqual(cpu_hours, 1.3)
        cpu_hours = jobs_list.get_elapsed_hours({'vm_hours': 0.0})
        self.assertEqual(cpu_hours, 0.0)

    def test_get_column_data(self):
        mock_api = Mock()
        mock_api.jobs_list.return_value = [{'id': 123, 'workflow_version': 456, 'usage': {'cpu_hours': 1.2}}]
        jobs_list = JobsList(api=mock_api)
        jobs_list.get_workflow_tag = Mock()
        jobs_list.get_workflow_tag.return_value = 'sometag/v1/human'
        jobs_list.get_elapsed_hours = Mock()
        jobs_list.get_elapsed_hours.return_value = 1.2

        column_data = jobs_list.get_column_data()
        self.assertEqual(len(column_data), 1)
        self.assertEqual(column_data[0]['id'], 123)
        self.assertEqual(column_data[0]['workflow_tag'], 'sometag/v1/human')
        self.assertEqual(column_data[0]['elapsed_hours'], 1.2)
        jobs_list.get_workflow_tag.assert_called_with(456)
        jobs_list.get_elapsed_hours.assert_called_with(mock_api.jobs_list.return_value[0]['usage'])
