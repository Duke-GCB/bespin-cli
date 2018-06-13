from __future__ import print_function
from bespin.config import ConfigFile
from bespin.api import BespinApi
from bespin.exceptions import IncompleteJobFileException
from bespin.dukeds import DDSFileUtil
from tabulate import tabulate
import yaml
import json
import sys

USER_VALUE_PLACEHOLDER = "TODO"
USER_FILE_PLACEHOLDER = "dds://TODO_PROJECT_NAME/TODO_FILE_PATH"
USER_PLACEHOLDERS = [USER_VALUE_PLACEHOLDER, USER_FILE_PLACEHOLDER]
USER_PLACEHOLDER_DICT = {
    'File': {
        "class": "File",
        "path": USER_FILE_PLACEHOLDER
    },
    'int': USER_VALUE_PLACEHOLDER,
    'string': USER_VALUE_PLACEHOLDER,
    'NamedFASTQFilePairType': {
        "name": USER_VALUE_PLACEHOLDER,
        "file1": {
            "class": "File",
            "path": USER_FILE_PLACEHOLDER
        },
        "file2": {
            "class": "File",
            "path": USER_FILE_PLACEHOLDER
        }
    }
}


class Commands(object):
    """
    Commands run based on command line input.
    """

    def __init__(self, version_str, user_agent_str):
        """
        :param version_str: str: version of bespin-cli
        :param user_agent_str: str: agent string to use when talking to bespin-api
        """
        self.version_str = version_str
        self.user_agent_str = user_agent_str

    def _create_api(self):
        config = ConfigFile().read_or_create_config()
        return BespinApi(config, user_agent_str=self.user_agent_str)

    def workflows_list(self):
        """
        Print out a table of workflows/questionnaires
        """
        api = self._create_api()
        workflow_data = WorkflowDetails(api)
        print(Table(workflow_data.column_names, workflow_data.get_column_data()))

    def jobs_list(self):
        """
        Print out a table of current job statuses
        """
        column_names = ["id", "name", "state", "step", "fund_code", "created", "last_updated"]
        api = self._create_api()
        print(Table(column_names, api.jobs_list()))

    def init_job(self, tag, outfile):
        """
        Write a sample job file with placeholder values to outfile
        :param tag: str: tag (slug) representing which workflow/questionnaire to use
        :param outfile: file: output file that will have the sample job data written to
        """
        api = self._create_api()
        questionnaire = api.questionnaires_list(slug=tag)[0]
        job_file = JobQuestionnaire(questionnaire).create_job_file_with_placeholders()
        outfile.write(job_file.yaml_str())
        if outfile != sys.stdout:
            print("Wrote job file {}.".format(outfile.name))
            print("Edit this file filling in TODO fields then run `bespin jobs create {}` .".format(outfile.name))

    def create_job(self, infile):
        """
        Create a job based on an input job file (possibly created via init_job)
        Prints out job id.
        :param infile: file: input file to use for creating a job
        """
        api = self._create_api()
        job_file = JobFileLoader(infile).create_job_file()
        job = job_file.create_job(api)
        print("Created job {}".format(job['id']))

    def start_job(self, job_id, token=None):
        """
        Start a job with optional authorization token
        :param job_id: int: id of the job to start
        :param token: str: token to use to authorize running the job
        """
        api = self._create_api()
        if token:
            api.authorize_job(job_id, token)
            print("Set run token for job {}".format(job_id))
        api.start_job(job_id)
        print("Started job {}".format(job_id))

    def cancel_job(self, job_id):
        """
        Cancel a running job
        :param job_id: int: id of the job to cancel
        """
        api = self._create_api()
        api.cancel_job(job_id)
        print("Canceled job {}".format(job_id))

    def restart_job(self, job_id):
        """
        Restart a non-running job
        :param job_id: int: id of the job to restart
        """
        api = self._create_api()
        api.restart_job(job_id)
        print("Restarted job {}".format(job_id))

    def delete_job(self, job_id):
        """
        Delete a job
        :param job_id: int: id of the job to delete
        """
        api = self._create_api()
        api.delete_job(job_id)
        print("Deleted job {}".format(job_id))


class Table(object):
    """
    Used to display column headers and associated data as rows
    """
    def __init__(self, column_names, items):
        self.column_names = column_names
        self.items = items

    @staticmethod
    def _format_column_name(column_name):
        return column_name.replace("_", " ").title()

    def __str__(self):
        column_data = [[item[name] for name in self.column_names] for item in self.items]
        formatted_column_names = [self._format_column_name(name) for name in self.column_names]
        return tabulate(column_data, headers=formatted_column_names)


class WorkflowDetails(object):
    """
    Creates column data based on workflows/questionnaires
    """
    TAG_COLUMN_NAME = "latest version tag"

    def __init__(self, api):
        self.api = api
        self.column_names = ["id", "name", self.TAG_COLUMN_NAME]

    def get_column_data(self):
        """
        Return list of dictionaries of workflow data.
        :return: [dict]: one record for each questionnaire
        """
        data = []
        for workflow in self.api.workflows_list():
            latest_version = workflow['versions'][-1]
            for questionnaire in self.api.questionnaires_list(workflow_version=latest_version):
                workflow[self.TAG_COLUMN_NAME] = questionnaire['slug']
                data.append(workflow)
        return data


class JobFile(object):
    """
    Contains data for creating a job.
    """
    def __init__(self, workflow_tag, name, fund_code, job_order):
        """
        :param workflow_tag: str: questionnaire tag from bespin-api
        :param name: str: user name for the job
        :param fund_code: str: fund code to
        :param job_order: dict: job order details used with CWL workflow
        """
        self.workflow_tag = workflow_tag
        self.name = name
        self.fund_code = fund_code
        self.job_order = job_order

    def yaml_str(self):
        data = {
            'name': self.name,
            'fund_code': self.fund_code,
            'job_order': self.job_order,
            'workflow_tag': self.workflow_tag,
        }
        return yaml.dump(data, default_flow_style=False)

    def create_user_job_order_json(self):
        """
        Format job order replacing dds remote file paths with filenames that will be staged
        :return: dict: job order for running CWL
        """
        user_job_order = {}
        for key in self.job_order.keys():
            value = self.job_order[key]
            if isinstance(value, dict) and value['class'] == 'File':
                value['path'] = self.format_file_path(value['path'])
            user_job_order[key] = value
        return json.dumps(user_job_order)

    @staticmethod
    def format_file_path(path):
        """
        Create a valid file path based on a dds placeholder url
        :param path: str: format dds://<projectname>/<filepath>
        :return: str: file path to be used for staging data when running the workflow
        """
        return path.replace("dds://", "dds_").replace("/", "_").replace(":", "_")

    def get_dds_files_details(self):
        """
        Get dds files info based on job_order
        :return: [(dds_file, staging_filename)]
        """
        dds_file_util = DDSFileUtil()
        dds_files = []
        for key in self.job_order.keys():
            value = self.job_order[key]
            if isinstance(value, dict) and value['class'] == 'File':
                path = value['path']
                dds_file = dds_file_util.find_file_for_path(path)
                dds_files.append((dds_file, self.format_file_path(path)))
        return dds_files

    def create_job(self, api):
        """
        Create a job using the passed on api
        :param api: BespinApi
        :return: dict: job dictionary returned from bespin api
        """
        dds_user_credential = api.dds_user_credentials_list()[0]
        questionnaire = api.questionnaires_list(slug=self.workflow_tag)[0]
        stage_group = api.stage_group_post()
        dds_project_ids = set()
        sequence = 0
        for dds_file, path in self.get_dds_files_details():
            api.dds_job_input_files_post(dds_file.project_id, dds_file.id, path, 0, sequence,
                                         dds_user_credential['id'], stage_group_id=stage_group['id'])
            sequence += 1
            dds_project_ids.add(dds_file.project_id)
        user_job_order_json = self.create_user_job_order_json()
        job_answer_set = api.job_answer_set_post(self.name, self.fund_code, user_job_order_json,
                                                 questionnaire['id'], stage_group['id'])
        job = api.job_answer_set_create_job(job_answer_set['id'])

        dds_file_util = DDSFileUtil()
        for project_id in dds_project_ids:
            dds_file_util.give_download_permissions(project_id, dds_user_credential['dds_id'])
        return job


class JobFileLoader(object):
    """
    Creates JobFile based on an input file
    """
    def __init__(self, infile):
        self.data = yaml.load(infile)

    def create_job_file(self):
        self.validate_job_file_data()
        job_file = JobFile(workflow_tag=self.data['workflow_tag'],
                           name=self.data['name'],
                           fund_code=self.data['fund_code'],
                           job_order=self.data['job_order'])
        return job_file

    def validate_job_file_data(self):
        bad_fields = []
        for field_name in ['name', 'fund_code']:
            if self.value_contains_placeholder(self.data[field_name]):
                bad_fields.append(field_name)
        job_order = self.data['job_order']
        for jo_field_name in job_order.keys():
            if self.value_contains_placeholder(job_order[jo_field_name]):
                bad_fields.append("job_order.{}".format(jo_field_name))
        if bad_fields:
            raise IncompleteJobFileException("Please fill in TODO field(s): {}".format(', '.join(bad_fields)))

    @staticmethod
    def value_contains_placeholder(obj):
        if isinstance(obj, dict):
            if obj['class'] == 'File':
                return obj['path'] in USER_PLACEHOLDERS
            else:
                raise ValueError("Unknown class {}".format(obj['class']))
        else:
            return obj in USER_PLACEHOLDERS


class JobQuestionnaire(object):
    """
    Creates a placeholder job file based on pass in questionnaire
    """
    def __init__(self, questionnaire):
        """
        :param questionnaire: dict: questionnaire returned from bespin api
        """
        self.questionnaire = questionnaire

    def create_job_file_with_placeholders(self):
        return JobFile(workflow_tag=self.questionnaire['slug'],
                       name=USER_VALUE_PLACEHOLDER, fund_code=USER_VALUE_PLACEHOLDER,
                       job_order=self.format_user_fields())

    def format_user_fields(self):
        user_fields = json.loads(self.questionnaire['user_fields_json'])
        formatted_user_fields = {}
        for user_field in user_fields:
            field_type = user_field.get('type')
            field_name = user_field.get('name')
            if isinstance(field_type, dict):
                if field_type['type'] == 'array':
                    value = self.create_placeholder_value(field_type['items'], is_array=True)
                else:
                    value = self.create_placeholder_value(field_type['type'], is_array=False)
            else:
                value = self.create_placeholder_value(field_type, is_array=False)
            formatted_user_fields[field_name] = value
        return formatted_user_fields

    def create_placeholder_value(self, type_name, is_array):
        if is_array:
            return [self.create_placeholder_value(type_name, is_array=False)]
        else:  # single item type
            placeholder = USER_PLACEHOLDER_DICT.get(type_name)
            if not placeholder:
                return USER_VALUE_PLACEHOLDER
            return placeholder
