from __future__ import print_function
import argparse
import sys

DESCRIPTION_STR = "bespin ({}) Run bioinformatics workflows"


class ArgParser(object):
    def __init__(self, version_str, target_object):
        """
        Create argument parser with the specified version string that will call the appropriate methods
        in target_object when those commands are selected.
        :param version_str: str: version of datadelivery
        :param target_object: object: object with methods named the same as the commands
        """
        self.version_str = version_str
        self.target_object = target_object
        self.argument_parser = self._create_argument_parser()

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

    def _create_argument_parser(self):
        argument_parser = argparse.ArgumentParser(description=DESCRIPTION_STR.format(self.version_str))
        subparsers = argument_parser.add_subparsers()
        self._create_workflows_parser(subparsers)
        self._create_job_parser(subparsers)
        self._create_share_groups_parser(subparsers)
        self._create_vm_strategies_parser(subparsers)
        return argument_parser

    def _create_workflows_parser(self, subparsers):
        workflows_parser = subparsers.add_parser('workflows', description='workflows commands')
        workflows_subparser = workflows_parser.add_subparsers()

        list_parser = workflows_subparser.add_parser('list', description='list workflows')
        list_parser.add_argument('-a', '--all', action='store_true',
                                 help='show all workflow versions instead of just the most recent.')
        list_parser.set_defaults(func=self._run_list_workflows)

        joborder_parser = workflows_subparser.add_parser('joborder', description='show workflow job order')
        joborder_parser.add_argument('--tag', type=str, dest='tag', required=True)
        joborder_parser.add_argument('--outfile', type=argparse.FileType('w'), dest='outfile', default=sys.stdout)
        joborder_parser.set_defaults(func=self._run_show_workflow_job_order)

    def _create_job_parser(self, subparsers):
        jobs_parser = subparsers.add_parser('jobs')
        jobs_subparser = jobs_parser.add_subparsers()

        list_jobs_parser = jobs_subparser.add_parser('list', description='list jobs')
        list_jobs_parser.set_defaults(func=self._run_list_jobs)

        init_jobs_parser = jobs_subparser.add_parser('init', description='init job file')
        init_jobs_parser.set_defaults(func=self._run_init_job)
        init_jobs_parser.add_argument(type=str, dest='tag')
        init_jobs_parser.add_argument('--outfile', type=argparse.FileType('w'), dest='outfile', default=sys.stdout)

        submit_jobs_parser = jobs_subparser.add_parser('create',
                                                       description="create job using 'infile' from init command")
        submit_jobs_parser.add_argument('--share-group', type=str, required=True,
                                        help="id of the share group use for this job")
        submit_jobs_parser.add_argument('--vm-strategy', type=str,
                                        help="id of the vm strategy use for this job")
        submit_jobs_parser.add_argument('--dry-run', action='store_true',
                                 help='Do not create a job, instead check the inputs for validity.')
        submit_jobs_parser.set_defaults(func=self._run_create_job)
        submit_jobs_parser.add_argument('infile', type=argparse.FileType('r'), help='file created by init command')

        start_jobs_parser = jobs_subparser.add_parser('start', description='start job')
        start_jobs_parser.set_defaults(func=self._run_start_job)
        start_jobs_parser.add_argument('job_id', type=int)
        start_jobs_parser.add_argument('--token', type=str)

        cancel_jobs_parser = jobs_subparser.add_parser('cancel', description='cancel job')
        cancel_jobs_parser.set_defaults(func=self._run_cancel_job)
        cancel_jobs_parser.add_argument('job_id', type=int)

        restart_jobs_parser = jobs_subparser.add_parser('restart', description='restart job')
        restart_jobs_parser.set_defaults(func=self._run_restart_job)
        restart_jobs_parser.add_argument('job_id', type=int)

        delete_jobs_parser = jobs_subparser.add_parser('delete', description='delete job')
        delete_jobs_parser.set_defaults(func=self._run_delete_job)
        delete_jobs_parser.add_argument('job_id', type=int)

    def _create_share_groups_parser(self, subparsers):
        share_groups_parser = subparsers.add_parser('sharegroups', description='sharegroups commands')
        share_groups_subparser = share_groups_parser.add_subparsers()

        list_parser = share_groups_subparser.add_parser('list', description='list share groups')
        list_parser.set_defaults(func=self._run_list_share_groups)

    def _create_vm_strategies_parser(self, subparsers):
        share_groups_parser = subparsers.add_parser('vmstrategies', description='VM Stratgies commands')
        share_groups_subparser = share_groups_parser.add_subparsers()

        list_parser = share_groups_subparser.add_parser('list', description='list vm strategies')
        list_parser.set_defaults(func=self._run_list_vm_strategies)

    def _run_list_jobs(self, _):
        self.target_object.jobs_list()

    def _run_list_workflows(self, args):
        self.target_object.workflows_list(all_versions=args.all)

    def _run_show_workflow_job_order(self, args):
        self.target_object.workflow_configuration_job_order_show(args.tag, args.outfile)

    def _run_init_job(self, args):
        self.target_object.init_job(args.tag, args.outfile)

    def _run_create_job(self, args):
        self.target_object.create_job(args.infile, args.dry_run, args.share_group, args.vm_strategy)

    def _run_start_job(self, args):
        self.target_object.start_job(args.job_id, args.token)

    def _run_cancel_job(self, args):
        self.target_object.cancel_job(args.job_id)

    def _run_restart_job(self, args):
        self.target_object.restart_job(args.job_id)

    def _run_delete_job(self, args):
        self.target_object.delete_job(args.job_id)

    def _run_list_share_groups(self, args):
        self.target_object.list_share_groups()

    def _run_list_vm_strategies(self, args):
        self.target_object.list_vm_strategies()

    @staticmethod
    def read_argument_file_contents(infile):
        """
        return the contents of a file or "" if infile is None.
        If the infile is STDIN displays a message to tell user how to quit entering data.
        :param infile: file handle to read from
        :return: str: contents of the file
        """
        if infile:
            if infile == sys.stdin:
                print("Enter message and press CTRL-d when done:")
            return infile.read()
        return ""
