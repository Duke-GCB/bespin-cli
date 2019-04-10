#!/usr/bin/env python

import tempfile
from urllib.request import urlretrieve
import zipfile
import os
from bespin.validate_workflow import main as validate_main
from bespin.commands import Commands
from bespin.api import BespinClientErrorException

# workflow name
# workflow version string
# workflow url
# workflow type
# workflow path


workflows = [
  ('exomeseq-gatk4-preprocessing', 'v1.0.0', 'https://github.com/bespin-workflows/exomeseq-gatk4/archive/v1.0.0.zip', 'zipped', 'exomeseq-gatk4-1.0.0/exomeseq-gatk4-preprocessing.cwl',),
  ('exomeseq-gatk4-preprocessing', 'v2.0.0', 'https://github.com/bespin-workflows/exomeseq-gatk4/archive/v2.0.0.zip', 'zipped', 'exomeseq-gatk4-2.0.0/exomeseq-gatk4-preprocessing.cwl',),
  ('exomeseq-gatk4', 'v2.0.0', 'https://github.com/bespin-workflows/exomeseq-gatk4/archive/v2.0.0.zip', 'zipped', 'exomeseq-gatk4-2.0.0/exomeseq-gatk4.cwl',),
]

def create_workflow(name, tag):
  c = Commands('bespin-cli-dev','bespin-cli-loader')
  try:
    c.workflow_create(name, tag)
  except BespinClientErrorException:
    # may already exist
    pass

def create_workflow_version(workflow_values):
  (name, version, url, workflow_type, path) = workflow_values
  c = Commands('bespin-cli-dev','bespin-cli-loader')
  c.workflow_version_create(url, workflow_type, path, 'https://version-info-url.com')

# when creating workflows only try the top-levels

for workflow in workflows:
  workflow_tag = workflow[0]
  create_workflow(workflow_tag, workflow_tag)
  create_workflow_version(workflow)

#   create_version(workfow)


