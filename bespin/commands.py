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
           "class":"File",
            "path": USER_FILE_PLACEHOLDER},
        "file2": {
            "class":"File",
            "path": USER_FILE_PLACEHOLDER
        }
    }
}


class Commands(object):
    def __init__(self, version_str, user_agent_str):
        self.version_str = version_str
        self.user_agent_str = user_agent_str

    def _create_api(self):
        config = ConfigFile().read_or_create_config()
        return BespinApi(config, user_agent_str=self.user_agent_str)

    def workflows_list(self):
        api = self._create_api()
        workflow_data = WorkflowDetails(api)
        print(Table(workflow_data.column_names, workflow_data.get_column_data()))

    def jobs_list(self):
        column_names = ["id", "name", "state", "step", "fund_code", "created", "last_updated"]
        api = self._create_api()
        print(Table(column_names, api.jobs_list()))

    def init_job(self, slug, outfile):
        api = self._create_api()
        questionnaire = api.questionnaires_list(slug=slug)[0]
        job_file = JobQuestionnaire(questionnaire).create_job_file_with_placeholders()
        outfile.write(job_file.yaml_str())
        if outfile != sys.stdout:
            print("Wrote job file {}.".format(outfile.name))
            print("Edit this file filling in TODO fields then run `bespin jobs create {}` .".format(outfile.name))

    def create_job(self, infile):
        api = self._create_api()
        job_file = JobFileLoader(infile).create_job_file()
        job = job_file.create_job(api)
        print("Created job {}".format(job['id']))

    def start_job(self, job_id, token=None):
        api = self._create_api()
        if token:
            api.authorize_job(job_id, token)
            print("Set run token for job {}".format(job_id))
        api.start_job(job_id)
        print("Started job {}".format(job_id))

    def cancel_job(self, job_id):
        api = self._create_api()
        api.cancel_job(job_id)
        print("Canceled job {}".format(job_id))

    def restart_job(self, job_id):
        api = self._create_api()
        api.restart_job(job_id)
        print("Restarted job {}".format(job_id))

    def delete_job(self, job_id):
        api = self._create_api()
        api.delete_job(job_id)
        print("Deleted job {}".format(job_id))


class Table(object):
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
    SLUG_COLUMN_NAME = "latest version slug"

    def __init__(self, api, only_latest_versions=True):
        self.api = api
        self.only_latest_versions = only_latest_versions
        self.column_names = ["id", "name", self.SLUG_COLUMN_NAME]

    def get_column_data(self):
        data = []
        for workflow in self.api.workflows_list():
            included_versions = workflow['versions']
            if self.only_latest_versions:
                included_versions = [included_versions[-1]]
            for version_id in included_versions:
                for questionnaire in self.api.questionnaires_list(workflow_version=version_id):
                    workflow[self.SLUG_COLUMN_NAME] = questionnaire['slug']
                    data.append(workflow)
        return data


class JobFile(object):
    def __init__(self, workflow_slug, name, fund_code, params):
        self.workflow_slug = workflow_slug
        self.name = name
        self.fund_code = fund_code
        self.params = params

    def yaml_str(self):
        data = {
            'name': self.name,
            'fund_code': self.fund_code,
            'params': self.params,
            'workflow_slug': self.workflow_slug,
        }
        return yaml.dump(data, default_flow_style=False)

    def create_user_job_order_json(self):
        user_job_order = {}
        for key in self.params.keys():
            value = self.params[key]
            if isinstance(value, dict) and value['class'] == 'File':
                value['path'] = self.format_file_path(value['path'])
            user_job_order[key] = value
        return json.dumps(user_job_order)

    @staticmethod
    def format_file_path(path):
        return path.replace("dds://", "dds_").replace("/", "_").replace(":", "_")

    def get_dds_files_details(self):
        dds_file_util = DDSFileUtil()
        dds_files = []
        for key in self.params.keys():
            value = self.params[key]
            if isinstance(value, dict) and value['class'] == 'File':
                path = value['path']
                dds_file = dds_file_util.find_file_for_path(path)
                dds_files.append((dds_file, self.format_file_path(path)))
        return dds_files

    def create_job(self, api):
        dds_user_credential = api.dds_user_credentials_list()[0]
        questionnaire = api.questionnaires_list(slug=self.workflow_slug)[0]
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
    def __init__(self, infile):
        self.data = yaml.load(infile)

    def create_job_file(self):
        self.validate_job_file_data()
        job_file = JobFile(workflow_slug=self.data['workflow_slug'],
                           name=self.data['name'],
                           fund_code=self.data['fund_code'],
                           params=self.data['params'])
        return job_file

    def validate_job_file_data(self):
        bad_fields = []
        for field_name in ['name', 'fund_code']:
            if self.value_contains_placeholder(self.data[field_name]):
                bad_fields.append(field_name)
        params = self.data['params']
        for param_field_name in params.keys():
            if self.value_contains_placeholder(params[param_field_name]):
                bad_fields.append("param.{}".format(param_field_name))
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
    def __init__(self, questionnaire):
        self.questionnaire = questionnaire

    def create_job_file_with_placeholders(self):
        return JobFile(workflow_slug=self.questionnaire['slug'],
                       name=USER_VALUE_PLACEHOLDER, fund_code=USER_VALUE_PLACEHOLDER,
                       params=self.format_user_fields())

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
        else: # single item type
            placeholder = USER_PLACEHOLDER_DICT.get(type_name)
            if not placeholder:
                return USER_VALUE_PLACEHOLDER
            return placeholder
