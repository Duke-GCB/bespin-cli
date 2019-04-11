from __future__ import absolute_import
from unittest import TestCase
from bespin.workflow import CWLWorkflowVersion, BespinWorkflowLoader, BespinWorkflowValidator, BespinWorkflowParser
from mock import patch, call, Mock


class BespinWorkflowLoaderTestCase(TestCase):
    pass


class BespinWorkflowParserTestCase(TestCase):
    pass


class BespinWorkflowValidatorTestCase(TestCase):
    pass


class CWLWorkflowVersionTestCase(TestCase):
    def setUp(self):
        self.cwl_workflow_version = CWLWorkflowVersion(url='someurl',
                                                       workflow_type='packed',
                                                       workflow_path='#main',
                                                       version_info_url='infourl')

    @patch('bespin.workflow.CWLWorkflowVersion.validate_workflow')
    def test_create(self, mock_validate_workflow):
        # Create should validate the workflow, get the id, and call api.workflow_verisons_post
        mock_parser = Mock(version='v1', tag='wf-tag', input_fields=['a',], description='SomeDesc')
        mock_validate_workflow.return_value = mock_parser
        mock_api = Mock()
        mock_api.workflow_get_for_tag.return_value = {'id': 1}
        self.cwl_workflow_version.create(mock_api)
        mock_api.workflow_get_for_tag.assert_called_with('wf-tag')
        mock_api.workflow_versions_post.assert_called_with(workflow=1,
                                                           version='v1',
                                                           workflow_type='packed',
                                                           workflow_path='#main',
                                                           version_info_url='infourl',
                                                           description='SomeDesc',
                                                           url="someurl",
                                                           fields=['a',])

    @patch('bespin.workflow.BespinWorkflowLoader')
    @patch('bespin.workflow.BespinWorkflowParser')
    @patch('bespin.workflow.BespinWorkflowValidator')
    def test_load_and_parse_workflow(self, mock_validator, mock_parser, mock_loader):
        expected_tag = 'expected-tag'
        expected_version = 've.x.p'
        mock_load = mock_loader.return_value.load
        loaded_and_parsed = self.cwl_workflow_version._load_and_parse_workflow(expected_tag, expected_version)

        # The loader should be instantiated with the workflow and load() called
        self.assertEqual(mock_loader.call_args, call(self.cwl_workflow_version))
        self.assertTrue(mock_load.called)

        # The parser should be instantiated with the loaded workflow
        self.assertEqual(mock_parser.call_args, call(mock_load.return_value))

        # The validator should also be instantiated with the loaded workflow
        self.assertEqual(mock_validator.call_args, call(mock_load.return_value))

        self.assertTrue(mock_validator.return_value.validate.called)
        self.assertEqual(mock_validator.return_value.validate.call_args, call(expected_tag, expected_version))
        self.assertEqual(mock_parser.return_value, loaded_and_parsed)

    @patch('bespin.workflow.BespinWorkflowLoader')
    @patch('bespin.workflow.BespinWorkflowParser')
    @patch('bespin.workflow.BespinWorkflowValidator')
    def test_load_and_parse_workflow_no_validate(self, mock_validator, mock_parser, mock_loader):
        self.cwl_workflow_version.validate = False
        self.cwl_workflow_version._load_and_parse_workflow()
        self.assertFalse(mock_validator.return_value.validate.called)

    @patch('bespin.workflow.BespinWorkflowLoader')
    @patch('bespin.workflow.BespinWorkflowParser')
    @patch('bespin.workflow.BespinWorkflowValidator')
    def test_load_and_parse_override(self, mock_validator, mock_parser, mock_loader):
        self.cwl_workflow_version.override_tag = 'override-tag'
        self.cwl_workflow_version.override_version = 'override-version'
        mock_parser.return_value.tag = 'original-tag'
        mock_parser.return_value.version = 'original-version'
        parsed = self.cwl_workflow_version._load_and_parse_workflow()
        self.assertEqual(parsed.tag, 'override-tag')
        self.assertEqual(parsed.version, 'override-version')

    @patch('bespin.workflow.CWLWorkflowVersion._load_and_parse_workflow')
    def test_validate_workflow(self, mock_load_and_parse_workflow):
        expected_tag = 'expected-tag'
        expected_version = 've.x.p'
        validated = self.cwl_workflow_version.validate_workflow(expected_tag, expected_version)
        self.assertEqual(mock_load_and_parse_workflow.call_args, call(expected_tag, expected_version))
        self.assertTrue(mock_load_and_parse_workflow.return_value.check_required_fields.called)
        self.assertEqual(mock_load_and_parse_workflow.return_value, validated)

    def test_get_workflow_id(self):
        mock_api = Mock()
        mock_api.workflow_get_for_tag.return_value = {'id': 2}
        response = self.cwl_workflow_version.get_workflow_id(mock_api, 'wf-tag')
        mock_api.workflow_get_for_tag.assert_called_with('wf-tag')
        self.assertEqual(response, 2)
