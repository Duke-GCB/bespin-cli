from __future__ import absolute_import
from unittest import TestCase
from bespin.commands import Commands, Table, ShortWorkflowDetails, FullWorkflowDetails, JobsList, \
    WorkflowVersionsList, WorkflowConfigurationsList, ShareGroupsList, JobStrategiesList
from bespin.exceptions import UserInputException
from mock import patch, call, Mock


class CommandsTestCase(TestCase):
    def setUp(self):
        self.version_str = 'v1'
        self.user_agent_str = 'user_agent'

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.FullWorkflowDetails')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_workflows_list_latest_versions(self, mock_print, mock_table, mock_workflow_details, mock_bespin_api,
                                            mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflows_list(all_versions=False, short_format=False, tag=None)
        workflow_details = mock_workflow_details.return_value
        mock_table.assert_called_with(workflow_details.column_names,
                                      workflow_details.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)
        mock_workflow_details.assert_called_with(mock_bespin_api.return_value, False, None)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.FullWorkflowDetails')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_workflows_list_all_versions(self, mock_print, mock_table, mock_workflow_details, mock_bespin_api,
                                         mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflows_list(all_versions=True, short_format=False, tag=None)
        workflow_details = mock_workflow_details.return_value
        mock_table.assert_called_with(workflow_details.column_names,
                                      workflow_details.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)
        mock_workflow_details.assert_called_with(mock_bespin_api.return_value, True, None)

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
    @patch('bespin.commands.print')
    def test_job_template_create(self, mock_print, mock_bespin_api, mock_config_file):
        mock_outfile = Mock()
        mock_bespin_api.return_value.job_templates_init.return_value = {}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.job_template_create(tag='rnaseq/v1/human', outfile=mock_outfile)

        mock_bespin_api.return_value.job_templates_init.assert_called_with('rnaseq/v1/human')
        mock_outfile.write.assert_called_with('{}\n')

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobTemplateLoader')
    @patch('bespin.commands.print')
    def test_job_create(self, mock_print, mock_job_template_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()
        mock_job_template_loader.return_value.create_job_template.return_value.create_job.return_value = {'job': 1}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.job_create(job_template_infile=mock_infile)

        mock_job_template_loader.assert_called_with(mock_infile)
        mock_print.assert_has_calls([
            call("Created job 1"),
            call("To start this job run `bespin job start 1` .")])
        mock_job_template = mock_job_template_loader.return_value.create_job_template.return_value
        mock_job_template.create_job.assert_called_with(mock_bespin_api.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobTemplateLoader')
    @patch('bespin.commands.print')
    def test_job_run(self, mock_print, mock_job_template_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()
        mock_job_template_loader.return_value.create_job_template.return_value.create_job.return_value = {'job': 1}

        commands = Commands(self.version_str, self.user_agent_str)
        commands.job_run(job_template_infile=mock_infile, token='mytoken')

        mock_job_template_loader.assert_called_with(mock_infile)
        mock_print.assert_has_calls([
            call("Created job 1"),
            call("Set run token for job 1"),
            call("Started job 1")])
        mock_job_template = mock_job_template_loader.return_value.create_job_template.return_value
        mock_job_template.create_job.assert_called_with(mock_bespin_api.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobTemplateLoader')
    @patch('bespin.commands.print')
    def test_job_validate(self, mock_print, mock_job_template_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()

        commands = Commands(self.version_str, self.user_agent_str)
        commands.job_validate(job_template_infile=mock_infile)

        mock_job_template_loader.assert_called_with(mock_infile)
        mock_job_template = mock_job_template_loader.return_value.create_job_template.return_value
        mock_job_template.validate.assert_called_with(mock_bespin_api.return_value)
        mock_print.assert_called_with('Job file is valid.')

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobTemplateLoader')
    @patch('bespin.commands.print')
    def test_job_validate_exception(self, mock_print, mock_job_template_loader, mock_bespin_api, mock_config_file):
        mock_infile = Mock()
        mock_job_template = mock_job_template_loader.return_value.create_job_template.return_value
        mock_job_template.validate.side_effect = UserInputException("Bad data")

        commands = Commands(self.version_str, self.user_agent_str)
        with self.assertRaises(UserInputException):
            commands.job_validate(job_template_infile=mock_infile)

        mock_print.assert_called_with('ERROR: Job template is invalid.')

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
    def test_workflow_create(self, mock_print, mock_bespin_api, mock_config_file):
        mock_bespin_api.return_value.workflow_post.return_value = {
            'id': 4
        }
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflow_create(name='myname', tag='mytag')
        mock_bespin_api.return_value.workflow_post.assert_called_with('myname', 'mytag')
        mock_print.assert_has_calls([
            call("Created workflow 4.")
        ])

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.WorkflowVersionsList')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_workflow_versions_list(self, mock_print, mock_table, mock_workflow_versions_list, mock_bespin_api,
                                    mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflow_versions_list(workflow_tag='sometag')
        mock_workflow_versions_list.assert_called_with(mock_bespin_api.return_value, 'sometag')
        mock_table.assert_called_with(mock_workflow_versions_list.return_value.column_names,
                                      mock_workflow_versions_list.return_value.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    @patch('bespin.commands.CWLWorkflowVersion')
    def test_workflow_version_create(self, mock_cwl_workflow_version, mock_print, mock_bespin_api, mock_config_file):
        mock_cwl_workflow_version.return_value.create.return_value = {
            'id': 7
        }
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflow_version_create(url='someurl', workflow_type='packed', workflow_path='#main',
                                         version_info_url='infourl', override_version='v3.2', override_tag='tag',
                                         validate=True)
        mock_cwl_workflow_version.assert_called_with('someurl','packed', '#main', 'infourl',override_tag='tag',
                                                     override_version='v3.2',validate=True)
        mock_print.assert_has_calls([
            call("Created workflow version 7.")
        ])

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    @patch('bespin.commands.CWLWorkflowVersion')
    def test_workflow_version_validate(self, mock_cwl_workflow_version, mock_print, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        mock_cwl_workflow_version.return_value.validate_workflow.return_value = Mock(tag='workflow-tag',version='v1.2.3')
        commands.workflow_version_validate(url='someurl', workflow_type='zipped', workflow_path='extracted/workflow.cwl',
                                           expected_tag='workflow-tag', expected_version='v1.2.3')
        mock_cwl_workflow_version.assert_called_with('someurl','zipped','extracted/workflow.cwl', validate=True)
        mock_print.assert_has_calls([
            call("Validated someurl as 'workflow-tag/v1.2.3'")
        ])


    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.WorkflowConfigurationsList')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_workflow_configs_list(self, mock_print, mock_table, mock_workflow_configs_list, mock_bespin_api,
                                    mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflow_configs_list(workflow_tag='sometag')
        mock_workflow_configs_list.assert_called_with(mock_bespin_api.return_value, 'sometag')
        mock_table.assert_called_with(mock_workflow_configs_list.return_value.column_names,
                                      mock_workflow_configs_list.return_value.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    def test_workflow_config_show_job_order(self, mock_print, mock_bespin_api, mock_config_file):
        mock_outfile = Mock()
        mock_bespin_api.return_value.workflow_configurations_list.return_value = [{
            "system_job_order": {
                "threads": 2
            }
        }]
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflow_config_show_job_order(tag="human", workflow_tag="exomeseq", outfile=mock_outfile)
        mock_outfile.write.assert_called_with('threads: 2\n')

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.print')
    @patch('bespin.commands.yaml')
    def test_workflow_config_create(self, mock_yaml, mock_print, mock_bespin_api, mock_config_file):
        mock_yaml.load.return_value = {
            'a': 1
        }
        mock_bespin_api.return_value.workflow_get_for_tag.return_value = {
            'id': 2
        }
        mock_bespin_api.return_value.job_strategy_get_for_name.return_value = {
            'id': 3
        }
        mock_bespin_api.return_value.share_group_get_for_name.return_value = {
            'id': 4
        }
        mock_bespin_api.return_value.workflow_configurations_post.return_value = {
            'id': 5
        }
        commands = Commands(self.version_str, self.user_agent_str)
        commands.workflow_config_create(workflow_tag='exome', default_job_strategy_name='default',
                                        share_group_name='myname', tag='human', joborder_infile=Mock())
        mock_bespin_api.return_value.workflow_configurations_post.assert_called_with('human', 2, 3, 4, {'a': 1})
        mock_print.assert_called_with("Created workflow config 5.")

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.ShareGroupsList')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_share_groups_list(self, mock_print, mock_table, mock_share_groups_list, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.share_groups_list()
        mock_share_groups_list.assert_called_with(mock_bespin_api.return_value)
        mock_table.assert_called_with(mock_share_groups_list.return_value.column_names,
                                      mock_share_groups_list.return_value.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)

    @patch('bespin.commands.ConfigFile')
    @patch('bespin.commands.BespinApi')
    @patch('bespin.commands.JobStrategiesList')
    @patch('bespin.commands.Table')
    @patch('bespin.commands.print')
    def test_job_configs_list(self, mock_print, mock_table, mock_job_strategies_list, mock_bespin_api, mock_config_file):
        commands = Commands(self.version_str, self.user_agent_str)
        commands.job_configs_list()
        mock_job_strategies_list.assert_called_with(mock_bespin_api.return_value)
        mock_table.assert_called_with(mock_job_strategies_list.return_value.column_names,
                                      mock_job_strategies_list.return_value.get_column_data.return_value)
        mock_print.assert_called_with(mock_table.return_value)


class TableTestCase(TestCase):
    @patch('bespin.commands.tabulate')
    def test_str(self, mock_tabulate):
        table = Table(column_names=['col_1', 'col_2'], items=[
            {'col_1': 'A', 'col_2': 'B'},
            {'col_1': 'C', 'col_2': 'D'},
        ])
        self.assertEqual(table.__str__(), mock_tabulate.return_value)
        mock_tabulate.assert_called_with([['A', 'B'], ['C', 'D']], headers=['Col 1', 'Col 2'])


class FullWorkflowDetailsTestCase(TestCase):
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
        details = FullWorkflowDetails(mock_api, all_versions=False, tag=None)
        expected_data = [{'id': 1,
                          'job template tag': 'exome/v2/human',
                          'tag': 'exome',
                          'name': 'exome',
                          'versions': [1, 2]}]
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 1)
        self.assertEqual(column_data, expected_data)
        mock_api.workflow_configurations_list.assert_called_with(workflow_tag='exome')

        mock_api.workflow_configurations_list.reset_mock()
        mock_api.workflow_configurations_list.side_effect = [
            [{'tag': 'human'}],
            [{'tag': 'human'}]
        ]
        details = FullWorkflowDetails(mock_api, all_versions=True, tag=None)
        expected_data = [
            {
                'id': 1,
                'job template tag': 'exome/v1/human',
                'name': 'exome',
                'tag': 'exome',
                'versions': [1, 2]
            },
            {
                'id': 1,
                'job template tag': 'exome/v2/human',
                'name': 'exome',
                'tag': 'exome',
                'versions': [1, 2]
            },
        ]
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 2)
        self.assertEqual(column_data, expected_data)
        mock_api.workflow_configurations_list.assert_has_calls([
            call(workflow_tag='exome'),
            call(workflow_tag='exome'),
        ])

    def test_ignores_workflows_without_versions_when_latest(self):
        mock_api = Mock()
        mock_api.workflows_list.return_value = [
            {'id': 1, 'name': 'no-versions', 'versions': []},
        ]
        details = FullWorkflowDetails(mock_api, all_versions=False, tag=None)
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 0)
        mock_api.questionnaires_list.assert_not_called()

    def test_ignores_workflows_without_versions_when_all(self):
        mock_api = Mock()
        mock_api.workflows_list.return_value = [
            {'id': 1, 'name': 'no-versions', 'versions': []},
        ]
        details = FullWorkflowDetails(mock_api, all_versions=True, tag=None)
        column_data = details.get_column_data()
        self.assertEqual(len(column_data), 0)
        mock_api.questionnaires_list.assert_not_called()


class JobsListTestCase(TestCase):
    def test_column_names(self):
        jobs_list = JobsList(api=Mock())
        self.assertEqual(jobs_list.column_names, ["id", "name", "state", "step", "last_updated", "elapsed_hours",
                                                  "workflow_version_tag"])

    def test_get_workflow_tag(self):
        mock_api = Mock()
        mock_api.workflow_version_get.return_value = {'tag': 'sometag/v1'}
        jobs_list = JobsList(api=mock_api)
        workflow_tag = jobs_list.get_workflow_version_tag(workflow_version_id=123)
        self.assertEqual(workflow_tag, 'sometag/v1')
        mock_api.workflow_version_get.assert_called_with(123)

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
        jobs_list.get_workflow_version_tag = Mock()
        jobs_list.get_workflow_version_tag.return_value = 'sometag/v1'
        jobs_list.get_elapsed_hours = Mock()
        jobs_list.get_elapsed_hours.return_value = 1.2

        column_data = jobs_list.get_column_data()
        self.assertEqual(len(column_data), 1)
        self.assertEqual(column_data[0]['id'], 123)
        self.assertEqual(column_data[0]['workflow_version_tag'], 'sometag/v1')
        self.assertEqual(column_data[0]['elapsed_hours'], 1.2)
        jobs_list.get_workflow_version_tag.assert_called_with(456)
        jobs_list.get_elapsed_hours.assert_called_with(mock_api.jobs_list.return_value[0]['usage'])


class ShortWorkflowDetailsTestCase(TestCase):
    def test_get_column_data(self):
        mock_api = Mock()
        mock_api.workflows_list.return_value = [
            {
                'id': 1,
                'name': 'Exome Seq',
                'tag': 'exome'
            }
        ]
        details = ShortWorkflowDetails(mock_api, tag="exome")
        self.assertEqual(details.column_names, ["id", "name", "tag"])
        self.assertEqual(details.get_column_data(), [
            {'id': 1, 'name': 'Exome Seq', 'tag': 'exome'}
        ])
        mock_api.workflows_list.assert_called_with("exome")


class WorkflowVersionsListTestCase(TestCase):
    def test_get_column_data(self):
        mock_api = Mock()
        mock_api.workflow_versions_list.return_value = [
            {
                'id': 1,
                'description': 'Exome Seq',
                'version': 2,
                'url': 'someurl',
                'tag': 'mytag',
                "workflow": 3,
            }
        ]
        mock_api.workflow_get.return_value = {
            'tag': 'othertag'
        }
        details = WorkflowVersionsList(mock_api, workflow_tag='sometag')
        self.assertEqual(details.column_names, ["id", "description", "workflow tag", "version", "url"])
        self.assertEqual(details.get_column_data(), [
            {
                'description': 'Exome Seq',
                'id': 1,
                'tag': 'mytag',
                'url': 'someurl',
                'version': 2,
                'workflow': 3,
                'workflow tag': 'othertag'
            }
        ])


class WorkflowConfigurationsListTestCase(TestCase):
    def test_get_column_data(self):
        mock_api = Mock()
        mock_api.workflow_configurations_list.return_value = [
            {
                'id': 8,
                'share_group': 1,
                'workflow': 2,
                'default_job_strategy': 3,
            }
        ]
        mock_api.workflow_get.return_value = {
            'tag': 'exomeseq'
        }
        mock_api.share_group_get.return_value = {
            'name': 'Informatics'
        }
        mock_api.job_strategy_get.return_value = {
            'name': 'default'
        }
        wfc_list = WorkflowConfigurationsList(mock_api, workflow_tag='mytag')
        self.assertEqual(wfc_list.column_names, ['id', 'tag', 'workflow', 'share group', 'Default Job Strategy'])
        self.assertEqual(wfc_list.get_column_data(), [
            {
                'Default Job Strategy': 'default',
                'default_job_strategy': 3,
                'id': 8,
                'share group': 'Informatics',
                'share_group': 1,
                'workflow': 'exomeseq'
            }
        ])


class ShareGroupsListTestCase(TestCase):
    def test_get_column_data(self):
        mock_api = Mock()
        mock_api.share_groups_list.return_value = [
            {'id': 1, 'name': "GroupName", "email": "com@com.com"}
        ]
        sg_list = ShareGroupsList(mock_api)
        self.assertEqual(sg_list.column_names, ["id", "name", "email"])
        self.assertEqual(sg_list.get_column_data(), [
            {'id': 1, 'name': "GroupName", "email": "com@com.com"}
        ])


class JobStrategiesListTestCase(TestCase):
    def test_get_column_data(self):
        mock_api = Mock()
        mock_api.job_strategies_list.return_value = [
            {
                'id': 4,
                'name': 'default',
                'volume_size_factor': 2,
                'volume_size_base': 10,
                'job_flavor': {
                    'name': 'm1.large',
                    'cpus': 22,
                    'memory': '1MB',
                },
            }
        ]
        job_strategies_list = JobStrategiesList(mock_api)
        self.assertEqual(job_strategies_list.column_names, ['id', 'name', 'type', 'cpus', 'memory', 'volume size (g)'])
        self.assertEqual(job_strategies_list.get_column_data(), [
            {
                'cpus': 22,
                'memory': '1MB',
                'id': 4,
                'name': 'default',
                'type': 'm1.large',
                'job_flavor': {'cpus': 22, 'name': 'm1.large', 'memory': '1MB'},
                'volume size (g)': '2 x Input Data Size + 10',
                'volume_size_base': 10,
                'volume_size_factor': 2
            }
        ])
