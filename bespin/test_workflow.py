from __future__ import absolute_import
from unittest import TestCase
from bespin.workflow import CWLWorkflowVersion, BespinWorkflowLoader, BespinWorkflowValidator, BespinWorkflowParser
from bespin.workflow import InvalidWorkflowFileException
from unittest.mock import patch, call, Mock, create_autospec

import logging
logging.disable(logging.ERROR)


@patch('bespin.workflow.tempfile.mkdtemp')
class BespinWorkflowLoaderTestCase(TestCase):

    def setUp(self):
        self.workflow_version = create_autospec(CWLWorkflowVersion,
                                                url='http://example.com/workflow.cwl',
                                                workflow_type='dummy')
        self.packed_workflow_version = create_autospec(CWLWorkflowVersion,
                                                       url='http://example.com/packed.cwl',
                                                       workflow_type=BespinWorkflowLoader.TYPE_PACKED,
                                                       workflow_path='#main')
        self.zipped_workflow_version = create_autospec(CWLWorkflowVersion,
                                                       url='http://example.com/zipped.zip',
                                                       workflow_type=BespinWorkflowLoader.TYPE_ZIPPED,
                                                       workflow_path='unzipped/workflow.cwl')
        self.direct_workflow_version = create_autospec(CWLWorkflowVersion,
                                                       url='file:///direct/direct.cwl',
                                                       workflow_type=BespinWorkflowLoader.TYPE_DIRECT,
                                                       workflow_path=None)

    def setup_mkdtemp(self, mock_mkdtemp):
        mock_mkdtemp.return_value = '/tmpdir'

    def test_init_common(self, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.workflow_version)
        self.assertEqual(loader.download_dir, mock_mkdtemp.return_value)
        self.assertEqual(loader.workflow_version, self.workflow_version)
        self.assertEqual(loader.download_path, '/tmpdir/workflow.cwl')

    def test_init_direct(self, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.direct_workflow_version)
        self.assertFalse(mock_mkdtemp.called)
        self.assertEqual(loader.workflow_version, self.direct_workflow_version)
        self.assertFalse(hasattr(loader, 'download_path'))
        self.assertFalse(hasattr(loader, 'download_dir'))

    @patch('bespin.workflow.BespinWorkflowLoader._download_workflow')
    @patch('bespin.workflow.BespinWorkflowLoader._handle_download')
    @patch('bespin.workflow.BespinWorkflowLoader._load_downloaded_workflow')
    @patch('bespin.workflow.BespinWorkflowLoader._cleanup')
    def test_load(self, mock_cleanup, mock_load_downloaded_workflow, mock_handle_download, mock_download_workflow, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.workflow_version)
        manager = Mock()
        manager.attach_mock(mock_download_workflow, 'download')
        manager.attach_mock(mock_handle_download, 'handle')
        manager.attach_mock(mock_load_downloaded_workflow, 'load_downloaded')
        manager.attach_mock(mock_cleanup, 'cleanup')
        loaded = loader.load()
        self.assertEqual(manager.mock_calls, [call.download(), call.handle(), call.load_downloaded(), call.cleanup()])
        # Make sure we assert this check after the order, because it interferes with the calls
        self.assertEqual(loaded, mock_load_downloaded_workflow.return_value)

    @patch('bespin.workflow.urlretrieve')
    def test__download_workflow(self, mock_urlretrieve, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.zipped_workflow_version)
        loader._download_workflow()
        self.assertEqual(mock_urlretrieve.call_args, call(self.zipped_workflow_version.url, loader.download_path))

    @patch('bespin.workflow.urlretrieve')
    def test__no_download_direct(self, mock_urlretriefve, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.direct_workflow_version)
        loader._download_workflow()
        self.assertFalse(mock_mkdtemp.called)
        self.assertFalse(mock_urlretriefve.called)

    @patch('bespin.workflow.zipfile.ZipFile')
    def test__handle_download_zipped(self, mock_zipfile, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.zipped_workflow_version)
        loader._handle_download()
        self.assertTrue(mock_zipfile.called)
        self.assertEqual(mock_zipfile.return_value.__enter__.return_value.extractall.call_args, call(loader.download_dir))

    @patch('bespin.workflow.zipfile.ZipFile')
    def test__handle_download_packed(self, mock_zipfile, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.packed_workflow_version)
        loader._handle_download()
        self.assertFalse(mock_zipfile.called)

    @patch('bespin.workflow.load_tool')
    @patch('bespin.workflow.BespinWorkflowLoader._get_tool_path')
    @patch('bespin.workflow.LoadingContext')
    def test__load_downloaded_workflow(self, mock_context, mock_get_tool_path, mock_load_tool, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        mock_get_tool_path.return_value = 'tool-path'
        loader = BespinWorkflowLoader(self.workflow_version)
        loaded = loader._load_downloaded_workflow()
        self.assertEqual(loaded, mock_load_tool.return_value)
        self.assertEqual(mock_load_tool.call_args, call('tool-path', mock_context.return_value))

    def test__get_tool_path_packed(self, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.packed_workflow_version)
        tool_path = loader._get_tool_path()
        self.assertEqual(tool_path, '/tmpdir/packed.cwl#main')

    def test__get_tool_path_zipped(self, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.zipped_workflow_version)
        tool_path = loader._get_tool_path()
        self.assertEqual(tool_path, '/tmpdir/unzipped/workflow.cwl')

    def test__get_tool_path_direct(self, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.direct_workflow_version)
        tool_path = loader._get_tool_path()
        self.assertEqual(tool_path, 'file:///direct/direct.cwl')

    def test__get_tool_path_raises(self, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        self.workflow_version.workflow_type = 'other'
        loader = BespinWorkflowLoader(self.workflow_version)
        with self.assertRaises(InvalidWorkflowFileException) as context:
            tool_path = loader._get_tool_path()
        self.assertIn('Workflow type other is not supported', str(context.exception))

    @patch('bespin.workflow.shutil.rmtree')
    def test__cleanup_zipped(self, mock_rmtree, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.zipped_workflow_version)
        loader._cleanup()
        self.assertEqual(mock_rmtree.call_args, call(loader.download_dir))

    @patch('bespin.workflow.shutil.rmtree')
    def test__cleanup_direct(self, mock_rmtree, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.direct_workflow_version)
        loader._cleanup()
        self.assertFalse(mock_rmtree.called)


class BespinWorkflowValidatorTestCase(TestCase):

    def setUp(self):
        self.tag = 'processing'
        self.version = 'v2.4.6'
        self.workflow_dict = {
            'class': 'Workflow',
            'cwlVersion': 'v1.0',
            'label': 'processing/v2.4.6',
            'doc': 'Processing - v2.4.6',
        }

    def test_validate_ok(self):
        workflow = Mock(tool=self.workflow_dict)
        validator = BespinWorkflowValidator(workflow)
        self.assertEqual(len(validator.errors), 0)
        self.assertEqual(len(validator.messages), 0)
        validator.validate(self.tag, self.version)
        validator.report(True)
        self.assertEqual(len(validator.errors), 0)
        self.assertEqual(len(validator.messages), 8)
        self.assertEqual('\n'.join(validator.messages), """Field 'class' exists
Field 'class' has required value 'Workflow'
Field 'cwlVersion' exists
Field 'cwlVersion' has required value 'v1.0'
Field 'label' exists
Field 'label' has required value 'processing/v2.4.6'
Field 'doc' exists
Field 'doc' has required pattern 'v2.4.6'""")

    def test_validate_fails_class_not_workflow(self):
        self.workflow_dict['class'] = 'NotWorkflow'
        workflow = Mock(tool=self.workflow_dict)
        validator = BespinWorkflowValidator(workflow)
        validator.validate(self.tag, self.version)
        self.assertIn("Field 'class' must have a value of 'Workflow'", validator.errors)
        with self.assertRaises(InvalidWorkflowFileException) as context:
            validator.report(True)

    def test_validate_fails_missing_required_fields(self):
        workflow = Mock(tool={})
        validator = BespinWorkflowValidator(workflow)
        validator.validate(self.tag, self.version)
        self.assertMultiLineEqual('\n'.join(validator.errors), """Field 'class' was not found in your CWL file
Field 'cwlVersion' was not found in your CWL file
Field 'label' was not found in your CWL file
Field 'doc' was not found in your CWL file""")
        with self.assertRaises(InvalidWorkflowFileException) as context:
            validator.report(True)

    def test_validate_fails_wrong_label_version(self):
        self.workflow_dict['label'] = 'processing/v2.6.1'
        workflow = Mock(tool=self.workflow_dict)
        validator = BespinWorkflowValidator(workflow)
        validator.validate(self.tag, self.version)
        self.assertIn("Field 'label' must have a value of 'processing/v2.4.6'", validator.errors)
        with self.assertRaises(InvalidWorkflowFileException) as context:
            validator.report(True)

    def test_validate_fails_wrong_label_tag(self):
        self.workflow_dict['label'] = 'analysis/v2.4.6'
        workflow = Mock(tool=self.workflow_dict)
        validator = BespinWorkflowValidator(workflow)
        validator.validate(self.tag, self.version)
        self.assertIn("Field 'label' must have a value of 'processing/v2.4.6'", validator.errors)
        with self.assertRaises(InvalidWorkflowFileException) as context:
            validator.report(True)

    def test_validate_fails_wrong_doc_version(self):
        self.workflow_dict['doc'] = 'Some Workflow - v1.2.1'
        workflow = Mock(tool=self.workflow_dict)
        validator = BespinWorkflowValidator(workflow)
        validator.validate(self.tag, self.version)
        self.assertIn("Field 'doc' must have a pattern 'v2.4.6'", validator.errors)
        with self.assertRaises(InvalidWorkflowFileException) as context:
            validator.report(True)


class BespinWorkflowParserTestCase(TestCase):

    def setUp(self):
        self.loaded_workflow = Mock(
            tool={'label':'processing/v2.4.6', 'doc': 'Processing v2.4.6'},
            inputs_record_schema={'fields': ['field1','field2']}
        )

    def test_parses_on_init(self):
        parser = BespinWorkflowParser(self.loaded_workflow)
        self.assertEqual(parser.version, 'v2.4.6')
        self.assertEqual(parser.tag, 'processing')
        self.assertEqual(parser.description, 'Processing v2.4.6')
        self.assertEqual(parser.input_fields, ['field1','field2'])

    def test_ignores_label_if_invalid(self):
        self.loaded_workflow.tool['label'] = 'workflow-v1.2.3'
        parser = BespinWorkflowParser(self.loaded_workflow)
        self.assertIsNone(parser.tag)
        self.assertIsNone(parser.version)
        self.assertIsNotNone(parser.description)

    def test_check_required_fields_raises_on_empty_tag(self):
        parser = BespinWorkflowParser(self.loaded_workflow)
        parser.tag = None
        with self.assertRaises(InvalidWorkflowFileException) as context:
            parser.check_required_fields()
        self.assertIn('Unable to extract workflow tag and version', str(context.exception))

    def test_check_required_fields_raises_on_empty_version(self):
        parser = BespinWorkflowParser(self.loaded_workflow)
        parser.version = None
        with self.assertRaises(InvalidWorkflowFileException) as context:
            parser.check_required_fields()
        self.assertIn('Unable to extract workflow tag and version', str(context.exception))

    def test_check_required_fields_raises_on_empty_description(self):
        parser = BespinWorkflowParser(self.loaded_workflow)
        parser.description = ''
        with self.assertRaises(InvalidWorkflowFileException) as context:
            parser.check_required_fields()
        self.assertIn('Unable to extract workflow description', str(context.exception))

    def test_check_required_fields_ok(self):
        parser = BespinWorkflowParser(self.loaded_workflow)
        parser.check_required_fields()


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
