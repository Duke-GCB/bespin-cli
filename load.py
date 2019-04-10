#!/usr/bin/env python

from bespin.api import BespinClientErrorException
from bespin.commands import Commands


def make_zipped_version_dict(repo, version_string_no_v, tag):
    return {
        'version': 'v{}'.format(version_string_no_v),
        'url': 'https://github.com/bespin-workflows/{}/archive/v{}.zip'.format(repo, version_string_no_v),
        'type': 'zipped',
        'path': '{}-{}/{}.cwl'.format(repo, version_string_no_v, tag),
        'info_url': 'https://github.com/bespin-workflows/{}/blob/v{}/CHANGELOG.md'.format(repo, version_string_no_v)
    }


workflows = [
    {'name': 'Whole Exome Sequence preprocessing using GATK4',
     'tag': 'exomeseq-gatk4-preprocessing',
     'versions':
         [
             make_zipped_version_dict('exomeseq-gatk4', '1.0.0', 'exomeseq-gatk4-preprocessing'),
             make_zipped_version_dict('exomeseq-gatk4', '2.0.0', 'exomeseq-gatk4-preprocessing'),
         ],
     },
    {'name': 'Whole Exome Sequence analysis using GATK4',
     'tag': 'exomeseq-gatk4',
     'versions':
         [
             make_zipped_version_dict('exomeseq-gatk4', '2.0.0', 'exomeseq-gatk4'),
         ],
     },

]


def create_workflow(name, tag):
    c = Commands('bespin-cli-dev', 'bespin-cli-loader')
    try:
        c.workflow_create(name, tag)
    except BespinClientErrorException:
        # may already exist
        pass


def create_workflow_version(url, workflow_type, path, version_info_url):
    c = Commands('bespin-cli-dev', 'bespin-cli-loader')
    c.workflow_version_create(url, workflow_type, path, version_info_url)


for workflow in workflows:
    create_workflow(workflow['name'], workflow['tag'])
    for version in workflow['versions']:
        create_workflow_version(version['url'], version['type'], version['path'], version['info_url'])
