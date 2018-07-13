from ddsc.sdk.client import Client, ItemNotFound
from bespin.exceptions import InvalidFilePathException, FileDoesNotExistException, ProjectDoesNotExistException
import os

PATH_PREFIX = "dds://"

INVALID_DUKEDS_FILE_PATH_MSG = "Invalid DukeDS file path ({})"
DUKEDS_FILE_PATH_MISSING_PREFIX = INVALID_DUKEDS_FILE_PATH_MSG.format("missing prefix")
DUKEDS_FILE_PATH_MISSING_SLASH = INVALID_DUKEDS_FILE_PATH_MSG.format("missing / between project and file path")

class DDSFileUtil(object):
    def __init__(self):
        self.client = Client()

    def find_file_for_path(self, duke_ds_file_path):
        project_name, file_path = self.get_project_name_and_file_path(duke_ds_file_path)
        project = self.find_project_for_name(project_name)
        if project:
            try:
                return project.get_child_for_path(file_path)
            except ItemNotFound:
                raise FileDoesNotExistException("File does not exist: {}".format(duke_ds_file_path))
        else:
            raise ProjectDoesNotExistException("Project does not exist: {}".format(duke_ds_file_path))

    @staticmethod
    def get_project_name_and_file_path(duke_ds_file_path):
        if not duke_ds_file_path.startswith(PATH_PREFIX):
            raise InvalidFilePathException("{}: {}".format(DUKEDS_FILE_PATH_MISSING_PREFIX, duke_ds_file_path))
        path = duke_ds_file_path.replace(PATH_PREFIX, '', 1)
        path_parts = path.split(os.sep)
        if len(path_parts) < 2:
            raise InvalidFilePathException("{}: {}".format(DUKEDS_FILE_PATH_MISSING_SLASH, duke_ds_file_path))
        project_name = path_parts[0]
        file_path = path.replace('{}/'.format(project_name), '', 1)
        return project_name, file_path

    def find_project_for_name(self, project_name):
        for project in self.client.get_projects():
            if project.name == project_name:
                return project
        return None

    def give_download_permissions(self, project_id, dds_user_id):
        self.client.dds_connection.data_service.set_user_project_permission(project_id, dds_user_id,
                                                                            auth_role='file_downloader')
