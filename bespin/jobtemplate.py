from bespin.exceptions import IncompleteJobTemplateException, WorkflowConfigurationNotFoundException
from bespin.dukeds import DDSFileUtil
from bespin.dukeds import PATH_PREFIX as DUKEDS_PATH_PREFIX
import yaml

STRING_VALUE_PLACEHOLDER = "<String Value>"
INT_VALUE_PLACEHOLDER = "<Integer Value>"
FILE_PLACEHOLDER = "dds://<Project Name>/<File Path>"
USER_PLACEHOLDER_VALUES = [STRING_VALUE_PLACEHOLDER, INT_VALUE_PLACEHOLDER, FILE_PLACEHOLDER]
USER_PLACEHOLDER_DICT = {
    'File': {
        "class": "File",
        "path": FILE_PLACEHOLDER
    },
    'int': INT_VALUE_PLACEHOLDER,
    'string': STRING_VALUE_PLACEHOLDER,
    'NamedFASTQFilePairType': {
        "name": STRING_VALUE_PLACEHOLDER,
        "file1": {
            "class": "File",
            "path": FILE_PLACEHOLDER
        },
        "file2": {
            "class": "File",
            "path": FILE_PLACEHOLDER
        }
    },
    'FASTQReadPairType': {
        "name": STRING_VALUE_PLACEHOLDER,
        "read1_files": [{
            "class": "File",
            "path": FILE_PLACEHOLDER
        }],
        "read2_files": [{
            "class": "File",
            "path": FILE_PLACEHOLDER
        }]
    }
}


class JobTemplate(object):
    """
    Contains data for creating a job.
    """
    def __init__(self, tag, name, fund_code, job_order, job_vm_strategy_id=None):
        self.tag = tag
        self.name = name
        self.fund_code = fund_code
        self.job_order = job_order
        self.job_vm_strategy_id = job_vm_strategy_id
        self.stage_group_id = None

    def to_dict(self):
        data = {
            'name': self.name,
            'fund_code': self.fund_code,
            'job_order': self.job_order,
            'tag': self.tag,
        }
        if self.stage_group_id:
            data['stage_group'] = self.stage_group_id
        if self.job_vm_strategy_id:
            data['job_vm_strategy'] = self.job_vm_strategy_id
        return data

    def create_user_job_order(self):
        """
        Format job order replacing dds remote file paths with filenames that will be staged
        :return: dict: job order for running CWL
        """
        user_job_order = self.job_order.copy()
        formatter = JobOrderFormatFiles()
        formatter.walk(user_job_order)
        return user_job_order

    def get_dds_files_details(self):
        """
        Get dds files info based on job_order
        :return: [(dds_file, staging_filename)]
        """
        job_order_details = JobOrderFileDetails()
        job_order_details.walk(self.job_order)
        return job_order_details.dds_files

    def read_workflow_configuration(self, api):
        workflow_configurations = api.workflow_configurations_list(tag=self.tag)
        if workflow_configurations:
            return workflow_configurations[0]
        raise WorkflowConfigurationNotFoundException(
            "Unable to find workflow configuration for tag {}".format(self.tag)
        )

    def create_job(self, api):
        """
        Create a job using the passed on api
        :param api: BespinApi
        :return: dict: job dictionary returned from bespin api
        """
        dds_user_credential = api.dds_user_credentials_list()[0]
        self.read_workflow_configuration(api)
        stage_group = api.stage_group_post()
        self.stage_group_id = stage_group['id']
        dds_project_ids = set()
        sequence = 0
        for dds_file, path in self.get_dds_files_details():
            file_size = dds_file.current_version['upload']['size']
            api.dds_job_input_files_post(dds_file.project_id, dds_file.id, path, 0, sequence,
                                         dds_user_credential['id'], stage_group_id=self.stage_group_id,
                                         size=file_size)
            sequence += 1
            dds_project_ids.add(dds_file.project_id)
        self.job_order = self.create_user_job_order()
        job = api.job_templates_create_job(self.to_dict())
        dds_file_util = DDSFileUtil()
        for project_id in dds_project_ids:
            dds_file_util.give_download_permissions(project_id, dds_user_credential['dds_id'])
        return job

    def verify_job(self, api):
        self.read_workflow_configuration(api)  # workflow configuration must exist
        self.get_dds_files_details()  # DukeDS input files must exist
        self.create_user_job_order()  # verify that we can generate a job order


class JobTemplateLoader(object):
    """
    Creates JobFile based on an input file
    """
    def __init__(self, infile):
        self.data = yaml.load(infile)

    def create_job_template(self, vm_strategy_id):
        self.validate_job_file_data()
        job_template = JobTemplate(tag=self.data['tag'],
                                   name=self.data['name'],
                                   fund_code=self.data['fund_code'],
                                   job_order=self.data['job_order'],
                                   job_vm_strategy_id=vm_strategy_id)
        return job_template

    def validate_job_file_data(self):
        bad_fields = []
        for field_name in ['name', 'fund_code']:
            if self.data[field_name] in USER_PLACEHOLDER_VALUES:
                bad_fields.append(field_name)
        checker = JobOrderPlaceholderCheck()
        checker.walk(self.data['job_order'])
        bad_fields.extend(['job_order.{}'.format(key) for key in checker.keys_with_placeholders])
        if bad_fields:
            bad_fields.sort()
            bad_fields_str = ', '.join(bad_fields)
            error_msg = "Please fill in placeholder values for field(s): {}".format(bad_fields_str)
            raise IncompleteJobTemplateException(error_msg)


class JobConfiguration(object):
    """
    Creates a placeholder job file based on workflow_configuration
    """
    def __init__(self, workflow_configuration):
        self.workflow_configuration = workflow_configuration

    def create_job_template_with_placeholders(self):
        return JobTemplate(tag=self.workflow_configuration['tag'],
                           name=STRING_VALUE_PLACEHOLDER, fund_code=STRING_VALUE_PLACEHOLDER,
                           job_order=self.format_user_fields())

    def format_user_fields(self):
        user_fields = self.workflow_configuration['user_fields']
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
                return STRING_VALUE_PLACEHOLDER
            return placeholder


class JobOrderWalker(object):
    def walk(self, obj):
        for key in obj.keys():
            self._walk_job_order(key, obj[key])

    def _walk_job_order(self, top_level_key, obj):
        if self._is_list_but_not_string(obj):
            return [self._walk_job_order(top_level_key, item) for item in obj]
        elif isinstance(obj, dict):
            if 'class' in obj.keys():
                self.on_class_value(top_level_key, obj)
            else:
                for key in obj:
                    self._walk_job_order(top_level_key, obj[key])
        else:
            # base object string or int or something
            self.on_simple_value(top_level_key, obj)

    @staticmethod
    def _is_list_but_not_string(obj):
        return isinstance(obj, list) and not isinstance(obj, str)

    def on_class_value(self, top_level_key, value):
        pass

    def on_simple_value(self, top_level_key, value):
        pass

    @staticmethod
    def format_file_path(path):
        """
        Create a valid file path based on a dds placeholder url
        :param path: str: format dds://<projectname>/<filepath>
        :return: str: file path to be used for staging data when running the workflow
        """
        if path.startswith(DUKEDS_PATH_PREFIX):
            return path.replace(DUKEDS_PATH_PREFIX, "dds_").replace("/", "_").replace(":", "_")
        return path


class JobOrderPlaceholderCheck(JobOrderWalker):
    def __init__(self):
        self.keys_with_placeholders = set()

    def on_class_value(self, top_level_key, value):
        if value['class'] == 'File':
            path = value.get('path')
            if path and path in USER_PLACEHOLDER_VALUES:
                self.keys_with_placeholders.add(top_level_key)

    def on_simple_value(self, top_level_key, value):
        if value in USER_PLACEHOLDER_VALUES:
            self.keys_with_placeholders.add(top_level_key)


class JobOrderFormatFiles(JobOrderWalker):
    def on_class_value(self, top_level_key, value):
        if value['class'] == 'File':
            path = value.get('path')
            if path:
                value['path'] = self.format_file_path(path)


class JobOrderFileDetails(JobOrderWalker):
    def __init__(self):
        self.dds_file_util = DDSFileUtil()
        self.dds_files = []

    def on_class_value(self, top_level_key, value):
        if value['class'] == 'File':
            path = value.get('path')
            if path and path.startswith(DUKEDS_PATH_PREFIX):
                dds_file = self.dds_file_util.find_file_for_path(path)
                self.dds_files.append((dds_file, self.format_file_path(path)))
