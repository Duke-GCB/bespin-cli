from __future__ import absolute_import
from unittest import TestCase
from bespin.commands import Commands, Table, WorkflowDetails, JobsList
from mock import patch, call, Mock


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
    @patch('bespin.jobtemplate.JobConfiguration')
    @patch('bespin.commands.print')
    def test_init_job(self, mock_print, mock_job_configuration, mock_bespin_api, mock_config_file):
        mock_outfile = Mock()
        mock_bespin_api.return_value.job_templates_init.return_value = {}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.job_template_init(tag='rnaseq/v1/human', outfile=mock_outfile)

        mock_bespin_api.return_value.job_templates_init.assert_called_with('rnaseq/v1/human')
        mock_outfile.write.assert_called_with('{}\n')

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobTemplateLoader')
    @patch('bespin.commands.print')
    def test_create_job(self, mock_print, mock_job_template_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()
        mock_job_template_loader.return_value.create_job_template.return_value.create_job.return_value = {'job': 1}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.create_job(infile=mock_infile, dry_run=False)

        mock_job_template_loader.assert_called_with(mock_infile)
        mock_print.assert_has_calls([
            call("Created job 1"),
            call("To start this job run `bespin jobs start 1` .")])
        mock_job_template = mock_job_template_loader.return_value.create_job_template.return_value
        mock_job_template.create_job.assert_called_with(mock_bespin_api.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobTemplateLoader')
    @patch('bespin.commands.print')
    def test_create_job_dry_run(self, mock_print, mock_job_template_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()

        commands = Commands(self.version_str, self.user_agent_str)
        commands.create_job(infile=mock_infile, dry_run=True)

        mock_job_template_loader.assert_called_with(mock_infile)
        mock_job_template = mock_job_template_loader.return_value.create_job_template.return_value
        mock_job_template.verify_job.assert_called_with(mock_bespin_api.return_value)
        mock_print.assert_called_with('Job file is valid.')

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobTemplateLoader')
    @patch('bespin.commands.print')
    def test_create_job_with_vm_strategy(self, mock_print, mock_job_template_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()
        mock_job_template_loader.return_value.create_job_template.return_value.create_job.return_value = {'job': 1}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.create_job(infile=mock_infile, dry_run=False, vm_strategy=2)

        mock_job_template_loader.assert_called_with(mock_infile)
        mock_print.assert_has_calls([
            call("Created job 1"),
            call("To start this job run `bespin jobs start 1` .")])
        mock_job_template = mock_job_template_loader.return_value.create_job_template.return_value
        mock_job_template.create_job.assert_called_with(mock_bespin_api.return_value)

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
    def test_workflow_configuration_job_order_show(self, mock_print, mock_bespin_api, mock_config_file):
        mock_outfile = Mock()
        mock_bespin_api.return_value.workflow_configurations_get.return_value = {
            "system_job_order": {
                "threads": 2
            }
        }
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflow_configuration_job_order_show(workflow_configuration_id=2, outfile=mock_outfile)
        mock_outfile.write.assert_called_with('threads: 2\n')


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
            return {'tag': 'exome/v{}'.format(num)}

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
