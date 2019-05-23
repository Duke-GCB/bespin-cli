from unittest import TestCase
from unittest.mock import patch, call, Mock

from bespin.tool_details import DockerToolDetail, SoftwareToolDetail, ToolDetailsBuilder, ToolDetails


class DockerToolDetailTestCase(TestCase):
    def setUp(self):
        self.req_dict = {'dockerPull': 'orgname/image:3.2.1'}

    def test_init(self):
        detail = DockerToolDetail(self.req_dict)
        self.assertEqual(detail.docker_image_name, self.req_dict['dockerPull'])

    def test_add_info(self):
        detail = DockerToolDetail(self.req_dict)
        info_dict = {}
        detail.add_info(info_dict)
        self.assertEqual(info_dict['docker'], [{'image_name': 'orgname/image:3.2.1'}])


class SoftwareToolDetailTestCase(TestCase):
    def setUp(self):
        self.req_dict = {'packages': [
            {'package': 'abc-tk',
             'version': ['1.0'],
             'https://schema.org/citation': 'https://example.org'},
            {'package': 'def-tk',
             'version': ['2.0'],
             'https://schema.org/citation': 'https://example.com'}
        ]}

    def test_init(self):
        detail = SoftwareToolDetail(self.req_dict)
        self.assertEqual(detail.packages, self.req_dict['packages'])

    def test_add_info(self):
        detail = SoftwareToolDetail(self.req_dict)
        info_dict = {}
        detail.add_info(info_dict)
        self.assertEqual(info_dict['software'], [
            {'citation': 'https://example.org', 'package': 'abc-tk', 'versions': ['1.0']},
            {'citation': 'https://example.com', 'package': 'def-tk', 'versions': ['2.0']},
        ])


class ToolDetailsBuilderTestCase(TestCase):

    def setUp(self):
        self.prefix = '/pre/'
        self.docker_req = {'class': 'DockerRequirement', 'dockerPull': 'orgname/image:1.0'}
        self.software_req = {'class': 'SoftwareRequirement',
                             'packages': [
                                 {'package': 'abc-tk',
                                  'version': ['1.0'],
                                  'https://schema.org/citation': 'https://example.org'}
                             ]}

    def test_init(self):
        builder = ToolDetailsBuilder(self.prefix)
        self.assertEqual(builder.prefix, self.prefix)
        self.assertEqual(builder.details, [])

    def test_accept(self):
        builder = ToolDetailsBuilder(self.prefix)
        visitor = Mock()
        builder.accept(visitor)
        self.assertEqual(visitor.visit.call_args, call(builder.extract_tool_details))

    def test_tool_exists(self):
        builder = ToolDetailsBuilder(self.prefix)
        builder.details = [{'tool_name': 'foo'}]
        self.assertTrue(builder.tool_exists('foo'))
        self.assertFalse(builder.tool_exists('bar'))

    @patch('bespin.tool_details.DockerToolDetail')
    @patch('bespin.tool_details.SoftwareToolDetail')
    def test_extract_requirements_docker(self, mock_software_tool_detail, mock_docker_tool_detail):
        tool_info = Mock()
        builder = ToolDetailsBuilder(self.prefix)
        builder.extract_requirements([self.docker_req], tool_info)
        self.assertEqual(mock_docker_tool_detail.call_count, 1)
        self.assertEqual(mock_software_tool_detail.call_count, 0)
        self.assertEqual(mock_docker_tool_detail.call_args, call(self.docker_req))
        self.assertEqual(mock_docker_tool_detail.return_value.add_info.call_args, call(tool_info))

    @patch('bespin.tool_details.DockerToolDetail')
    @patch('bespin.tool_details.SoftwareToolDetail')
    def test_extract_requirements_software(self, mock_software_tool_detail, mock_docker_tool_detail):
        tool_info = Mock()
        builder = ToolDetailsBuilder(self.prefix)
        builder.extract_requirements([self.software_req], tool_info)
        self.assertEqual(mock_software_tool_detail.call_count, 1)
        self.assertEqual(mock_docker_tool_detail.call_count, 0)
        self.assertEqual(mock_software_tool_detail.call_args, call(self.software_req))
        self.assertEqual(mock_software_tool_detail.return_value.add_info.call_args, call(tool_info))

    @patch('bespin.tool_details.DockerToolDetail')
    @patch('bespin.tool_details.SoftwareToolDetail')
    def test_extract_requirements_other(self, mock_software_tool_detail, mock_docker_tool_detail):
        tool_info = Mock()
        builder = ToolDetailsBuilder(self.prefix)
        builder.extract_requirements([{'class': 'OtherRequirement'}], tool_info)
        self.assertEqual(mock_software_tool_detail.call_count, 0)
        self.assertEqual(mock_docker_tool_detail.call_count, 0)

    def test_extract_tool_details(self):
        node = {
            'class': 'CommandLineTool',
            'id': '/pre/tool.cwl',
            'requirements': [self.software_req],
            'hints': [self.docker_req],
        }
        builder = ToolDetailsBuilder(self.prefix)
        builder.extract_tool_details(node)
        expected_detail = {'tool_name': 'tool.cwl', 'tool_info': {
            'software': [{'package': 'abc-tk', 'versions': ['1.0'], 'citation': 'https://example.org'}],
            'docker': [{'image_name': 'orgname/image:1.0'}]}}
        self.assertIn(expected_detail, builder.details)

    def test_extract_skips_if_exists(self):
        builder = ToolDetailsBuilder(self.prefix)
        builder.details = [{'tool_name': 'tool.cwl'}]
        node = {
            'class': 'CommandLineTool',
            'id': '/pre/tool.cwl',
            'requirements': [self.software_req],
            'hints': [self.docker_req],
        }
        builder.extract_tool_details(node)
        self.assertEqual(builder.details, [{'tool_name': 'tool.cwl'}])

    def test_build(self):
        builder = ToolDetailsBuilder(self.prefix)
        details = {'tool_name': 'tool.cwl', 'tool_info': {
            'software': [{'package': 'abc-tk', 'versions': ['1.0'], 'citation': 'https://example.org'}],
            'docker': [{'image_name': 'orgname/image:1.0'}]}}
        builder.details = [details]
        built = builder.build()
        expected_built = [{'tool_name': 'tool.cwl', 'docker_images': ['orgname/image:1.0'],
                           'packages': [{'package': 'abc-tk', 'versions': ['1.0'], 'citation': 'https://example.org'}]}]
        self.assertEqual(built, expected_built)


class ToolDetailsTestCase(TestCase):
    def setUp(self):
        self.workflow_version = Mock()

    @patch('bespin.tool_details.BespinWorkflowLoader')
    @patch('bespin.tool_details.BespinWorkflowParser')
    @patch('bespin.tool_details.ToolDetailsBuilder')
    def test_init(self, mock_builder, mock_parser, mock_loader):
        tool_details = ToolDetails(self.workflow_version)
        self.assertEqual(tool_details.version, mock_parser.return_value.version)
        self.assertEqual(tool_details.tag, mock_parser.return_value.tag)
        self.assertEqual(tool_details.contents, mock_builder.return_value.build.return_value)
        self.assertEqual(mock_loader.call_args, call(self.workflow_version))
        self.assertEqual(mock_parser.call_args, call(mock_loader.return_value.load.return_value))
        self.assertEqual(mock_builder.call_args, call(mock_loader.return_value.get_prefix.return_value))
        self.assertEqual(mock_builder.return_value.accept.call_args, call(mock_parser.return_value.loaded_workflow))

    @patch('bespin.tool_details.BespinWorkflowLoader')
    @patch('bespin.tool_details.BespinWorkflowParser')
    @patch('bespin.tool_details.ToolDetailsBuilder')
    def test_create(self, mock_builder, mock_parser, mock_loader):
        tool_details = ToolDetails(self.workflow_version)
        mock_api = Mock()
        mock_api.workflow_version_find_by_tag_version.return_value = {'id': '56'}
        result = tool_details.create(mock_api)
        self.assertEqual(mock_api.workflow_version_find_by_tag_version.call_args,
                         call(tool_details.tag, tool_details.version))
        self.assertEqual(mock_api.workflow_version_tool_details_post.call_args, call('56', tool_details.contents))
        self.assertEqual(result, mock_api.workflow_version_tool_details_post.return_value)
