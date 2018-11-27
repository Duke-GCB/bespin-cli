from cwltool.context import LoadingContext
from cwltool.workflow import default_make_tool
from cwltool.resolver import tool_resolver
from cwltool.load_tool import load_tool
import logging


class CWLWorkflowVersion(object):
    def __init__(self, workflow, version_num, description, url):
        self.workflow = workflow
        self.version_num = version_num
        self.description = description
        self.url = url

    def create(self, api):
        fields = self.get_fields_from_url()
        return api.workflow_versions_post(
            workflow=self.workflow,
            version_num=self.version_num,
            description=self.description,
            url=self.url,
            fields=fields
        )

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
