import logging
import os
import re
import shutil
import tempfile
import zipfile
from urllib.request import urlretrieve

from cwltool.context import LoadingContext
from cwltool.load_tool import load_tool
from cwltool.resolver import tool_resolver
from cwltool.workflow import default_make_tool

from bespin.exceptions import InvalidWorkflowFileException

log = logging.getLogger(__name__)


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


class BespinWorkflowLoader(object):
    """
    Downloads, extracts, and loads workflows from a URL - packed or zipped.
    """

    TYPE_PACKED = 'packed'
    TYPE_ZIPPED = 'zipped'
    TYPE_DIRECT = 'direct'

    def __init__(self, workflow_version):
        """
        Create a workflow loader
        :param workflow_version: CWLWorkflowVersion containing the workflow_type and workflow_path
        :param download_dir: Optional path to a download directory. If None, a temp directory is used
        """
        self.workflow_version = workflow_version
        if not self.workflow_version.workflow_type == self.TYPE_DIRECT:
            self.download_dir = os.path.realpath(tempfile.mkdtemp())
            self.download_path = os.path.join(self.download_dir, os.path.basename(workflow_version.url))

    def load(self):
        """
        Load the workflow by downloading to a temporary directory, reading into memory, and deleting
        the temporary directory.
        :return: loaded CWL workflow
        """
        self._download_workflow()
        self._handle_download()
        loaded = self._load_downloaded_workflow()
        self._cleanup()
        return loaded

    def _download_workflow(self):
        if not self.workflow_version.workflow_type == self.TYPE_DIRECT:
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
        """
        Determine what path to provide for the loader.
        For packed workflows, we use the CWL file with #main. For zipped workflows, we must rely on workflow_path
        to know which CWL file to load.
        :return: tool path suitable for cwltool.load_tool.load_tool
        """
        if self.workflow_version.workflow_type == self.TYPE_PACKED:
            tool_path = self.download_path + '#main'
        elif self.workflow_version.workflow_type == self.TYPE_ZIPPED:
            tool_path = os.path.join(self.download_dir, self.workflow_version.workflow_path)
        elif self.workflow_version.workflow_type == self.TYPE_DIRECT:
            tool_path = self.workflow_version.url
        else:
            raise InvalidWorkflowFileException(
                'Workflow type {} is not supported'.format(self.workflow_version.workflow_type))
        return tool_path

    def _cleanup(self):
        """
        Remove temporary download items
        """
        if not self.workflow_version.workflow_type == self.TYPE_DIRECT:
            shutil.rmtree(self.download_dir)

    def get_prefix(self):
        """
        Determine the workflow's URI prefix from the loaded workflow_version.
        This prefix is useful for formatting the 'id' field of CWL objects included by the workflow,
        and by convention is related to the directory or URI containing the workflow document
        Note that we always use os.path.realpath here because cwltool will canonicalize paths too.
        :return: str: URI prefix of the workflow that can be stripped off parsed tools
        """
        if self.workflow_version.workflow_type == self.TYPE_DIRECT:
            # Direct workflows may be 'file:///path/to/workflow.cwl' or /path/to/workflow.cwl
            file_path = remove_prefix(self.workflow_version.url, 'file://')
            workflow_dir = os.path.dirname(file_path)
            prefix = 'file://{}/'.format(os.path.realpath(workflow_dir))
        elif self.workflow_version.workflow_type == self.TYPE_ZIPPED:
            # For zipped workflows we need to determine the absoute path to the unzipped file and get its directory
            workflow_dir = os.path.dirname(os.path.join(self.download_dir, self.workflow_version.workflow_path))
            prefix = 'file://{}/'.format(os.path.realpath(workflow_dir))
        elif self.workflow_version.workflow_type == self.TYPE_PACKED:
            # The prefix from a packed workflow uses the full path to the packed CWL file, plus a '#'
            prefix = 'file://{}#'.format(os.path.realpath(self.download_path))
        else:
            raise InvalidWorkflowFileException(
                'Workflow type {} is not supported'.format(self.workflow_version.workflow_type))
        return prefix


class BespinWorkflowValidator(object):
    """
    Validates parsed workflows according to bespin standards
    """

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
            return True
        else:
            self.add_error('Field \'{}\' was not found in your CWL file'.format(name))
        return False

    def check_field_value(self, name, value):
        if self.check_field_exists(name):
            if self.workflow.tool.get(name) == value:
                self.add_message('Field \'{}\' has required value \'{}\''.format(name, value))
                return True
            else:
                self.add_error('Field \'{}\' must have a value of \'{}\''.format(name, value))
        return False

    def check_field_pattern(self, name, pattern):
        if self.check_field_exists(name):
            field_value = self.workflow.tool.get(name)
            matched = re.search(pattern, field_value)
            if matched:
                self.add_message('Field \'{}\' has required pattern \'{}\''.format(name, pattern))
                return True
            else:
                self.add_error('Field \'{}\' must have a pattern \'{}\''.format(name, pattern))
        return False

    def validate(self, expected_tag, expected_version):
        # Verify it's a workflow
        self.check_field_value('class', 'Workflow')
        # Verify cwl version
        self.check_field_value('cwlVersion', 'v1.0')
        # for the label field, pattern shall be <tag>/<version>
        self.check_field_value('label', '{}/{}'.format(expected_tag, expected_version))
        # For the doc field, just verify the version string exists somewhere
        self.check_field_pattern('doc', expected_version)

    def report(self, raise_on_errors):
        for m in self.messages:
            log.info(m)
        for e in self.errors:
            log.error(e)
        if self.errors and raise_on_errors:
            raise InvalidWorkflowFileException('\n'.join(self.errors))


class BespinWorkflowParser(object):

    def __init__(self, loaded_workflow):
        """
        Create a workflow parser. Expects label field to contain tag and version
        :param loaded_workflow: The loaded cwl workflow
        """
        self.loaded_workflow = loaded_workflow
        self.version = None
        self.tag = None
        self.description = None
        self.input_fields = None
        self._extract_metadata()
        self._extract_input_fields()

    def _extract_metadata(self):
        self._extract_version_and_tag()
        self._extract_description()

    def _extract_input_fields(self):
        # Using inputs_record_schema['fields'] here as that has type dictionaries
        # (e.g {'name': 'input_file', 'type': 'File'}) and no fragments/references based on local
        # file paths.
        self.input_fields = self.loaded_workflow.inputs_record_schema.get('fields')

    def _extract_version_and_tag(self):
        """
        Attempt to extract version and tag from the label field
        :return: None
        """
        label = self.loaded_workflow.tool.get('label', '')
        fields = label.split('/')
        if len(fields) == 2:
            self.tag, self.version = fields

    def _extract_description(self):
        """
        Attempt to extract workflow description from the doc field
        :return:
        """
        doc = self.loaded_workflow.tool.get('doc', '')
        self.description = doc

    def check_required_fields(self):
        """
        Method to check that fields (version, tag, description) are not empty after parsing
        """
        if self.tag is None or self.version is None:
            raise InvalidWorkflowFileException('Unable to extract workflow tag and version. '
                                               'Please make sure workflow has a label field in the '
                                               'format \'tag/version\' (e.g. label: exomeseq-gatk4/v1.0.0)')
        if not self.description:
            raise InvalidWorkflowFileException('Unable to extract workflow description. Please make sure workflow '
                                               'has a long description in the doc field '
                                               '(e.g. doc: Whole Exome Sequence analysis using GATK 4 - v1.0.0')


class CWLWorkflowVersion(object):

    def __init__(self, url, workflow_type, workflow_path, version_info_url=None,
                 override_version=None, override_tag=None, validate=True):
        self.url = url
        self.workflow_type = workflow_type
        self.workflow_path = workflow_path
        self.version_info_url = version_info_url
        self.override_version = override_version
        self.override_tag = override_tag
        self.validate = validate

    def _load_and_parse_workflow(self, expected_tag=None, expected_version=None):
        """
        Fetch, load, parse, and (optionally) validate the workflow from the URL provided
        :param expected_tag: Optional - if provided, make sure the workflow fetched has the expected tag metadata
        :param expected_version: Optional - if provided, make sure the workflow fetched has the expected version metadata
        :return: a BespinWorkflowParser with the loaded workflow
        """
        loaded = BespinWorkflowLoader(self).load()
        parser = BespinWorkflowParser(loaded)
        if self.validate:
            validator = BespinWorkflowValidator(loaded)
            if expected_tag is None: expected_tag = parser.tag
            if expected_version is None: expected_version = parser.version
            validator.validate(expected_tag, expected_version)
            validator.report(raise_on_errors=True)
        if self.override_version:
            if parser.version is not None:
                log.warning('Overriding parsed version {} to {}'.format(parser.version, self.override_version))
            parser.version = self.override_version
        if self.override_tag:
            if parser.tag is not None:
                log.warning('Overriding parsed tag {} to {}'.format(parser.tag, self.override_tag))
            parser.tag = self.override_tag
        return parser

    def validate_workflow(self, expected_tag=None, expected_version=None):
        """
        Validate this workflow for required bespin standard fields
        :param expected_tag: Optional - if provided, make sure the workflow fetched has the expected tag metadata
        :param expected_version: Optional - if provided, make sure the workflow fetched has the expected version metadata
        :return: a BespinWorkflowParser with the loaded workflow
        """
        parser = self._load_and_parse_workflow(expected_tag, expected_version)
        parser.check_required_fields()
        return parser

    def create(self, api):
        """
        Validate and create the workflow version through bespin-api
        :param api: bespin.api.BespinApi
        :return: response JSON dictionary
        """
        parser = self.validate_workflow()
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
        """
        Get the ID of the workflow object by its tag using Bespin API
        :param api: bespin.api.BespinApi
        :param workflow_tag: A workflow tag string to look up
        :return: The id of the workflow
        """
        return api.workflow_get_for_tag(workflow_tag)['id']
