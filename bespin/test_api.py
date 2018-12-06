from __future__ import absolute_import
from unittest import TestCase
from bespin.api import BespinApi, BespinException, NotFoundException, requests
from mock import patch, Mock


class BespinApiTestCase(TestCase):
    def setUp(self):
        self.mock_config = Mock(url='someurl', token='sometoken')
        self.mock_user_agent_str = 'agentstr'
        self.expected_headers = {
            'user-agent': 'agentstr',
            'Authorization': 'Token sometoken',
            'content-type': 'application/json'
        }

    @patch('bespin.api.requests')
    def test_get_connection_error(self, mock_requests):
        mock_requests.exceptions.ConnectionError = ValueError
        mock_requests.get.side_effect = ValueError("Some Error")
        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        with self.assertRaises(BespinException) as raised_exception:
            api._get_request('test')
        self.assertEqual(str(raised_exception.exception).strip(), 'Failed to connect to someurl\nSome Error')

    @patch('bespin.api.requests')
    def test_post_connection_error(self, mock_requests):
        mock_requests.exceptions.ConnectionError = ValueError
        mock_requests.post.side_effect = ValueError("Some Error")
        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        with self.assertRaises(BespinException) as raised_exception:
            api._post_request('test', data={})
        self.assertEqual(str(raised_exception.exception).strip(), 'Failed to connect to someurl\nSome Error')

    @patch('bespin.api.requests')
    def test_delete_connection_error(self, mock_requests):
        mock_requests.exceptions.ConnectionError = ValueError
        mock_requests.delete.side_effect = ValueError("Some Error")
        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        with self.assertRaises(BespinException) as raised_exception:
            api._delete_request('test')
        self.assertEqual(str(raised_exception.exception).strip(), 'Failed to connect to someurl\nSome Error')

    @patch('bespin.api.requests')
    def test_jobs_list(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['job1', 'job2']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        jobs = api.jobs_list()

        self.assertEqual(jobs, ['job1', 'job2'])
        mock_requests.get.assert_called_with('someurl/jobs/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflows_list(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['workflow1', 'workflow2']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        workflows = api.workflows_list()

        self.assertEqual(workflows, ['workflow1', 'workflow2'])
        mock_requests.get.assert_called_with('someurl/workflows/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflows_list_with_filter(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['workflow1', 'workflow2']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        workflows = api.workflows_list(tag="mytag")

        self.assertEqual(workflows, ['workflow1', 'workflow2'])
        mock_requests.get.assert_called_with('someurl/workflows/?tag=mytag', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflow_get(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'workflow1'
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        workflow = api.workflow_get('12')

        self.assertEqual(workflow, 'workflow1')
        mock_requests.get.assert_called_with('someurl/workflows/12/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflow_get_for_tag(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['workflow1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        workflow = api.workflow_get_for_tag(workflow_tag='exomeseq')

        self.assertEqual(workflow, 'workflow1')
        mock_requests.get.assert_called_with('someurl/workflows/?tag=exomeseq', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflow_post(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'workflow1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        workflow = api.workflow_post(name="myname", tag="mytag")

        self.assertEqual(workflow, 'workflow1')
        mock_requests.post.assert_called_with('someurl/admin/workflows/', headers=self.expected_headers,
                                              json={'name': 'myname', 'tag': 'mytag'})

    @patch('bespin.api.requests')
    def test_workflow_versions_list(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['workflowversion1', 'workflowversion2']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        items = api.workflow_versions_list()

        self.assertEqual(items, ['workflowversion1', 'workflowversion2'])
        mock_requests.get.assert_called_with('someurl/workflow-versions/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflow_versions_list_with_filter(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['workflowversion1', 'workflowversion2']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        items = api.workflow_versions_list(workflow_tag='exomeseq')

        self.assertEqual(items, ['workflowversion1', 'workflowversion2'])
        mock_requests.get.assert_called_with('someurl/workflow-versions/?workflow__tag=exomeseq',
                                             headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflow_version_get(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'workflowversion1'
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        item = api.workflow_version_get(workflow_version=123)

        self.assertEqual(item, 'workflowversion1')
        mock_requests.get.assert_called_with('someurl/workflow-versions/123/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflow_versions_post(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'worflow_version1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        worflow_version = api.workflow_versions_post(workflow=1, version_num=2, description="my desc", url="someurl2",
                                                 fields=[])
        self.assertEqual(worflow_version, 'worflow_version1')
        expected_post_payload = {
            'workflow': 1,
            'version': 2,
            'description': 'my desc',
            'url': 'someurl2',
            'fields': []
        }
        mock_requests.post.assert_called_with('someurl/admin/workflow-versions/', headers=self.expected_headers,
                                              json=expected_post_payload)

    @patch('bespin.api.requests')
    def test_stage_group_post(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'stagegroup1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        stage_group = api.stage_group_post()
        self.assertEqual(stage_group, 'stagegroup1')

        mock_requests.post.assert_called_with('someurl/job-file-stage-groups/', headers=self.expected_headers, json={})

    @patch('bespin.api.requests')
    def test_dds_job_input_files_post(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'dds-job-input-file1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        dds_input_file = api.dds_job_input_files_post(project_id='123', file_id='456', destination_path='data.txt',
                                                      sequence_group=1, sequence=2,
                                                      dds_user_credentials=4, stage_group_id=5,
                                                      size=1000)

        self.assertEqual(dds_input_file, 'dds-job-input-file1')
        expected_json = {
            'project_id': '123',
            'file_id': '456',
            'destination_path': 'data.txt',
            'sequence_group': 1,
            'sequence': 2,
            'dds_user_credentials': 4,
            'stage_group': 5,
            'size': 1000,
        }
        mock_requests.post.assert_called_with('someurl/dds-job-input-files/', headers=self.expected_headers,
                                              json=expected_json)

    @patch('bespin.api.requests')
    def test_authorize_job(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'job1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        item = api.authorize_job(job_id=123, token='secret')

        self.assertEqual(item, 'job1')
        mock_requests.post.assert_called_with('someurl/jobs/123/authorize/',
                                              headers=self.expected_headers, json={'token': 'secret'})

    @patch('bespin.api.requests')
    def test_start_job(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'job1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        item = api.start_job(job_id=123)

        self.assertEqual(item, 'job1')
        mock_requests.post.assert_called_with('someurl/jobs/123/start/',
                                              headers=self.expected_headers, json={})

    @patch('bespin.api.requests')
    def test_cancel_job(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'job1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        item = api.cancel_job(job_id=123)

        self.assertEqual(item, 'job1')
        mock_requests.post.assert_called_with('someurl/jobs/123/cancel/',
                                              headers=self.expected_headers, json={})

    @patch('bespin.api.requests')
    def test_restart_job(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'job1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        item = api.restart_job(job_id=123)

        self.assertEqual(item, 'job1')
        mock_requests.post.assert_called_with('someurl/jobs/123/restart/',
                                              headers=self.expected_headers, json={})

    @patch('bespin.api.requests')
    def test_delete_job(self, mock_requests):
        mock_response = Mock()
        mock_requests.delete.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        api.delete_job(job_id=123)

        mock_requests.delete.assert_called_with('someurl/jobs/123', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_dds_user_credentials_list(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['agentcred1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        items = api.dds_user_credentials_list()

        self.assertEqual(items, ['agentcred1'])
        mock_requests.get.assert_called_with('someurl/dds-user-credentials/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflow_configurations_list_no_filtering(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['workflowconfig1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        items = api.workflow_configurations_list()
        mock_requests.get.assert_called_with('someurl/workflow-configurations/', headers=self.expected_headers)
        self.assertEqual(items, ['workflowconfig1'])

    @patch('bespin.api.requests')
    def test_workflow_configurations_list_with_filtering(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['workflowconfig1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        items = api.workflow_configurations_list(tag="sometag", workflow=1, workflow_tag="wftag")
        mock_requests.get.assert_called_with('someurl/workflow-configurations/?'
                                             'tag=sometag&'
                                             'workflow=1&'
                                             'workflow__tag=wftag',
                                             headers=self.expected_headers)
        self.assertEqual(items, ['workflowconfig1'])

    @patch('bespin.api.requests')
    def test_workflow_configurations_get(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'workflow1'
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        workflow = api.workflow_configurations_get('12')

        self.assertEqual(workflow, 'workflow1')
        mock_requests.get.assert_called_with('someurl/workflow-configurations/12/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_workflow_configurations_post(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'workflowconfiguration1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        workflow_configuration = api.workflow_configurations_post(tag='myconfig', workflow=1,
                                                                  share_group=2,
                                                                  default_vm_strategy=3,
                                                                  system_job_order={})

        self.assertEqual(workflow_configuration, 'workflowconfiguration1')
        expected_post_payload = {
            'tag': 'myconfig',
            'workflow': 1,
            'share_group': 2,
            'default_vm_strategy': 3,
            'system_job_order': {}
        }
        mock_requests.post.assert_called_with('someurl/admin/workflow-configurations/',
                                              headers=self.expected_headers,
                                              json=expected_post_payload)

    @patch('bespin.api.requests')
    def test_job_templates_init(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'job_template1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        result = api.job_templates_init(tag="exome/v1/human")
        self.assertEqual(result, 'job_template1')
        expected_post_payload = {
            'tag': 'exome/v1/human'
        }
        mock_requests.post.assert_called_with('someurl/job-templates/init/',
                                              headers=self.expected_headers,
                                              json=expected_post_payload)

    @patch('bespin.api.requests')
    def test_job_templates_create_job(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'job_template_filled_in'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        result = api.job_templates_create_job(job_file_payload={'a': '1'})
        self.assertEqual(result, 'job_template_filled_in')
        mock_requests.post.assert_called_with('someurl/job-templates/create-job/',
                                              headers=self.expected_headers,
                                              json={'a': '1'})

    @patch('bespin.api.requests')
    def test_share_groups_list(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['sharegroup1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        response = api.share_groups_list(name='somename')

        self.assertEqual(response, ['sharegroup1'])
        mock_requests.get.assert_called_with('someurl/share-groups/?name=somename', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_share_group_get(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'sharegroup1'
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        response = api.share_group_get(123)

        self.assertEqual(response, 'sharegroup1')
        mock_requests.get.assert_called_with('someurl/share-groups/123/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_share_group_get_for_name(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['sharegroup1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        response = api.share_group_get_for_name(name='myname')

        self.assertEqual(response, 'sharegroup1')
        mock_requests.get.assert_called_with('someurl/share-groups/?name=myname', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_vm_strategies_list(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['vmstrategy1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        response = api.vm_strategies_list(name='somename')

        self.assertEqual(response, ['vmstrategy1'])
        mock_requests.get.assert_called_with('someurl/vm-strategies/?name=somename', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_vm_strategy_get(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'vmstrategy1'
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        response = api.vm_strategy_get(123)

        self.assertEqual(response, 'vmstrategy1')
        mock_requests.get.assert_called_with('someurl/vm-strategies/123/', headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_vm_strategy_get_for_name(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['vmstrategy1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        response = api.vm_strategy_get_for_name(name='myname')

        self.assertEqual(response, 'vmstrategy1')
        mock_requests.get.assert_called_with('someurl/vm-strategies/?name=myname', headers=self.expected_headers)
