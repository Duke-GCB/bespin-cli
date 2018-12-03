from __future__ import print_function
import argparse
import sys

DESCRIPTION_STR = "bespin ({}) Run bioinformatics workflows"


class ArgParser(object):
    def __init__(self, version_str, target_object):
        """
        Create argument parser with the specified version string that will call the appropriate methods
        in target_object when those commands are selected.
        :param version_str: str: version of bespin-cli
        :param target_object: object: object with methods named the same as the commands
        """
        self.target_object = target_object
        description = DESCRIPTION_STR.format(version_str)
        self.argument_parser = argparse.ArgumentParser(description=description)
        self.subparsers = self.argument_parser.add_subparsers()
        self._add_commands_to_parser()

    def _add_commands_to_parser(self):
        self._add_command(WorkflowCommand)
        self._add_command(WorkflowVersionCommand)
        self._add_command(WorkflowConfigCommand)
        self._add_command(ShareGroupCommand)
        self._add_command(VMConfigCommand)
        self._add_command(JobTemplateCommand)
        self._add_command(JobCommand)

    def _add_command(self, command_constructor):
            command = command_constructor(self.target_object)
            command_parser = self.subparsers.add_parser(command.name,
                                                        aliases=[command.alias],
                                                        description=command.description)
            command_subparsers = command_parser.add_subparsers()
            command.add_actions(command_subparsers)

    def parse_and_run_commands(self, args=None):
        """
        Parses arguments from args or command line if args is None.
        :param args: optional set of arguments to parse
        """
        parsed_args = self.argument_parser.parse_args(args)
        if hasattr(parsed_args, 'func'):
            parsed_args.func(parsed_args)
        else:
            self.argument_parser.print_help()


class WorkflowCommand(object):
    name = "workflow"
    alias = "wf"
    description = "workflow commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list workflows')
        exclusive_flags = list_parser.add_mutually_exclusive_group()
        exclusive_flags.add_argument('--all', action='store_true',
                                  help='show all workflow versions instead of just the most recent.')
        exclusive_flags.add_argument('--short', action='store_true',
                                  help='show short list of only workflows excluding version/configuration data.')
        list_parser.add_argument('tag', nargs='?', metavar='WORKFLOW_TAG', help='Workflow tag to filter by')
        list_parser.set_defaults(func=self._run_workflows_list)

        create_parser = subparsers.add_parser('create', description='create a workflow')
        create_parser.add_argument('--name', required=True,
                                   help='Name to describe the workflow.')
        create_parser.add_argument('--tag', required=True,
                                   help='Unique tag of the workflow.')
        create_parser.set_defaults(func=self._run_workflow_create)

    def _run_workflows_list(self, args):
        self.target.workflows_list(args.all, args.short, args.tag)

    def _run_workflow_create(self, args):
        self.target.workflow_create(args.name, args.tag)


class WorkflowVersionCommand(object):
    name = "workflow-version"
    alias = "wfv"
    description = "workflow version commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list workflow versions')
        list_parser.add_argument('--workflow', metavar='WORKFLOW_TAG',
                                 help='Filter list based on a workflow tag.')
        list_parser.set_defaults(func=self._run_list_workflow_versions_list)

        create_parser = subparsers.add_parser('create', description='create new workflow version')
        create_parser.add_argument('--workflow', metavar='WORKFLOW_TAG', required=True,
                                   help='Tag specifying workflow to assign this workflow version to')
        create_parser.add_argument('--url', required=True,
                                   help='URL that specifies the packed CWL workflow')
        create_parser.add_argument('--description', required=True,
                                   help='Workflow version description')
        create_parser.add_argument('--version', required=True,
                                   help='Version number or "auto" to automatically determine next version.')
        create_parser.set_defaults(func=self._run_workflow_version_create)

    def _run_list_workflow_versions_list(self, args):
        self.target.workflow_versions_list(args.workflow)

    def _run_workflow_version_create(self, args):
        self.target.workflow_version_create(args.workflow, args.url, args.description, args.version)


class WorkflowConfigCommand(object):
    name = "workflow-config"
    alias = "wfc"
    description = "workflow configuration commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list workflow configurations')
        list_parser.add_argument('--workflow', metavar='TAG',
                                 help='Filter list based on a workflow tag.')
        list_parser.set_defaults(func=self._run_list_workflow_configs)

        show_job_order_parser = subparsers.add_parser('show-job-order', description='Prints out job order associated '
                                                                                    'with this configuration')
        show_job_order_parser.add_argument('--workflow', metavar='WORKFLOW_TAG',
                                           help='Specifies workflow that contains the configuration to be printed.')
        show_job_order_parser.add_argument('--tag',
                                           help='Specifies which configuration within a workflow to use.')
        show_job_order_parser.add_argument('--outfile', type=argparse.FileType('w'), dest='outfile', default=sys.stdout,
                                           help='File to write job order into. Prints to stdout if not specified.')
        show_job_order_parser.set_defaults(func=self._run_show_job_order_workflow_config)

        create_parser = subparsers.add_parser('create', description='create new workflow configuration')
        create_parser.add_argument('--workflow', metavar='WORKFLOW_TAG', required=True,
                                   help='Tag specifying workflow to assign this workflow configuration to')
        create_parser.add_argument('--default-vm-config', required=True, metavar='VM_CONFIG_NAME',
                                   help='Name of the default VM configuration to use')
        create_parser.add_argument('--share-group', required=True, metavar='SHARE_GROUP_NAME',
                                   help='Name of the share group')
        create_parser.add_argument('--tag', required=True,
                                   help='Tag to assign to this worflow configuration')
        create_parser.add_argument('job_order', type=argparse.FileType('r'), help='job order file')
        create_parser.set_defaults(func=self._run_workflow_config_create)

    def _run_list_workflow_configs(self, args):
        self.target.workflow_configs_list(args.workflow)

    def _run_show_job_order_workflow_config(self, args):
        self.target.workflow_config_show_job_order(args.tag, args.workflow, args.outfile)

    def _run_workflow_config_create(self, args):
        self.target.workflow_config_create(args.workflow, args.default_vm_config, args.share_group, args.tag,
                                           args.job_order)


class ShareGroupCommand(object):
    name = "share-group"
    alias = "sg"
    description = "share group commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list share groups')
        list_parser.set_defaults(func=self._run_list_share_groups)

    def _run_list_share_groups(self, args):
        self.target.list_share_groups()


class VMConfigCommand(object):
    name = "vm-config"
    alias = "vmc"
    description = "VM configuration commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list VM configurations')
        list_parser.set_defaults(func=self._run_list_vm_configs)

    def _run_list_vm_configs(self, args):
        self.target.list_vm_configs()


class JobTemplateCommand(object):
    name = "job-template"
    alias = "jt"
    description = "job template commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        create_parser = subparsers.add_parser('create', description='create job template for a workflow tag')
        create_parser.add_argument('tag',
                                   help='Tag that specifies workflow version and config to create job template for')
        create_parser.add_argument('--outfile', type=argparse.FileType('w'), dest='outfile', default=sys.stdout,
                                   help='File to write job template into. Prints to stdout if not specified.')
        create_parser.set_defaults(func=self._run_create_job_template)

    def _run_create_job_template(self, args):
        self.target.job_template_create(args.tag, args.outfile)


class JobCommand(object):
    name = "job"
    alias = "j"
    description = "job commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        create_parser = subparsers.add_parser('create', description='create a job based on a job template file')
        create_parser.add_argument('job_template', type=argparse.FileType('r'), help='job template file')
        create_parser.set_defaults(func=self._create_job)

        run_parser = subparsers.add_parser('run', description='create and start a job based on a job template file')
        run_parser.add_argument('job_template', type=argparse.FileType('r'), help='job template file')
        run_parser.add_argument('--token', type=str, help='Token used to authorize job (if necessary)')
        run_parser.set_defaults(func=self._run_job)

        validate_parser = subparsers.add_parser('validate', description='validate a job template file')
        validate_parser.add_argument('job_template', type=argparse.FileType('r'), help='job template file')
        validate_parser.set_defaults(func=self._validate_job)

        list_parser = subparsers.add_parser('list', description='list jobs')
        list_parser.set_defaults(func=self._list_jobs)

        start_parser = subparsers.add_parser('start', description='start job')
        start_parser.add_argument('job_id', type=int)
        start_parser.add_argument('--token', type=str, help='Token used to authorize job (if necessary)')
        start_parser.set_defaults(func=self._start_job)

        cancel_parser = subparsers.add_parser('cancel', description='cancel job')
        cancel_parser.add_argument('job_id', type=int)
        cancel_parser.set_defaults(func=self._cancel_job)

        restart_parser = subparsers.add_parser('restart', description='restart job')
        restart_parser.add_argument('job_id', type=int)
        restart_parser.set_defaults(func=self._restart_job)

        delete_parser = subparsers.add_parser('delete', description='delete job')
        delete_parser.add_argument('job_id', type=int)
        delete_parser.set_defaults(func=self._delete_job)

    def _create_job(self, args):
        self.target.job_create(args.job_template)

    def _run_job(self, args):
        self.target.job_run(args.job_template, args.token)

    def _validate_job(self, args):
        self.target.job_validate(args.job_template)

    def _list_jobs(self, args):
        self.target.jobs_list()

    def _start_job(self, args):
        self.target.start_job(args.job_id, args.token)

    def _cancel_job(self, args):
        self.target.cancel_job(args.job_id)

    def _restart_job(self, args):
        self.target.restart_job(args.job_id)

    def _delete_job(self, args):
        self.target.delete_job(args.job_id)
