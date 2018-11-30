from __future__ import print_function
from bespin.config import ConfigFile
from bespin.api import BespinApi
from bespin.workflow import CWLWorkflowVersion
from bespin.jobtemplate import JobTemplateLoader
from tabulate import tabulate
import yaml
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

    def workflows_list(self, all_versions):
        """
        Print out a table of workflows/questionnaires
        :param all_versions: bool: when true show all versions otherwise show most recent
        """
        api = self._create_api()
        workflow_data = WorkflowDetails(api, all_versions)
        print(Table(workflow_data.column_names, workflow_data.get_column_data()))

    def workflow_configuration_job_order_show(self, workflow_configuration_id, outfile):
        api = self._create_api()
        workflow_configuration = api.workflow_configurations_get(workflow_configuration_id)
        outfile.write(yaml.dump(workflow_configuration['system_job_order'], default_flow_style=False))

    def jobs_list(self):
        """
        Print out a table of current job statuses
        """
        api = self._create_api()
        jobs_list = JobsList(api)
        print(Table(jobs_list.column_names, jobs_list.get_column_data()))

    def job_template_init(self, tag, outfile):
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
            print("Edit this file filling in TODO fields then run `bespin jobs create {}` .".format(outfile.name))

    def create_job(self, infile, dry_run, vm_strategy=None):
        """
        Create a job based on an input job file (possibly created via init_job_template)
        Prints out job id.
        :param infile: file: input file to use for creating a job
        :param dry_run: boolean: when True do not actually create a job just validate the input
        :param vm_strategy: int: vm strategy id
        """
        api = self._create_api()
        job_template = JobTemplateLoader(infile).create_job_template(vm_strategy)
        if dry_run:
            job_template.verify_job(api)
            print("Job file is valid.")
        else:
            result = job_template.create_job(api)
            job_id = result['job']
            print("Created job {}".format(job_id))
            print("To start this job run `bespin jobs start {}` .".format(job_id))

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

    def list_share_groups(self):
        api = self._create_api()
        item_list = ShareGroupsList(api)
        print(Table(item_list.column_names, item_list.get_column_data()))

    def list_vm_strategies(self):
        api = self._create_api()
        item_list = VmStrategiesList(api)
        print(Table(item_list.column_names, item_list.get_column_data()))

    def workflow_configurations_list(self):
        api = self._create_api()
        item_list = WorkflowConfigurationsList(api)
        print(Table(item_list.column_names, item_list.get_column_data()))

    def create_workflow_configuration(self, name, workflow, default_vm_strategy, joborder_infile):
        api = self._create_api()
        joborder = yaml.load(joborder_infile)
        api.workflow_configurations_post(name, workflow, default_vm_strategy, joborder)

    def list_workflow_versions(self):
        api = self._create_api()
        item_list = WorkflowVersionsList(api)
        print(Table(item_list.column_names, item_list.get_column_data()))

    def create_workflow_version(self, workflow, version_num, description, url):
        api = self._create_api()
        workflow_version = CWLWorkflowVersion(workflow, version_num, description, url)
        workflow_version.create(api)


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
    TAG_COLUMN_NAME = "version tag"

    def __init__(self, api, all_versions):
        self.api = api
        self.all_versions = all_versions
        self.column_names = ["id", "name", self.TAG_COLUMN_NAME]

    def get_column_data(self):
        """
        Return list of dictionaries of workflow data.
        :return: [dict]: one record for each questionnaire
        """
        data = []
        for workflow in self.api.workflows_list():
            if len(workflow['versions']):
                versions = workflow['versions']
                if not self.all_versions:
                    versions = versions[-1:]
                for version_id in versions:
                    workflow_version = self.api.workflow_version_get(version_id)
                    for workflow_configuration in self.api.workflow_configurations_list(workflow_version=version_id):
                        tag = '{}/{}'.format(workflow_version['tag'], workflow_configuration['tag'])
                        workflow[self.TAG_COLUMN_NAME] = tag
                        data.append(dict(workflow))
        return data


class JobsList(object):
    """
    Creates column data based on current users's jobs
    """
    def __init__(self, api):
        self.api = api
        self.column_names = ["id", "name", "state", "step", "last_updated", "elapsed_hours", "workflow_tag"]

    def get_column_data(self):
        """
        Return list of dictionaries of workflow data.
        :return: [dict]: one record for each questionnaire
        """
        data = []
        for job in self.api.jobs_list():
            job['elapsed_hours'] = self.get_elapsed_hours(job.get('usage'))
            job['workflow_tag'] = self.get_workflow_tag(job['workflow_version'])
            data.append(job)
        return data

    def get_workflow_tag(self, workflow_version):
        """
        Lookup the workflow tag for the specified workflow version
        :param workflow_version: int: workflow version id to lookup tag for
        :return: str: tag associated with workflow_version
        """
        configurations = self.api.workflow_configurations_list(workflow_version=workflow_version)
        return configurations[0]['tag']

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


class VmStrategiesList(object):
    FLAVOR_NAME_FIELDNAME = "type"
    CPUS_FIELDNAME = "cpus"
    VOLUME_SIZE_FIELDNAME = "volume size (g)"
    def __init__(self, api):
        self.api = api
        self.column_names = ["id", "name", self.FLAVOR_NAME_FIELDNAME, self.CPUS_FIELDNAME, self.VOLUME_SIZE_FIELDNAME]

    def get_column_data(self):
        data = []
        for item in self.api.vm_strategies_list():
            self.add_new_fields(item)
            data.append(item)
        return data

    def add_new_fields(self, item):
        volume_size_factor = item['volume_size_factor']
        volume_size_base = item['volume_size_base']
        vm_flavor_name = item["vm_flavor"]["name"]
        vm_flavor_cpus = item["vm_flavor"]["cpus"]

        item[self.FLAVOR_NAME_FIELDNAME] = vm_flavor_name
        item[self.CPUS_FIELDNAME] = vm_flavor_cpus

        volume_size_format = "{} x Input Data Size + {}"
        item[self.VOLUME_SIZE_FIELDNAME] = volume_size_format.format(volume_size_factor, volume_size_base)


class WorkflowConfigurationsList(object):
    WORKFLOW_FIELDNAME = "workflow"
    SHARE_GROUP_FIELDNAME = "share group"
    DEFAULT_VM_STRATEGY_FIELDNAME = "Default VM Strategy"
    def __init__(self, api):
        self.api = api
        self.column_names = ["id", "tag", self.WORKFLOW_FIELDNAME, self.SHARE_GROUP_FIELDNAME,
                             self.DEFAULT_VM_STRATEGY_FIELDNAME]

    def get_column_data(self):
        data = []
        for item in self.api.workflow_configurations_list():
            self.add_new_fields(item)
            data.append(item)
        return data

    def add_new_fields(self, item):
        workflow = self.api.workflow_get(item['workflow'])
        self.add_field(item, self.WORKFLOW_FIELDNAME, workflow, 'tag')
        share_group = self.api.share_group_get(item['share_group'])
        self.add_field(item, self.SHARE_GROUP_FIELDNAME, share_group, 'name')
        vm_strategy = self.api.vm_strategy_get(item['default_vm_strategy'])
        self.add_field(item, self.DEFAULT_VM_STRATEGY_FIELDNAME, vm_strategy, 'name')

    @staticmethod
    def add_field(dest, dest_fieldname, source, source_fieldname):
        dest[dest_fieldname] = "{} ({})".format(source[source_fieldname], source['id'])


class WorkflowVersionsList(object):
    WORKFLOW_FIELDNAME="workflow"
    def __init__(self, api):
        self.api = api
        self.column_names = ["id", "description", self.WORKFLOW_FIELDNAME, "version", "url"]

    def get_column_data(self):
        data = []
        for item in self.api.workflow_versions_list():
            self.add_new_fields(item)
            data.append(item)
        return data

    def add_new_fields(self, item):
        workflow = self.api.workflow_get(item['workflow'])
        self.add_field(item, self.WORKFLOW_FIELDNAME, workflow, 'tag')

    @staticmethod
    def add_field(dest, dest_fieldname, source, source_fieldname):
        dest[dest_fieldname] = "{} ({})".format(source[source_fieldname], source['id'])
