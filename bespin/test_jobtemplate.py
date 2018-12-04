from __future__ import absolute_import
from unittest import TestCase
import yaml
import json
from bespin.jobtemplate import JobTemplate, JobTemplateLoader, JobConfiguration, JobOrderWalker, JobOrderFileDetails, \
    JobOrderFormatFiles, JobOrderPlaceholderCheck, STRING_VALUE_PLACEHOLDER, INT_VALUE_PLACEHOLDER, FILE_PLACEHOLDER
from bespin.exceptions import IncompleteJobTemplateException
from mock import patch, call, Mock


class JobTemplateTestCase(TestCase):
    def test_to_dict(self):
        job_template = JobTemplate(tag='sometag', name='myjob', fund_code='001', job_order={})
        expected_dict = {
            'fund_code': '001',
            'job_order': {},
            'name': 'myjob',
            'tag': 'sometag'
        }
        self.assertEqual(job_template.to_dict(), expected_dict)

    def test_create_user_job_order_json(self):
        job_template = JobTemplate(tag='sometag', name='myjob', fund_code='001', job_order={
            'myfile': {
                'class': 'File',
                'path': 'dds://project/somepath.txt'
            },
            'my_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'my_url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
            'myint': 123,
            'myfileary': [
                {
                    'class': 'File',
                    'path': 'dds://project/somepath1.txt'
                },
                {
                    'class': 'File',
                    'path': 'dds://project/somepath2.txt'
                },
            ],
            'myfastq_pairs': [
                {'file1':
                     {'class': 'File',
                      'path': 'dds://myproject/rawData/SAAAA_R1_001.fastq.gz'
                      },
                 'file2': {
                     'class': 'File',
                     'path': 'dds://myproject/rawData/SAAAA_R2_001.fastq.gz'
                 },
                 'name': 'Sample1'}]
        })
        user_job_order = job_template.create_user_job_order()
        self.assertEqual(user_job_order['myint'], 123)
        self.assertEqual(user_job_order['myfile'], {
            'class': 'File',
            'path': 'dds_project_somepath.txt'
        })
        self.assertEqual(user_job_order['myfileary'], [
            {
                'class': 'File',
                'path': 'dds_project_somepath1.txt'
            },
            {
                'class': 'File',
                'path': 'dds_project_somepath2.txt'
            },
        ])
        self.assertEqual(user_job_order['myfastq_pairs'], [
            {'file1':
                 {'class': 'File',
                  'path': 'dds_myproject_rawData_SAAAA_R1_001.fastq.gz'
                  },
             'file2': {
                 'class': 'File',
                 'path': 'dds_myproject_rawData_SAAAA_R2_001.fastq.gz'
             },
             'name': 'Sample1'}])
        self.assertEqual(user_job_order['my_path_file'], {
            'class': 'File',
            'path': '/tmp/data.txt'
        }, "Plain file paths should not be modified.")
        self.assertEqual(user_job_order['my_url_file'], {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
        }, "URL file paths should not be modified.")

    @patch('bespin.jobtemplate.DDSFileUtil')
    def test_get_dds_files_details(self, mock_dds_file_util):
        mock_dds_file_util.return_value.find_file_for_path.return_value = 'filedata1'
        job_template = JobTemplate(tag='sometag', name='myjob', fund_code='001', job_order={
            'myfile': {
                'class': 'File',
                'path': 'dds://project_somepath.txt'
            },
            'myint': 123
        })
        file_details = job_template.get_dds_files_details()
        self.assertEqual(file_details, [('filedata1', 'dds_project_somepath.txt')])

    @patch('bespin.jobtemplate.DDSFileUtil')
    def test_create_job(self, mock_dds_file_util):
        mock_dds_file_util.return_value.find_file_for_path.return_value = 'filedata1'
        mock_api = Mock()
        mock_api.dds_user_credentials_list.return_value = [{'id': 111, 'dds_id': 112}]
        mock_api.workflow_configurations_list.return_value = [
            {
                'id': 222
            }
        ]
        mock_api.stage_group_post.return_value = {
            'id': 333
        }
        job_template = JobTemplate(tag='sometag/v1/human', name='myjob', fund_code='001', job_order={
            'myfile': {
                'class': 'File',
                'path': 'dds://project_somepath.txt'
            },
            'myint': 555
        })
        job_template.get_dds_files_details = Mock()
        mock_file = Mock(project_id=666, current_version={'upload': {'size': 4002}})
        mock_file.id = 777
        job_template.get_dds_files_details.return_value = [[mock_file, 'somepath']]

        job_template.create_job(mock_api)

        mock_api.workflow_configurations_list.assert_called_with(tag='human', workflow_tag='sometag')
        mock_api.dds_job_input_files_post.assert_called_with(666, 777, 'somepath', 0, 0, 111, stage_group_id=333,
                                                             size=4002)
        mock_api.job_templates_create_job.assert_called_with({
            'name': 'myjob',
            'fund_code': '001',
            'job_order': {
                'myfile': {
                    'class': 'File',
                    'path': 'dds_project_somepath.txt'
                },
                'myint': 555
            },
            'tag': 'sometag/v1/human',
            'stage_group': 333
        })
        mock_dds_file_util.return_value.give_download_permissions.assert_called_with(666, 112)

    @patch('bespin.jobtemplate.DDSFileUtil')
    @patch('bespin.jobtemplate.JobOrderFormatFiles')
    def test_verify_job(self, mock_job_order_format_files, mock_dds_file_util):
        mock_dds_file_util.return_value.find_file_for_path.return_value = 'filedata1'
        mock_api = Mock()
        mock_api.dds_user_credentials_list.return_value = [{'id': 111, 'dds_id': 112}]
        mock_api.workflow_configurations_list.return_value = [
            {
                'id': 222
            }
        ]
        mock_api.stage_group_post.return_value = {
            'id': 333
        }
        job_order = {
            'myfile': {
                'class': 'File',
                'path': 'dds://project_somepath.txt'
            },
            'myint': 555
        }
        job_template = JobTemplate(tag='sometag/v1/human', name='myjob', fund_code='001', job_order=job_order)
        job_template.get_dds_files_details = Mock()
        mock_file = Mock(project_id=666, current_version={'upload': {'size': 4002}})
        mock_file.id = 777
        job_template.get_dds_files_details.return_value = [[mock_file, 'somepath']]

        job_template.verify_job(mock_api)
        mock_api.workflow_configurations_list.assert_called_with(tag='human', workflow_tag='sometag')
        job_template.get_dds_files_details.assert_called_with()
        mock_job_order_format_files.return_value.walk.assert_called_with(job_order)


class JobFileLoaderTestCase(TestCase):
    @patch('bespin.jobtemplate.yaml')
    def test_create_job_file(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': 'myjob',
            'fund_code': '0001',
            'job_order': {},
            'tag': 'mytag',
        }
        job_template_loader = JobTemplateLoader(Mock())
        job_template_loader.validate_job_file_data = Mock()
        job_template = job_template_loader.create_job_template()

        self.assertEqual(job_template.name, 'myjob')
        self.assertEqual(job_template.fund_code, '0001')
        self.assertEqual(job_template.job_order, {})
        self.assertEqual(job_template.tag, 'mytag')

    @patch('bespin.jobtemplate.yaml')
    def test_validate_job_file_data_ok(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': 'myjob',
            'fund_code': '0001',
            'job_order': {},
            'tag': 'mytag',
        }
        job_template_loader = JobTemplateLoader(Mock())
        job_template_loader.validate_job_file_data()

    @patch('bespin.jobtemplate.yaml')
    def test_validate_job_file_data_invalid_name_and_fund_code(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': STRING_VALUE_PLACEHOLDER,
            'fund_code': STRING_VALUE_PLACEHOLDER,
            'job_order': {},
            'tag': 'mytag',
        }
        job_template_loader = JobTemplateLoader(Mock())
        with self.assertRaises(IncompleteJobTemplateException) as raised_exception:
            job_template_loader.validate_job_file_data()
        self.assertEqual(str(raised_exception.exception),
                         'Please fill in placeholder values for field(s): fund_code, name')

    @patch('bespin.jobtemplate.yaml')
    def test_validate_job_file_data_invalid_job_order_params(self, mock_yaml):
        mock_yaml.load.return_value = {
            'name': 'myjob',
            'fund_code': '0001',
            'job_order': {
                'intval': INT_VALUE_PLACEHOLDER,
                'fileval': {
                    'class': 'File',
                    'path': FILE_PLACEHOLDER
                },
                'otherint': 123,
                'otherfile': {
                    'class': 'File',
                    'path': 'somefile.txt'
                },
            },
            'tag': 'mytag',
        }
        job_template_loader = JobTemplateLoader(Mock())
        with self.assertRaises(IncompleteJobTemplateException) as raised_exception:
            job_template_loader.validate_job_file_data()
        self.assertEqual(str(raised_exception.exception),
                         'Please fill in placeholder values for field(s): job_order.fileval, job_order.intval')


class JobConfigurationTestCase(TestCase):
    def test_create_job_file_with_placeholders(self):
        configuration = JobConfiguration({
            'tag': 'mytag',
            'user_fields': {}
        })
        job_file = configuration.create_job_template_with_placeholders()
        self.assertEqual(job_file.tag, 'mytag')
        self.assertEqual(job_file.name, STRING_VALUE_PLACEHOLDER)
        self.assertEqual(job_file.fund_code, STRING_VALUE_PLACEHOLDER)
        self.assertEqual(job_file.job_order, {})

    def test_format_user_fields(self):
        user_fields = [
            {"type": "int", "name": "myint"},
            {"type": "string", "name": "mystr"},
            {"type": {"type": "array",  "items": "int"}, "name": "intary"}
        ]
        configuration = JobConfiguration({
            'tag': 'mytag',
            'user_fields': user_fields,
        })
        user_fields = configuration.format_user_fields()
        self.assertEqual(user_fields, {
            'intary': [INT_VALUE_PLACEHOLDER], 'myint': INT_VALUE_PLACEHOLDER, 'mystr': STRING_VALUE_PLACEHOLDER
        })

    def test_create_placeholder_value(self):
        configuration = JobConfiguration({
            'tag': 'mytag',
            'user_fields': {}
        })
        self.assertEqual(
            configuration.create_placeholder_value(type_name='string', is_array=False),
            STRING_VALUE_PLACEHOLDER)
        self.assertEqual(
            configuration.create_placeholder_value(type_name='int', is_array=False),
            INT_VALUE_PLACEHOLDER)
        self.assertEqual(
            configuration.create_placeholder_value(type_name='int', is_array=True),
            [INT_VALUE_PLACEHOLDER])
        self.assertEqual(
            configuration.create_placeholder_value(type_name='File', is_array=False),
            {
                "class": "File",
                "path": FILE_PLACEHOLDER
            })
        self.assertEqual(
            configuration.create_placeholder_value(type_name='File', is_array=True),
            [{
                "class": "File",
                "path": FILE_PLACEHOLDER
            }])
        self.assertEqual(
            configuration.create_placeholder_value(type_name='NamedFASTQFilePairType', is_array=False),
            {
                "name": STRING_VALUE_PLACEHOLDER,
                "file1": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                },
                "file2": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                }
            })
        self.assertEqual(
            configuration.create_placeholder_value(type_name='NamedFASTQFilePairType', is_array=True),
            [{
                "name": STRING_VALUE_PLACEHOLDER,
                "file1": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                },
                "file2": {
                    "class": "File",
                    "path": FILE_PLACEHOLDER
                }
            }])


class JobOrderWalkerTestCase(TestCase):
    def test_walk(self):
        walker = JobOrderWalker()
        walker.on_class_value = Mock()
        walker.on_simple_value = Mock()
        walker.walk({
            'color': 'red',
            'weight': 123,
            'file1': {
                'class': 'File',
                'path': 'somepath'
            },
            'file_ary': [
                {
                    'class': 'File',
                    'path': 'somepath1'
                }, {
                    'class': 'File',
                    'path': 'somepath2'
                },
            ],
            'nested': {
                'a': [{
                    'class': 'File',
                    'path': 'somepath3'
                }]
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        })

        walker.on_simple_value.assert_has_calls([
            call('color', 'red'),
            call('weight', 123),
        ])
        walker.on_class_value.assert_has_calls([
            call('file1', {'class': 'File', 'path': 'somepath'}),
            call('file_ary', {'class': 'File', 'path': 'somepath1'}),
            call('file_ary', {'class': 'File', 'path': 'somepath2'}),
            call('nested', {'class': 'File', 'path': 'somepath3'}),
        ])

    def test_format_file_path(self):
        data = [
            # input    expected
            ('https://placeholder.data/stuff/data.txt', 'https://placeholder.data/stuff/data.txt'),
            ('dds://myproject/rawData/SAAAA_R1_001.fastq.gz', 'dds_myproject_rawData_SAAAA_R1_001.fastq.gz'),
            ('dds://project/somepath.txt', 'dds_project_somepath.txt'),
            ('dds://project/dir/somepath.txt', 'dds_project_dir_somepath.txt'),
        ]
        for input_val, expected_val in data:
            self.assertEqual(JobOrderWalker.format_file_path(input_val), expected_val)


class JobOrderPlaceholderCheckTestCase(TestCase):
    def test_walk(self):
        job_order = {
            'good_str': 'a',
            'bad_str': STRING_VALUE_PLACEHOLDER,
            'good_int': 123,
            'bad_int': INT_VALUE_PLACEHOLDER,
            'good_file': {
                'class': 'File',
                'path': 'somepath.txt',
            },
            'bad_file': {
                'class': 'File',
                'path': FILE_PLACEHOLDER,
            },
            'good_str_ary': ['a', 'b', 'c'],
            'bad_str_ary': ['a', STRING_VALUE_PLACEHOLDER, 'c'],
            'good_file_ary': [{
                'class': 'File',
                'path': 'somepath.txt',
            }],
            'bad_file_ary': [{
                'class': 'File',
                'path': FILE_PLACEHOLDER,
            }],
            'good_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': 'somepath.txt',
                }
            },
            'bad_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': FILE_PLACEHOLDER,
                }
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        }
        expected_keys = [
            'bad_str', 'bad_int', 'bad_file', 'bad_str_ary', 'bad_file_ary', 'bad_file_dict',
        ]

        checker = JobOrderPlaceholderCheck()
        checker.walk(job_order)

        self.assertEqual(checker.keys_with_placeholders, set(expected_keys))


class JobOrderFormatFilesTestCase(TestCase):
    def test_walk(self):
        job_order = {
            'good_str': 'a',
            'good_int': 123,
            'good_file': {
                'class': 'File',
                'path': 'dds://project1/data/somepath.txt',
            },
            'good_str_ary': ['a', 'b', 'c'],
            'good_file_ary': [{
                'class': 'File',
                'path': 'dds://project2/data/somepath2.txt',
            }],
            'good_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': 'dds://project3/data/other/somepath.txt',
                }
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        }

        formatter = JobOrderFormatFiles()
        formatter.walk(job_order)

        self.assertEqual(job_order['good_str'], 'a')
        self.assertEqual(job_order['good_int'], 123)
        self.assertEqual(job_order['good_file'],
                         {'class': 'File', 'path': 'dds_project1_data_somepath.txt'})
        self.assertEqual(job_order['good_str_ary'], ['a', 'b', 'c'])
        self.assertEqual(job_order['good_file_ary'],
                         [{'class': 'File', 'path': 'dds_project2_data_somepath2.txt'}])
        self.assertEqual(job_order['good_file_dict'],
                         {'stuff': {'class': 'File', 'path': 'dds_project3_data_other_somepath.txt'}})


class JobOrderFileDetailsTestCase(TestCase):
    @patch('bespin.jobtemplate.DDSFileUtil')
    def test_walk(self, mock_dds_file_util):
        mock_dds_file_util.return_value.find_file_for_path.return_value = 'ddsfiledata'
        job_order = {
            'good_str': 'a',
            'good_int': 123,
            'good_file': {
                'class': 'File',
                'path': 'dds://project1/data/somepath.txt',
            },
            'good_str_ary': ['a', 'b', 'c'],
            'good_file_ary': [{
                'class': 'File',
                'path': 'dds://project2/data/somepath2.txt',
            }],
            'good_file_dict': {
                'stuff': {
                    'class': 'File',
                    'path': 'dds://project3/data/other/somepath.txt',
                }
            },
            'plain_path_file': {
                'class': 'File',
                'path': '/tmp/data.txt'
            },
            'url_file': {
                'class': 'File',
                'location': 'https://github.com/datafile1.dat'
            },
        }
        expected_dds_file_info = [
            ('ddsfiledata', 'dds_project1_data_somepath.txt'),
            ('ddsfiledata', 'dds_project2_data_somepath2.txt'),
            ('ddsfiledata', 'dds_project3_data_other_somepath.txt')
        ]

        details = JobOrderFileDetails()
        details.walk(job_order)

        self.assertEqual(details.dds_files, expected_dds_file_info)

