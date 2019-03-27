import sys
import logging
from cwltool.context import LoadingContext
from cwltool.workflow import default_make_tool
from cwltool.load_tool import load_tool
from cwltool.resolver import tool_resolver
import re

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


def disable_cwl_logs():
  logging.getLogger("cwltool").setLevel(logging.ERROR)
  logging.getLogger("rdflib.term").setLevel(logging.ERROR)

def load_cwl(filename_or_url):
  log.info('Loading {}'.format(filename_or_url))
  disable_cwl_logs()
  context = LoadingContext({"construct_tool_object": default_make_tool,
                            "resolver": tool_resolver,
                            "disable_js_validation": True})
  return load_tool(filename_or_url, context)


def check_field_exists(cwl, name):
  if name in cwl.tool:
    log.info('Field \'{}\' exists'.format(name))
  else:
    log.error('Field \'{}\' was not found in your CWL file'.format(name))

def check_field_value(cwl, name, value):
  check_field_exists(cwl, name)
  if cwl.tool.get(name) == value:
    log.info('Field \'{}\' has required value \'{}\''.format(name, value))
  else:
    log.error('Field \'{}\' must have a value of \'{}\''.format(name, value))

def check_field_pattern(cwl, name, pattern):
  check_field_exists(cwl, name)
  field_value = cwl.tool.get(name)
  matched = re.search(pattern, field_value)
  if matched:
    log.info('Field \'{}\' has required pattern \'{}\''.format(name, pattern))
  else:
    log.error('Field \'{}\' must have a pattern \'{}\''.format(name, pattern))

def validate_workflow(expected_version, filename):
  cwl = load_cwl(filename)
  # Verify it's a workflow
  check_field_value(cwl, 'class', 'Workflow')
  # Verify cwl version
  check_field_value(cwl, 'cwlVersion', 'v1.0')
  # for the label field, pattern must be
  label_pattern = '\S.*/{}$'.format(expected_version) # No spaces and ends with /version
  check_field_pattern(cwl, 'label', label_pattern)
  # For the doc field, just verify the version string exists somewhere
  doc_pattern = expected_version
  check_field_pattern(cwl, 'doc', doc_pattern)

if __name__ == '__main__':
  expected_version, filename = sys.argv[1:3]
  validate_workflow(expected_version, filename)
