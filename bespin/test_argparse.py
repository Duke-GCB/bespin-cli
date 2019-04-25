from __future__ import absolute_import
from unittest import TestCase
from bespin.argparser import ArgParser
from mock import patch, Mock, ANY, mock_open
import sys


class ArgParserTestCase(TestCase):
    def setUp(self):
        self.target_object = Mock()
        self.arg_parser = ArgParser(version_str='1.0', target_object=self.target_object)

    def test_workflows_list_current_versions(self):
        self.arg_parser.parse_and_run_commands(["workflow", "list"])
        self.target_object.workflows_list.assert_called_with(all_versions=False, short_format=False, tag=None)

    def test_workflow_list_all_versions(self):
        self.arg_parser.parse_and_run_commands(["workflow", "list", "--all"])
        self.target_object.workflows_list.assert_called_with(all_versions=True, short_format=False, tag=None)

    def test_workflow_list_short(self):
        self.arg_parser.parse_and_run_commands(["workflow", "list", "--short"])
        self.target_object.workflows_list.assert_called_with(all_versions=False, short_format=True, tag=None)

    def test_workflows_create(self):
        self.arg_parser.parse_and_run_commands(["workflow", "create", "--name", "MyWF", "--tag", "sometag"])
        self.target_object.workflows_list.workflow_create(name="MyWF", tag="sometag")

    def test_workflow_versions_list(self):
        self.arg_parser.parse_and_run_commands(["workflow-version", "list"])
        self.target_object.workflow_versions_list.assert_called_with(workflow_tag=None)

    def test_workflow_versions_list_with_filter(self):
        self.arg_parser.parse_and_run_commands(["workflow-version", "list", "--workflow", "sometag"])
        self.target_object.workflow_versions_list.assert_called_with(workflow_tag="sometag")

    def test_workflow_versions_create_only_required(self):
        self.arg_parser.parse_and_run_commands(["workflow-version", "create",
                                                "--url", "someurl",
                                                "--type", "packed",
                                                "--path", "#main",
                                                "--version-info-url", "infourl"])
        self.target_object.workflow_version_create.assert_called_with(
            url="someurl",
            workflow_type="packed",
            workflow_path="#main",
            version_info_url="infourl",
            override_tag=None,
            override_version=None,
            validate=True
        )

    def test_workflow_versions_create_with_explicit_version_and_tag(self):
        self.arg_parser.parse_and_run_commands(['workflow-version', 'create',
                                                '--url', 'someurl',
                                                '--type', 'packed',
                                                '--path', '#main',
                                                '--version-info-url','infourl',
                                                '--version', 'v3.1.0',
                                                '--workflow-tag','newtag'])
        self.target_object.workflow_version_create.assert_called_with(
            url="someurl",
            workflow_type="packed",
            workflow_path="#main",
            version_info_url="infourl",
            override_tag='newtag',
            override_version='v3.1.0',
            validate=True
        )

    def test_workflow_versions_create_novalidate(self):
        self.arg_parser.parse_and_run_commands(["workflow-version", "create",
                                                "--url", "someurl",
                                                "--type", "packed",
                                                "--path", "#main",
                                                "--version-info-url", "infourl",
                                                "--no-validate"])
        self.target_object.workflow_version_create.assert_called_with(
            url="someurl",
            workflow_type="packed",
            workflow_path="#main",
            version_info_url="infourl",
            override_tag=None,
            override_version=None,
            validate=False
        )

    def test_workflow_versions_validate_only_required(self):
        self.arg_parser.parse_and_run_commands(['workflow-version', 'validate',
                                                '--url', 'someurl',
                                                '--type', 'packed',
                                                '--path', '#main'])
        self.target_object.workflow_version_validate.assert_called_with(
            url="someurl",
            workflow_type="packed",
            workflow_path="#main",
            expected_tag=None,
            expected_version=None
        )

    def test_workflow_versions_validate_with_explicit_version_and_tag(self):
        self.arg_parser.parse_and_run_commands(['workflow-version', 'validate',
                                                '--url', 'someurl',
                                                '--type', 'packed',
                                                '--path', '#main',
                                                '--workflow-tag', 'expected-tag',
                                                '--version','vE.X.P'])
        self.target_object.workflow_version_validate.assert_called_with(
            url="someurl",
            workflow_type="packed",
            workflow_path="#main",
            expected_tag='expected-tag',
            expected_version='vE.X.P'
        )

    def test_workflow_versions_validate_local_without_path(self):
        self.arg_parser.parse_and_run_commands(['workflow-version', 'validate',
                                                '--url', 'localurl',
                                                '--type', 'local'])
        self.target_object.workflow_version_validate.assert_called_with(
            url="localurl",
            workflow_type="local",
            workflow_path=None,
            expected_tag=None,
            expected_version=None
        )

    def test_workflow_config_list(self):
        self.arg_parser.parse_and_run_commands(["workflow-config", "list"])
        self.target_object.workflow_configs_list.assert_called_with(workflow_tag=None)

    def test_workflow_config_list_with_filter(self):
        self.arg_parser.parse_and_run_commands(["workflow-config", "list", "--workflow", "sometag"])
        self.target_object.workflow_configs_list.assert_called_with(workflow_tag="sometag")

    def test_workflow_config_config_show_job_order(self):
        self.arg_parser.parse_and_run_commands(["workflow-config", "show-job-order",
                                                "--workflow", "sometag",
                                                "--tag", "mytag"])
        self.target_object.workflow_config_show_job_order.assert_called_with(tag='mytag',
                                                                             workflow_tag='sometag',
                                                                             outfile=sys.stdout)

    def test_workflow_config_create(self):
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.arg_parser.parse_and_run_commands(["workflow-config", "create",
                                                    "--workflow", "sometag",
                                                    "--default-job-config", "default2",
                                                    "--share-group", "informatics",
                                                    "--tag", "newtag",
                                                    "job_order.json"])
        self.target_object.workflow_config_create.assert_called_with(
            workflow_tag='sometag',
            default_job_strategy_name='default2',
            share_group_name='informatics',
            tag='newtag',
            joborder_infile=ANY)

    def test_share_group_list(self):
        self.arg_parser.parse_and_run_commands(["share-group", "list"])
        self.target_object.share_groups_list.assert_called_with()

    def test_job_config_list(self):
        self.arg_parser.parse_and_run_commands(["job-config", "list"])
        self.target_object.job_configs_list.assert_called_with()

    def test_job_template_create(self):
        self.arg_parser.parse_and_run_commands(["job-template", "create", "sometag/v1/human"])
        self.target_object.job_template_create.assert_called_with(tag='sometag/v1/human', outfile=sys.stdout)

    def test_job_list(self):
        self.arg_parser.parse_and_run_commands(["job", "list"])
        self.target_object.jobs_list.assert_called_with()

    def test_job_create(self):
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.arg_parser.parse_and_run_commands(["job", "create", "job_template.yaml"])
        self.target_object.job_create.assert_called_with(job_template_infile=mock_file.return_value)

    def test_job_run(self):
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.arg_parser.parse_and_run_commands(["job", "run", "job_template.yaml"])
        self.target_object.job_run.assert_called_with(job_template_infile=mock_file.return_value, token=None)

    def test_job_run_with_token(self):
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.arg_parser.parse_and_run_commands(["job", "run", "job_template.yaml", "--token", "secret"])
        self.target_object.job_run.assert_called_with(job_template_infile=mock_file.return_value, token="secret")

    def test_job_validate(self):
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.arg_parser.parse_and_run_commands(["job", "validate", "job_template.yaml"])
        self.target_object.job_validate.assert_called_with(job_template_infile=mock_file.return_value)

    def test_start_job(self):
        self.arg_parser.parse_and_run_commands(["job", "start", "123"])
        self.target_object.start_job.assert_called_with(job_id=123, token=None)

    def test_start_job_with_optional_token(self):
        self.arg_parser.parse_and_run_commands(["job", "start", "123", "--token", "secret"])
        self.target_object.start_job.assert_called_with(job_id=123, token="secret")

    def test_cancel_job(self):
        self.arg_parser.parse_and_run_commands(["job", "cancel", "123"])
        self.target_object.cancel_job.assert_called_with(job_id=123)

    def test_restart_job(self):
        self.arg_parser.parse_and_run_commands(["job", "restart", "123"])
        self.target_object.restart_job.assert_called_with(job_id=123)

    def test_delete_job(self):
        self.arg_parser.parse_and_run_commands(["job", "delete", "123"])
        self.target_object.delete_job.assert_called_with(job_id=123)
