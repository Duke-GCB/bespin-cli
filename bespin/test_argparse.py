from __future__ import absolute_import
from unittest import TestCase
from bespin.argparser import ArgParser
from mock import patch, Mock
import sys


class ArgParserTestCase(TestCase):
    def setUp(self):
        self.target_object = Mock()
        self.arg_parser = ArgParser(version_str='1.0', target_object=self.target_object)

    def test_workflows_list_current_versions(self):
        self.arg_parser.parse_and_run_commands(["workflows", "list"])
        self.target_object.workflows_list.assert_called_with(all_versions=False)

    def test_workflows_list_all_versions(self):
        self.arg_parser.parse_and_run_commands(["workflows", "list", "--all"])
        self.target_object.workflows_list.assert_called_with(all_versions=True)

    def test_workflows_list_all_versions_short_flag(self):
        self.arg_parser.parse_and_run_commands(["workflows", "list", "-a"])
        self.target_object.workflows_list.assert_called_with(all_versions=True)

    def test_workflow_configurations_list(self):
        self.arg_parser.parse_and_run_commands(["workflowconfigurations", "list"])
        self.target_object.workflow_configurations_list.assert_called_with()

    def test_workflow_configurations_show(self):
        self.arg_parser.parse_and_run_commands(["workflowconfigurations", "show", "--tag", "exome/v1/human"])
        self.target_object.workflow_configurations_show.assert_called_with("exome/v1/human", sys.stdout)

    def test_init_job(self):
        self.arg_parser.parse_and_run_commands(["jobs", "init", "--tag", "exome/v1/human"])
        self.target_object.init_job.assert_called_with("exome/v1/human", sys.stdout)

    def test_create_job(self):
        self.arg_parser.parse_and_run_commands(["jobs", "create", "setup.py"])
        self.target_object.create_job.assert_called()

    def test_start_job(self):
        self.arg_parser.parse_and_run_commands(["jobs", "start", "123"])
        self.target_object.start_job.assert_called_with(123, None)

    def test_start_job_with_optional_token(self):
        self.arg_parser.parse_and_run_commands(["jobs", "start", "123", "--token", "secret"])
        self.target_object.start_job.assert_called_with(123, "secret")

    def test_cancel_job(self):
        self.arg_parser.parse_and_run_commands(["jobs", "cancel", "123"])
        self.target_object.cancel_job.assert_called_with(123)

    def test_restart_job(self):
        self.arg_parser.parse_and_run_commands(["jobs", "restart", "123"])
        self.target_object.restart_job.assert_called_with(123)

    def test_delete_job(self):
        self.arg_parser.parse_and_run_commands(["jobs", "delete", "123"])
        self.target_object.delete_job.assert_called_with(123)
