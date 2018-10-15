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
    def test_workflow_versions_list(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['workflowversion1', 'workflowversion2']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        items = api.workflow_versions_list()

        self.assertEqual(items, ['workflowversion1', 'workflowversion2'])
        mock_requests.get.assert_called_with('someurl/workflow-versions/', headers=self.expected_headers)

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
    def test_questionnaires_list(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = ['questionnaire1']
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        items = api.questionnaires_list()

        self.assertEqual(items, ['questionnaire1'])
        mock_requests.get.assert_called_with('someurl/job-questionnaires/', headers=self.expected_headers)

        api.questionnaires_list(workflow_version=1)
        mock_requests.get.assert_called_with('someurl/job-questionnaires/?workflow_version=1',
                                             headers=self.expected_headers)

        api.questionnaires_list(tag='exomeseq/v1/human')
        mock_requests.get.assert_called_with('someurl/job-questionnaires/?tag=exomeseq/v1/human',
                                             headers=self.expected_headers)

        api.questionnaires_list(workflow_version=1, tag='exomeseq/v1/human')
        mock_requests.get.assert_called_with('someurl/job-questionnaires/?workflow_version=1&tag=exomeseq/v1/human',
                                             headers=self.expected_headers)

    @patch('bespin.api.requests')
    def test_questionnaire_get(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'questionnaire1'
        mock_requests.get.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        item = api.questionnaire_get(questionnaire_id=123)
        self.assertEqual(item, 'questionnaire1')
        mock_requests.get.assert_called_with('someurl/job-questionnaires/123/', headers=self.expected_headers)

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
    def test_job_answer_set_post(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'job-answer-set1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        item = api.job_answer_set_post(job_name='somejob', fund_code='001', user_job_order_json={}, questionnaire_id=2,
                                       stage_group_id=3)

        self.assertEqual(item, 'job-answer-set1')
        expected_json = {
            'job_name': 'somejob',
            'fund_code': '001',
            'user_job_order_json': {},
            'questionnaire': 2,
            'stage_group': 3
        }
        mock_requests.post.assert_called_with('someurl/job-answer-sets/', headers=self.expected_headers,
                                              json=expected_json)

    @patch('bespin.api.requests')
    def test_job_answer_set_create_job(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = 'job1'
        mock_requests.post.return_value = mock_response

        api = BespinApi(config=self.mock_config, user_agent_str=self.mock_user_agent_str)
        item = api.job_answer_set_create_job(job_answer_set_id=123)

        self.assertEqual(item, 'job1')
        mock_requests.post.assert_called_with('someurl/job-answer-sets/123/create-job/',
                                              headers=self.expected_headers, json={})

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
