from cwltool.context import LoadingContext
from cwltool.workflow import default_make_tool
from cwltool.resolver import tool_resolver
from cwltool.load_tool import load_tool
from bespin.exceptions import WorkflowNotFound
import logging

AUTO_VERSION_VALUE = 'auto'


class CWLWorkflowVersion(object):
    def __init__(self, workflow_tag, url, description, version):
        self.workflow_tag = workflow_tag
        self.url = url
        self.description = description
        self.version = version

    def create(self, api):
        return api.workflow_versions_post(
            workflow=self.get_workflow_id(api),
            version_num=self.get_version_num(api),
            description=self.description,
            url=self.url,
            fields=self.get_fields_from_url()
        )

    def get_workflow_id(self, api):
        return api.workflow_get_for_tag(self.workflow_tag)['id']

    def get_version_num(self, api):
        if self.version == AUTO_VERSION_VALUE:
            items = api.workflow_versions_list(self.workflow_tag)
            if not items:
                return 1
            else:
                return items[-1]['version'] + 1
        return self.version

    def get_fields_from_url(self):
        # turn off default cwltool INFO logging
        cwl_logger = logging.getLogger("cwltool")
        cwl_logger.setLevel(logging.ERROR)
        context = LoadingContext({"construct_tool_object": default_make_tool,
                                  "resolver": tool_resolver,
                                  "disable_js_validation": True})
        context.strict = False
        parsed = load_tool(self.url + '#main', context)
        return parsed.inputs_record_schema.get('fields')
