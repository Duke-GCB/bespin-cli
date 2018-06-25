from __future__ import absolute_import
from unittest import TestCase
from bespin.dukeds import DDSFileUtil, InvalidFilePathException, ProjectDoesNotExistException, \
    FileDoesNotExistException, ItemNotFound
from mock import patch, Mock


class DDSFileUtilTestCase(TestCase):
    @patch('bespin.dukeds.Client')
    def test_find_file_for_path_invalid_path(self, mock_client):
        util = DDSFileUtil()
        with self.assertRaises(InvalidFilePathException):
            util.find_file_for_path('other://mouse/dir/data.txt')

    @patch('bespin.dukeds.Client')
    def test_find_file_for_path_no_project(self, mock_client):
        util = DDSFileUtil()
        util.find_project_for_name = Mock()
        util.find_project_for_name.return_value = None
        with self.assertRaises(ProjectDoesNotExistException):
            util.find_file_for_path('dds://mouse/dir/data.txt')

    @patch('bespin.dukeds.Client')
    def test_find_file_for_path_no_project(self, mock_client):
        util = DDSFileUtil()
        util.find_project_for_name = Mock()
        mock_project = Mock()
        mock_project.get_child_for_path.side_effect = ItemNotFound()
        util.find_project_for_name.return_value = mock_project
        with self.assertRaises(FileDoesNotExistException):
            util.find_file_for_path('dds://mouse/dir/data.txt')

    @patch('bespin.dukeds.Client')
    def test_find_file_for_path(self, mock_client):
        util = DDSFileUtil()
        mock_project = Mock()
        mock_file = Mock()
        util.find_project_for_name = Mock()
        util.find_project_for_name.return_value = mock_project
        mock_project.get_child_for_path.return_value = mock_file
        returned_file = util.find_file_for_path('dds://mouse/dir/data.txt')
        self.assertEqual(returned_file, mock_file)

    @patch('bespin.dukeds.Client')
    def test_find_project_for_name(self, mock_client):
        project1 = Mock()
        project1.name = 'mouse'
        project2 = Mock()
        project2.name = 'rat'
        util = DDSFileUtil()
        util.client.get_projects.return_value = [project1, project2]

        self.assertEqual(util.find_project_for_name('mouse'), project1)
        self.assertEqual(util.find_project_for_name('rat'), project2)
        self.assertEqual(util.find_project_for_name('cheese'), None)

    @patch('bespin.dukeds.Client')
    def test_give_download_permissions(self, mock_client):
        util = DDSFileUtil()
        util.give_download_permissions(project_id='123', dds_user_id='456')
        util.client.dds_connection.data_service.set_user_project_permission.assert_called_with(
            '123', '456', auth_role='file_downloader')
