from __future__ import print_function
from bespin.config import ConfigFile
from bespin.api import BespinApi
from bespin.workflow import CWLWorkflowVersion, BespinWorkflowLoader
from bespin.tool_details import ToolDetailsExtractor
from bespin.jobtemplate import JobTemplateLoader
from bespin.exceptions import WorkflowConfigurationNotFoundException, UserInputException
from tabulate import tabulate
import yaml
import json
import sys
from decimal import Decimal, ROUND_HALF_UP


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

    def _print_details_as_table(self, details):
        print(Table(details.column_names, details.get_column_data()))

    def workflows_list(self, all_versions, short_format, tag):
        """
        Print out a table of workflows and optionally the versions/configurations
        :param all_versions: bool: when true show all versions otherwise show most recent
        :param short_format: bool: when true show only workflow info
        :param tag: str: when true show all versions otherwise show most recent
        """
        api = self._create_api()
        if short_format:
            self._print_details_as_table(ShortWorkflowDetails(api, tag))
        else:
            self._print_details_as_table(FullWorkflowDetails(api, all_versions, tag))

    def workflow_create(self, name, tag):
        api = self._create_api()
        response = api.workflow_post(name, tag)
        print("Created workflow {}.".format(response['id']))

    def workflow_versions_list(self, workflow_tag):
        api = self._create_api()
        self._print_details_as_table(WorkflowVersionsList(api, workflow_tag))

    def workflow_version_create(self, url, workflow_type, workflow_path, version_info_url, override_tag=None,
                                override_version=None, validate=True):
        api = self._create_api()
        workflow_version = CWLWorkflowVersion(url, workflow_type, workflow_path, version_info_url,
                                              override_tag=override_tag, override_version=override_version,
                                              validate=validate)
        response = workflow_version.create(api)
        print("Created workflow version {}.".format(response['id']))

    @staticmethod
    def _raise_on_incompatible_workflow_type_and_path(workflow_type, workflow_path):
        if workflow_type == BespinWorkflowLoader.TYPE_DIRECT and workflow_path:
            # direct type does not use workflow_path
            msg = "Error: Do not provide path for {} workflows".format(BespinWorkflowLoader.TYPE_DIRECT)
            raise UserInputException(msg)
        elif workflow_type != BespinWorkflowLoader.TYPE_DIRECT and not workflow_path:
            # other types require workflow_path
            msg = "Error: path is required for {} workflows".format(workflow_type)
            raise UserInputException(msg)

    def workflow_version_validate(self, url, workflow_type, workflow_path, expected_tag=None, expected_version=None):
        self._raise_on_incompatible_workflow_type_and_path(workflow_type, workflow_path)
        workflow_version = CWLWorkflowVersion(url, workflow_type, workflow_path, validate=True)
        validated = workflow_version.validate_workflow(expected_tag, expected_version)
        print("Validated {} as '{}/{}'".format(url, validated.tag, validated.version))

    def workflow_tool_details_preview(self, url, workflow_type, workflow_path):
        self._raise_on_incompatible_workflow_type_and_path(workflow_type, workflow_path)
        workflow_version = CWLWorkflowVersion(url, workflow_type, workflow_path, validate=False)
        extractor = ToolDetailsExtractor(workflow_version)
        print(json.dumps(extractor.tool_details, indent=2))

    def workflow_tool_details_create(self, url, workflow_type, workflow_path):
        # May also override tag and version!
        self._raise_on_incompatible_workflow_type_and_path(workflow_type, workflow_path)
        workflow_version = CWLWorkflowVersion(url, workflow_type, workflow_path, validate=False)
        extractor = ToolDetailsExtractor(workflow_version)
        api = self._create_api()
        api_workflow_version = api.workflow_version_find_by_version_tag(extractor.version, extractor.tag)
        workflow_version_id = api_workflow_version['id']
        response = api.workflow_tool_details_post(workflow_version_id, extractor.tool_details)
        print("Created workflow tool details {}.".format(response['id']))

    def workflow_configs_list(self, workflow_tag):
        api = self._create_api()
        self._print_details_as_table(WorkflowConfigurationsList(api, workflow_tag))

    def workflow_config_show_job_order(self, tag, workflow_tag, outfile):
        api = self._create_api()
        configs = api.workflow_configurations_list(tag=tag, workflow_tag=workflow_tag)
        if not configs:
            msg = "Workflow configuration not found for tag {} and workflow {}".format(tag, workflow_tag)
            raise WorkflowConfigurationNotFoundException(msg)
        config = configs[0]
        outfile.write(yaml.dump(config['system_job_order'], default_flow_style=False))

    def workflow_config_create(self, workflow_tag, default_job_strategy_name, share_group_name, tag, joborder_infile):
        api = self._create_api()
        joborder = yaml.load(joborder_infile)
        workflow = api.workflow_get_for_tag(workflow_tag)
        default_job_strategy = api.job_strategy_get_for_name(default_job_strategy_name)
        share_group = api.share_group_get_for_name(share_group_name)
        response = api.workflow_configurations_post(tag,
                                                    workflow['id'],
                                                    default_job_strategy['id'],
                                                    share_group['id'],
                                                    joborder)
        print("Created workflow config {}.".format(response['id']))

    def share_groups_list(self):
        api = self._create_api()
        item_list = ShareGroupsList(api)
        self._print_details_as_table(item_list)

    def job_configs_list(self):
        api = self._create_api()
        item_list = JobStrategiesList(api)
        self._print_details_as_table(item_list)

    def jobs_list(self):
        """
        Print out a table of current job statuses
        """
        api = self._create_api()
        jobs_list = JobsList(api)
        self._print_details_as_table(jobs_list)

    def job_template_create(self, tag, outfile):
        """
        Write a sample job file with placeholder values to outfile
        :param tag: str: tag representing which workflow/questionnaire to use
        :param outfile: file: output file that will have the sample job data written to
        """
        api = self._create_api()
        job_file = api.job_templates_init(tag)
        outfile.write(yaml.dump(job_file, default_flow_style=False))
        if outfile != sys.stdout:
            print("Wrote job file {}.".format(outfile.name))
            print("Edit this file filling in TODO fields then run `bespin job create {}` .".format(outfile.name))

    def job_create(self, job_template_infile):
        """
        Create a job based on an input job file (possibly created via init_job_template)
        Prints out job id.
        :param job_template_infile: file: input file to use for creating a job
        """
        api = self._create_api()
        job_template = JobTemplateLoader(job_template_infile).create_job_template()
        result = job_template.create_job(api)
        job_id = result['job']
        print("Created job {}".format(job_id))
        print("To start this job run `bespin job start {}` .".format(job_id))

    def job_run(self, job_template_infile, token=None):
        """
        Creates and starts a job based on an input job file (possibly created via init_job_template)
        Prints out job id.
        :param job_template_infile: file: input file to use for creating a job
        :param token: str: token to use to authorize running the job
        """
        api = self._create_api()
        job_template = JobTemplateLoader(job_template_infile).create_job_template()
        result = job_template.create_job(api)
        job_id = result['job']
        print("Created job {}".format(job_id))
        if token:
            api.authorize_job(job_id, token)
            print("Set run token for job {}".format(job_id))
        api.start_job(job_id)
        print("Started job {}".format(job_id))

    def job_validate(self, job_template_infile):
        """
        Validates a job can be created for the specified job template.
        :param job_template_infile: file: input file to use for creating a job
        """
        api = self._create_api()
        job_template = JobTemplateLoader(job_template_infile).create_job_template()
        try:
            job_template.validate(api)
            print("Job file is valid.")
        except UserInputException:
            print("ERROR: Job template is invalid.")
            raise

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


class ShortWorkflowDetails(object):
    """
    Creates column data based on workflows
    """
    def __init__(self, api, tag):
        self.api = api
        self.tag = tag
        self.column_names = ["id", "name", "tag"]

    def get_column_data(self):
        """
        Return list of dictionaries of workflow data.
        :return: [dict]: one record for each questionnaire
        """
        data = []
        for workflow in self.api.workflows_list(self.tag):
            data.append(dict(workflow))
        return data


class FullWorkflowDetails(object):
    """
    Creates column data based on workflows/questionnaires
    """
    TAG_COLUMN_NAME = "job template tag"

    def __init__(self, api, all_versions, tag):
        self.api = api
        self.all_versions = all_versions
        self.tag = tag
        self.column_names = ["id", "name", self.TAG_COLUMN_NAME]

    def get_column_data(self):
        """
        Return list of dictionaries of workflow data.
        :return: [dict]: one record for each questionnaire
        """
        data = []
        for workflow in self.api.workflows_list(self.tag):
            if len(workflow['versions']):
                versions = workflow['versions']
                if not self.all_versions:
                    versions = versions[-1:]
                for version_id in versions:
                    workflow_version = self.api.workflow_version_get(version_id)
                    configurations = self.api.workflow_configurations_list(workflow_tag=workflow['tag'])
                    for workflow_configuration in configurations:
                        tag = '{}/{}'.format(workflow_version['tag'], workflow_configuration['tag'])
                        workflow[self.TAG_COLUMN_NAME] = tag
                        data.append(dict(workflow))
        return data


class WorkflowVersionsList(object):
    WORKFLOW_FIELDNAME="workflow tag"
    def __init__(self, api, workflow_tag):
        self.api = api
        self.workflow_tag = workflow_tag
        self.column_names = ["id", "description", self.WORKFLOW_FIELDNAME, "version", "url", "workflow_path"]

    def get_column_data(self):
        data = []
        for item in self.api.workflow_versions_list(self.workflow_tag):
            workflow = self.api.workflow_get(item['workflow'])
            item[self.WORKFLOW_FIELDNAME] = workflow['tag']
            data.append(item)
        return data


class WorkflowConfigurationsList(object):
    WORKFLOW_FIELDNAME = "workflow"
    SHARE_GROUP_FIELDNAME = "share group"
    DEFAULT_JOB_STRATEGY_FIELDNAME = "Default Job Strategy"

    def __init__(self, api, workflow_tag):
        self.api = api
        self.workflow_tag = workflow_tag
        self.column_names = ["id", "tag", self.WORKFLOW_FIELDNAME, self.SHARE_GROUP_FIELDNAME,
                             self.DEFAULT_JOB_STRATEGY_FIELDNAME]

    def get_column_data(self):
        data = []
        for item in self.api.workflow_configurations_list(workflow_tag=self.workflow_tag):
            self.add_new_fields(item)
            data.append(item)
        return data

    def add_new_fields(self, item):
        workflow = self.api.workflow_get(item['workflow'])
        item[self.WORKFLOW_FIELDNAME] = workflow['tag']
        share_group = self.api.share_group_get(item['share_group'])
        item[self.SHARE_GROUP_FIELDNAME] = share_group['name']
        job_strategy = self.api.job_strategy_get(item['default_job_strategy'])
        item[self.DEFAULT_JOB_STRATEGY_FIELDNAME] = job_strategy['name']


class JobsList(object):
    WORKFLOW_VERSION_TAG = "workflow_version_tag"
    """
    Creates column data based on current users's jobs
    """
    def __init__(self, api):
        self.api = api
        self.column_names = ["id", "name", "state", "step", "last_updated", "elapsed_hours", self.WORKFLOW_VERSION_TAG]

    def get_column_data(self):
        """
        Return list of dictionaries of workflow data.
        :return: [dict]: one record for each questionnaire
        """
        data = []
        for job in self.api.jobs_list():
            job['elapsed_hours'] = self.get_elapsed_hours(job.get('usage'))
            job[self.WORKFLOW_VERSION_TAG] = self.get_workflow_version_tag(job['workflow_version'])
            data.append(job)
        return data

    def get_workflow_version_tag(self, workflow_version_id):
        workflow_version = self.api.workflow_version_get(workflow_version_id)
        return workflow_version['tag']

    def get_elapsed_hours(self, usage):
        if usage:
            elapsed_hours = Decimal(usage.get('vm_hours'))
            # round to 1 decimal placec
            rounded_elapsed_hours = Decimal(elapsed_hours.quantize(Decimal('.1'), rounding=ROUND_HALF_UP))
            return float(rounded_elapsed_hours)
        return None


class ShareGroupsList(object):
    def __init__(self, api):
        self.api = api
        self.column_names = ["id", "name", "email"]

    def get_column_data(self):
        data = []
        for item in self.api.share_groups_list():
            data.append(item)
        return data


class JobStrategiesList(object):
    FLAVOR_NAME_FIELDNAME = "type"
    CPUS_FIELDNAME = "cpus"
    JOB_MEMORY_FIELDNAME = "memory"
    VOLUME_SIZE_FIELDNAME = "volume size (g)"
    def __init__(self, api):
        self.api = api
        self.column_names = ["id", "name", self.FLAVOR_NAME_FIELDNAME, self.CPUS_FIELDNAME, self.JOB_MEMORY_FIELDNAME,
                             self.VOLUME_SIZE_FIELDNAME]

    def get_column_data(self):
        data = []
        for item in self.api.job_strategies_list():
            self.add_new_fields(item)
            data.append(item)
        return data

    def add_new_fields(self, item):
        volume_size_factor = item['volume_size_factor']
        volume_size_base = item['volume_size_base']
        job_flavor_name = item["job_flavor"]["name"]
        job_flavor_cpus = item["job_flavor"]["cpus"]
        job_memory = item["job_flavor"]["memory"]

        item[self.FLAVOR_NAME_FIELDNAME] = job_flavor_name
        item[self.CPUS_FIELDNAME] = job_flavor_cpus
        item[self.JOB_MEMORY_FIELDNAME] = job_memory

        volume_size_format = "{} x Input Data Size + {}"
        item[self.VOLUME_SIZE_FIELDNAME] = volume_size_format.format(volume_size_factor, volume_size_base)
