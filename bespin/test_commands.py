from __future__ import absolute_import
from unittest import TestCase
from bespin.commands import Commands, Table, WorkflowDetails, JobFile, JobFileLoader, JobQuestionnaire
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

        mock_bespin_api.return_value.questionnaires_list.assert_called_with(slug='rnaseq/v1/human')
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
