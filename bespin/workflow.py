from cwltool.context import LoadingContext
from cwltool.workflow import default_make_tool
from cwltool.resolver import tool_resolver
from cwltool.load_tool import load_tool

from bespin.exceptions import WorkflowNotFound, InvalidWorkflowFileException
import logging

import tempfile
import shutil
from urllib.request import urlretrieve
import zipfile
import os
import re

log = logging.getLogger(__name__)


class CWLWorkflowLoader(object):

    TYPE_PACKED = 'packed'
    TYPE_ZIPPED = 'zipped'

    def __init__(self, workflow_version):
        """
        Create a workflow loader
        :param workflow_version: CWLWorkflowVersion containing the workflow_type and workflow_path
        :param download_dir: Optional path to a download directory. If None, a temp directory is used
        """
        self.download_dir = tempfile.mkdtemp()
        self.workflow_version = workflow_version
        self.download_path = os.path.join(self.download_dir, os.path.basename(workflow_version.url))

    def load(self):
        self._download_workflow()
        self._handle_download()
        loaded = self._load_downloaded_workflow()
        self._cleanup()
        return loaded

    def _download_workflow(self):
        urlretrieve(self.workflow_version.url, self.download_path)

    def _handle_download(self):
        if self.workflow_version.workflow_type == self.TYPE_ZIPPED:
            with zipfile.ZipFile(self.download_path) as z:
                z.extractall(self.download_dir)

    def _load_downloaded_workflow(self):
        # Turn down cwltool and rdflib logging
        logging.getLogger("cwltool").setLevel(logging.ERROR)
        logging.getLogger("rdflib.term").setLevel(logging.ERROR)
        context = LoadingContext({"construct_tool_object": default_make_tool,
                                  "resolver": tool_resolver,
                                  "disable_js_validation": True})
        context.strict = False
        tool_path = self._get_tool_path()
        return load_tool(tool_path, context)

    def _get_tool_path(self):
        if self.workflow_version.workflow_type == self.TYPE_PACKED:
            tool_path = self.download_path + '#main'
        elif self.workflow_version.workflow_type == self.TYPE_ZIPPED:
            tool_path = os.path.join(self.download_dir, self.workflow_version.workflow_path)
        else:
            raise InvalidWorkflowFileException('Workflow type {} is not supported'.format(self.workflow_version.workflow_type))
        return tool_path

    def _cleanup(self):
        """
        Remove temporary download items
        :return:
        """
        shutil.rmtree(self.download_dir)


class BespinWorkflowValidator(object):

    def __init__(self, workflow):
        self.workflow = workflow
        self.messages = []
        self.errors = []

    def add_message(self, message):
        self.messages.append(message)

    def add_error(self, error):
        self.errors.append(error)

    def check_field_exists(self, name):
        if name in self.workflow.tool:
            self.add_message('Field \'{}\' exists'.format(name))
        else:
            self.add_error('Field \'{}\' was not found in your CWL file'.format(name))

    def check_field_value(self, name, value):
        self.check_field_exists(name)
        if self.workflow.tool.get(name) == value:
            self.add_message('Field \'{}\' has required value \'{}\''.format(name, value))
        else:
            self.add_error('Field \'{}\' must have a value of \'{}\''.format(name, value))

    def check_field_pattern(self, name, pattern):
        self.check_field_exists(name)
        field_value = self.workflow.tool.get(name)
        matched = re.search(pattern, field_value)
        if matched:
            self.add_message('Field \'{}\' has required pattern \'{}\''.format(name, pattern))
        else:
            self.add_error('Field \'{}\' must have a pattern \'{}\''.format(name, pattern))

    def validate(self, expected_version):
        # Verify it's a workflow
        self.check_field_value('class', 'Workflow')
        # Verify cwl version
        self.check_field_value('cwlVersion', 'v1.0')
        # for the label field, pattern must be <tag>/<version>
        # TODO: Ensure the tag is here too
        label_pattern = '\S.*/{}$'.format(expected_version)  # No spaces and ends with /version
        self.check_field_pattern('label', label_pattern)
        # For the doc field, just verify the version string exists somewhere
        doc_pattern = expected_version
        self.check_field_pattern('doc', doc_pattern)

    def report(self, raise_on_errors):
        for m in self.messages:
            log.info(m)
        for e in self.errors:
            log.error(e)
        if self.errors and raise_on_errors:
            raise InvalidWorkflowFileException('\n'.join(self.errors))


class CWLWorkflowParser(object):

    def __init__(self, loaded_workflow):
        """
        Create a workflow parser. Expects label field to contain tag and version
        :param loaded_workflow: The loaded workflow dict-like object
        """
        self.loaded_workflow = loaded_workflow
        self.version = None
        self.tag = None
        self.description = None
        self.input_fields = None
        self.extract_metadata()
        self.extract_input_fields()

    def extract_metadata(self):
        self.extract_version_and_tag()
        self.extract_description()

    def extract_input_fields(self):
        # TODO: may need to upconvert these to list of dicts if not a packed workflow.
        self.input_fields = self.loaded_workflow.tool.get('inputs')

    def extract_version_and_tag(self):
        label = self.loaded_workflow.tool.get('label', '')
        fields = label.split('/')
        if len(fields) == 2:
            self.tag, self.version = fields

    def extract_description(self):
        doc = self.loaded_workflow.tool.get('doc', '')
        self.description = doc


class CWLWorkflowVersion(object):
    def __init__(self, url, workflow_type, workflow_path, version_info_url):
        self.url = url
        self.workflow_type = workflow_type
        self.workflow_path = workflow_path
        self.version_info_url = version_info_url

    def load_and_parse_workflow(self):
        loaded = CWLWorkflowLoader(self).load()
        parser = CWLWorkflowParser(loaded)
        validator = BespinWorkflowValidator(loaded)
        validator.validate(parser.version)
        validator.report(raise_on_errors=True)
        return parser

    def create(self, api):
        parser = self.load_and_parse_workflow()
        workflow_id = self.get_workflow_id(api, parser.tag)
        return api.workflow_versions_post(
            workflow=workflow_id,
            version=parser.version,
            workflow_type=self.workflow_type,
            description=parser.description,
            workflow_path=self.workflow_path,
            url=self.url,
            version_info_url=self.version_info_url,
            fields=parser.input_fields
        )

    def get_workflow_id(self, api, workflow_tag):
        return api.workflow_get_for_tag(workflow_tag)['id']
