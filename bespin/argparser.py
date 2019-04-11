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
        self._add_command(JobConfigCommand)
        self._add_command(JobTemplateCommand)
        self._add_command(JobCommand)

    def _add_command(self, command_constructor):
            command = command_constructor(self.target_object)
            command_parser = self.subparsers.add_parser(command.name,
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
        list_parser.set_defaults(func=self._list)

        create_parser = subparsers.add_parser('create', description='create a workflow')
        create_parser.add_argument('--name', required=True,
                                   help='Name to describe the workflow.')
        create_parser.add_argument('--tag', required=True,
                                   help='Unique tag of the workflow.')
        create_parser.set_defaults(func=self._create)

    def _list(self, args):
        self.target.workflows_list(all_versions=args.all,
                                   short_format=args.short,
                                   tag=args.tag)

    def _create(self, args):
        self.target.workflow_create(name=args.name,
                                    tag=args.tag)


class WorkflowVersionCommand(object):
    name = "workflow-version"
    description = "workflow version commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list workflow versions')
        list_parser.add_argument('--workflow', metavar='WORKFLOW_TAG',
                                 help='Filter list based on a workflow tag.')
        list_parser.set_defaults(func=self._list)

        create_parser = subparsers.add_parser('create', description='create new workflow version')
        create_parser.add_argument('--workflow', metavar='WORKFLOW_TAG', required=True,
                                   help='Tag specifying workflow to assign this workflow version to')
        create_parser.add_argument('--url', required=True,
                                   help='URL that specifies the CWL workflow')
        create_parser.add_argument('--description', required=True,
                                   help='Workflow version description')
        create_parser.add_argument('--version', required=True,
                                   help='Version number or "auto" to automatically determine next version.')
        create_parser.set_defaults(func=self._create)

        validate_parser = subparsers.add_parser('validate', description='Validate workflow according to bespin standards')
        validate_parser.add_argument('--url', required=True, help='URL that specifies the CWL workflow')
        validate_parser.add_argument('--type', required=True, help='Type of worklfow (zipped or packed)')
        validate_parser.add_argument('--path', required=True, help='Path to the workflow to run (relative path in '
                                                                   'unzipped archive or #main for packed workflows)')
        validate_parser.set_defaults(func=self._validate)

    def _list(self, args):
        self.target.workflow_versions_list(workflow_tag=args.workflow)

    def _create(self, args):
        self.target.workflow_version_create(workflow_tag=args.workflow,
                                            url=args.url,
                                            description=args.description,
                                            version=args.version)

    def _validate(self, args):
        self.target.workflow_version_validate(url=args.url,
                                              workflow_type=args.type,
                                              workflow_path=args.path)


class WorkflowConfigCommand(object):
    name = "workflow-config"
    description = "workflow configuration commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list workflow configurations')
        list_parser.add_argument('--workflow', metavar='TAG',
                                 help='Filter list based on a workflow tag.')
        list_parser.set_defaults(func=self._list)

        show_job_order_parser = subparsers.add_parser('show-job-order', description='Prints out job order associated '
                                                                                    'with this configuration')
        show_job_order_parser.add_argument('--workflow', metavar='WORKFLOW_TAG', required=True,
                                           help='Specifies workflow that contains the configuration to be printed.')
        show_job_order_parser.add_argument('--tag', required=True,
                                           help='Specifies which configuration within a workflow to use.')
        show_job_order_parser.add_argument('--outfile', type=argparse.FileType('w'), dest='outfile', default=sys.stdout,
                                           help='File to write job order into. Prints to stdout if not specified.')
        show_job_order_parser.set_defaults(func=self._show_job_order)

        create_parser = subparsers.add_parser('create', description='create new workflow configuration')
        create_parser.add_argument('--workflow', metavar='WORKFLOW_TAG', required=True,
                                   help='Tag specifying workflow to assign this workflow configuration to')
        create_parser.add_argument('--default-job-config', required=True, metavar='JOB_CONFIG_NAME',
                                   help='Name of the default job configuration to use')
        create_parser.add_argument('--share-group', required=True, metavar='SHARE_GROUP_NAME',
                                   help='Name of the share group')
        create_parser.add_argument('--tag', required=True,
                                   help='Tag to assign to this worflow configuration')
        create_parser.add_argument('job_order', type=argparse.FileType('r'), help='job order file')
        create_parser.set_defaults(func=self._create)

    def _list(self, args):
        self.target.workflow_configs_list(workflow_tag=args.workflow)

    def _show_job_order(self, args):
        self.target.workflow_config_show_job_order(tag=args.tag,
                                                   workflow_tag=args.workflow,
                                                   outfile=args.outfile)

    def _create(self, args):
        self.target.workflow_config_create(
            workflow_tag=args.workflow,
            default_job_strategy_name=args.default_job_config,
            share_group_name=args.share_group,
            tag=args.tag,
            joborder_infile=args.job_order)


class ShareGroupCommand(object):
    name = "share-group"
    description = "share group commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list share groups')
        list_parser.set_defaults(func=self._list)

    def _list(self, args):
        self.target.share_groups_list()


class JobConfigCommand(object):
    name = "job-config"
    description = "Job configuration commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        list_parser = subparsers.add_parser('list', description='list VM configurations')
        list_parser.set_defaults(func=self._list)

    def _list(self, args):
        self.target.job_configs_list()


class JobTemplateCommand(object):
    name = "job-template"
    description = "job template commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        create_parser = subparsers.add_parser('create', description='create job template for a workflow tag')
        create_parser.add_argument('tag',
                                   help='Tag that specifies workflow version and config to create job template for')
        create_parser.add_argument('--outfile', type=argparse.FileType('w'), dest='outfile', default=sys.stdout,
                                   help='File to write job template into. Prints to stdout if not specified.')
        create_parser.set_defaults(func=self._create)

    def _create(self, args):
        self.target.job_template_create(tag=args.tag, outfile=args.outfile)


class JobCommand(object):
    name = "job"
    description = "job commands"

    def __init__(self, target):
        self.target = target

    def add_actions(self, subparsers):
        create_parser = subparsers.add_parser('create', description='create a job based on a job template file')
        create_parser.add_argument('job_template', type=argparse.FileType('r'), help='job template file')
        create_parser.set_defaults(func=self._create)

        run_parser = subparsers.add_parser('run', description='create and start a job based on a job template file')
        run_parser.add_argument('job_template', type=argparse.FileType('r'), help='job template file')
        run_parser.add_argument('--token', type=str, help='Token used to authorize job (if necessary)')
        run_parser.set_defaults(func=self._run)

        validate_parser = subparsers.add_parser('validate', description='validate a job template file')
        validate_parser.add_argument('job_template', type=argparse.FileType('r'), help='job template file')
        validate_parser.set_defaults(func=self._validate)

        list_parser = subparsers.add_parser('list', description='list jobs')
        list_parser.set_defaults(func=self._list)

        start_parser = subparsers.add_parser('start', description='start job')
        start_parser.add_argument('job_id', type=int)
        start_parser.add_argument('--token', type=str, help='Token used to authorize job (if necessary)')
        start_parser.set_defaults(func=self._start)

        cancel_parser = subparsers.add_parser('cancel', description='cancel job')
        cancel_parser.add_argument('job_id', type=int)
        cancel_parser.set_defaults(func=self._cancel)

        restart_parser = subparsers.add_parser('restart', description='restart job')
        restart_parser.add_argument('job_id', type=int)
        restart_parser.set_defaults(func=self._restart)

        delete_parser = subparsers.add_parser('delete', description='delete job')
        delete_parser.add_argument('job_id', type=int)
        delete_parser.set_defaults(func=self._delete)

    def _create(self, args):
        self.target.job_create(job_template_infile=args.job_template)

    def _run(self, args):
        self.target.job_run(job_template_infile=args.job_template, token=args.token)

    def _validate(self, args):
        self.target.job_validate(job_template_infile=args.job_template)

    def _list(self, args):
        self.target.jobs_list()

    def _start(self, args):
        self.target.start_job(job_id=args.job_id, token=args.token)

    def _cancel(self, args):
        self.target.cancel_job(job_id=args.job_id)

    def _restart(self, args):
        self.target.restart_job(job_id=args.job_id)

    def _delete(self, args):
        self.target.delete_job(job_id=args.job_id)
