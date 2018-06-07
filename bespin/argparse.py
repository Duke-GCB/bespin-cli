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
        return argument_parser

    def _create_workflows_parser(self, subparsers):
        jobs_parser = subparsers.add_parser('workflows', description='workflows commands')
        jobs_subparser = jobs_parser.add_subparsers()

        list_jobs_parser = jobs_subparser.add_parser('list', description='list workflows')
        list_jobs_parser.set_defaults(func=self._run_list_workflows)

    def _create_job_parser(self, subparsers):
        jobs_parser = subparsers.add_parser('jobs')
        jobs_subparser = jobs_parser.add_subparsers()

        list_jobs_parser = jobs_subparser.add_parser('list', description='list jobs')
        list_jobs_parser.set_defaults(func=self._run_list_jobs)

        init_jobs_parser = jobs_subparser.add_parser('init', description='init job file')
        init_jobs_parser.set_defaults(func=self._run_init_job)
        init_jobs_parser.add_argument('--slug', type=str, dest='slug', required=True)
        init_jobs_parser.add_argument('--outfile', type=argparse.FileType('w'), dest='outfile', default=sys.stdout)

        submit_jobs_parser = jobs_subparser.add_parser('create',
                                                       description="create job using 'infile' from init command")
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

    def _run_list_jobs(self, _):
        self.target_object.jobs_list()

    def _run_list_workflows(self, _):
        self.target_object.workflows_list()

    def _run_list_workflow_versions(self, _):
        self.target_object.list_workflow_versions()

    def _run_list_questionnaires(self, _):
        self.target_object.list_questionnaires()

    def _run_create_job_file(self, args):
        self.target_object.create_job_file(args.questionnaire_id, args.outfile)

    def _run_init_job(self, args):
        self.target_object.init_job(args.slug, args.outfile)

    def _run_create_job(self, args):
        self.target_object.create_job(args.infile)

    def _run_start_job(self, args):
        self.target_object.start_job(args.job_id, args.token)

    def _run_cancel_job(self, args):
        self.target_object.cancel_job(args.job_id)

    def _run_restart_job(self, args):
        self.target_object.restart_job(args.job_id)

    def _run_delete_job(self, args):
        self.target_object.delete_job(args.job_id)

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
