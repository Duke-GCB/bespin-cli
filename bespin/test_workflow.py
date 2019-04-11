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
        self.cwl_workflow_version = CWLWorkflowVersion(workflow_tag="sometag", url="someurl",
                                                       description="SomeDesc", version=1)

    @patch('bespin.workflow.load_tool')
    def test_create(self, mock_load_tool):
        mock_api = Mock()
        mock_api.workflow_get_for_tag.return_value = {'id': 1}
        response = self.cwl_workflow_version.create(mock_api)
        mock_fields = mock_load_tool.return_value.inputs_record_schema.get.return_value
        mock_api.workflow_versions_post.assert_called_with(workflow=1, version_num=1, description="SomeDesc",
                                                           url="someurl", fields=mock_fields)

    def test_get_workflow_id(self):
        mock_api = Mock()
        mock_api.workflow_get_for_tag.return_value = {'id': 2}
        response = self.cwl_workflow_version.get_workflow_id(mock_api)
        self.assertEqual(response, 2)

    def test_get_version_num(self):
        mock_api = Mock()
        self.cwl_workflow_version.version = 2
        self.assertEqual(self.cwl_workflow_version.get_version_num(mock_api), 2)
        mock_api.workflow_versions_list.assert_not_called()

        mock_api.workflow_versions_list.return_value = [
            {'version': 1},
            {'version': 2},
        ]
        self.cwl_workflow_version.version = 'auto'
        self.assertEqual(self.cwl_workflow_version.get_version_num(mock_api), 3)
        mock_api.workflow_versions_list.assert_called_with('sometag')

    @patch('bespin.workflow.load_tool')
    def test_get_fields_from_url(self, mock_load_tool):
        response = self.cwl_workflow_version.get_fields_from_url()
        self.assertEqual(response, mock_load_tool.return_value.inputs_record_schema.get.return_value)
        mock_load_tool.return_value.inputs_record_schema.get.assert_called_with("fields")
