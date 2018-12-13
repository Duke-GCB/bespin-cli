from bespin.exceptions import WorkflowConfigurationNotFoundException
from bespin.dukeds import DDSFileUtil
from bespin.dukeds import PATH_PREFIX as DUKEDS_PATH_PREFIX
import yaml


class JobTemplate(object):
    """
    Contains data for creating a job.
    """
    def __init__(self, tag, name, fund_code, job_order):
        self.tag = tag
        self.name = name
        self.fund_code = fund_code
        self.job_order = job_order
        self.stage_group_id = None

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
        workflow_tag, version_str, config_tag = self.tag.split('/')
        workflow_configurations = api.workflow_configurations_list(tag=config_tag, workflow_tag=workflow_tag)
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

        job = api.job_templates_create_job(self.get_formatted_dict())
        dds_file_util = DDSFileUtil()
        for project_id in dds_project_ids:
            dds_file_util.give_download_permissions(project_id, dds_user_credential['dds_id'])
        return job

    def validate(self, api):
        # check with bespin-api to see if the job order is valid
        api.job_template_validate(self.get_formatted_dict())
        # make sure DukeDS files exist (this takes longer)
        self.get_dds_files_details()

    def get_formatted_dict(self):
        formatted_job_order = self.create_user_job_order()
        data = {
            'name': self.name,
            'fund_code': self.fund_code,
            'job_order': formatted_job_order,
            'tag': self.tag,
        }
        if self.stage_group_id:
            data['stage_group'] = self.stage_group_id
        return data


class JobTemplateLoader(object):
    """
    Creates JobFile based on an input file
    """
    def __init__(self, infile):
        self.data = yaml.load(infile)

    def create_job_template(self):
        job_template = JobTemplate(tag=self.data.get('tag'),
                                   name=self.data.get('name'),
                                   fund_code=self.data.get('fund_code'),
                                   job_order=self.data.get('job_order'))
        return job_template


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
