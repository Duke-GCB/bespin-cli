from ddsc.sdk.client import Client, ItemNotFound
from bespin.exceptions import InvalidFilePathException, FileDoesNotExistException, ProjectDoesNotExistException
import os

PATH_PREFIX = "dds://"


class DDSFileUtil(object):
    def __init__(self):
        self.client = Client()

    def find_file_for_path(self, duke_ds_file_path):
        if not duke_ds_file_path.startswith(PATH_PREFIX):
            raise InvalidFilePathException("Invalid DukeDS file path: {}".format(duke_ds_file_path))

        path = duke_ds_file_path.replace(PATH_PREFIX, '', 1)
        project_name = os.path.dirname(path)
        file_path = path.replace('{}/'.format(project_name), '', 1)
        project = self.find_project_for_name(project_name)
        if project:
            try:
                return project.get_child_for_path(file_path)
            except ItemNotFound:
                raise FileDoesNotExistException("File does not exist: {}".format(duke_ds_file_path))
        else:
            raise ProjectDoesNotExistException("Project does not exist: {}".format(duke_ds_file_path))

    def find_project_for_name(self, project_name):
        for project in self.client.get_projects():
            if project.name == project_name:
                return project
        return None
