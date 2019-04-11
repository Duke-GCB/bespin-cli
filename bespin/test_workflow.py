from __future__ import absolute_import
from unittest import TestCase
from bespin.workflow import CWLWorkflowVersion, BespinWorkflowLoader, BespinWorkflowValidator, BespinWorkflowParser
from bespin.workflow import InvalidWorkflowFileException
from unittest.mock import patch, call, Mock, create_autospec


@patch('bespin.workflow.tempfile.mkdtemp')
class BespinWorkflowLoaderTestCase(TestCase):

    def setUp(self):
        self.workflow_version = create_autospec(CWLWorkflowVersion,
                                                url='http://example.com/workflow.cwl')
        self.packed_workflow_version = create_autospec(CWLWorkflowVersion,
                                                       url='http://example.com/packed.cwl',
                                                       workflow_type=BespinWorkflowLoader.TYPE_PACKED,
                                                       workflow_path='#main')
        self.zipped_workflow_version = create_autospec(CWLWorkflowVersion,
                                                       url='http://example.com/zipped.zip',
                                                       workflow_type=BespinWorkflowLoader.TYPE_ZIPPED,
                                                       workflow_path='unzipped/workflow.cwl')

    def setup_mkdtemp(self, mock_mkdtemp):
        mock_mkdtemp.return_value = '/tmpdir'

    def test_init(self, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.workflow_version)
        self.assertEqual(loader.download_dir, mock_mkdtemp.return_value)
        self.assertEqual(loader.workflow_version, self.workflow_version)
        self.assertEqual(loader.download_path, '/tmpdir/workflow.cwl')

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
        loader = BespinWorkflowLoader(self.workflow_version)
        loader._download_workflow()
        self.assertEqual(mock_urlretrieve.call_args, call(self.workflow_version.url, loader.download_path))

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

    def test__get_tool_path_raises(self, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        self.workflow_version.workflow_type = 'other'
        loader = BespinWorkflowLoader(self.workflow_version)
        with self.assertRaises(InvalidWorkflowFileException) as context:
            tool_path = loader._get_tool_path()
        self.assertIn('Workflow type other is not supported', str(context.exception))

    @patch('bespin.workflow.shutil.rmtree')
    def test__cleanup(self, mock_rmtree, mock_mkdtemp):
        self.setup_mkdtemp(mock_mkdtemp)
        loader = BespinWorkflowLoader(self.workflow_version)
        loader._cleanup()
        self.assertEqual(mock_rmtree.call_args, call(loader.download_dir))


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
