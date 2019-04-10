#!/usr/bin/env python

from bespin.api import BespinClientErrorException
from bespin.commands import Commands


def make_zipped_version_dicts(repo, tag, versions):
    return [make_zipped_version_dict(repo, tag, version) for version in versions]


def make_zipped_version_dict(repo, tag, version):
    return {
        'version': version,
        'url': 'https://github.com/bespin-workflows/{}/archive/{}.zip'.format(repo, version),
        'type': 'zipped',
        'path': '{}-{}/{}.cwl'.format(repo, version.lstrip('v'), tag),
        'info_url': 'https://github.com/bespin-workflows/{}/blob/{}/CHANGELOG.md'.format(repo, version)
    }


def make_packed_version_dict(filename, version):
    return {
        'version': '{}'.format(version),
        'url': 'https://github.com/Duke-GCB/bespin-cwl/releases/download/{}/{}.cwl'.format(version, filename),
        'type': 'packed',
        'path': '#main',
        'info_url': 'https://github.com/Duke-GCB/bespin-cwl'
    }


workflows = [
    {'name': 'Whole Exome Sequence preprocessing using GATK4',
     'tag': 'exomeseq-gatk4-preprocessing',
     'versions': make_zipped_version_dicts('exomeseq-gatk4','exomeseq-gatk4-preprocessing',
                                           ['v1.0.0','v2.0.0',])
     },
    {'name': 'Whole Exome Sequence analysis using GATK4',
     'tag': 'exomeseq-gatk4',
     'versions': make_zipped_version_dicts('exomeseq-gatk4', 'exomeseq-gatk4',
                                           ['v2.0.0',])
     },
    {'name': 'Whole Exome Sequence preprocessing using GATK3',
     'tag': 'exomeseq-gatk3-preprocessing',
     'versions': make_zipped_version_dicts('exomeseq-gatk3','exomeseq-gatk3-preprocessing',
                                           ['v4.1.0','v4.1.1','v4.2.0',])
     },
    {'name': 'Whole Exome Sequence preprocessing using GATK3',
     'tag': 'exomeseq-gatk3',
     'versions': make_zipped_version_dicts('exomeseq-gatk3','exomeseq-gatk3',
                                           ['v1.0.0', 'v2.0.0', 'v3.0.0', 'v3.0.1', 'v3.0.2', 'v4.0.0', 'v4.1.0', 'v4.1.1',])
     },
    {'name': 'Legacy Exome Sequence analysis',
     'tag': 'exomeseq',
     'versions': [ make_packed_version_dict('exomeseq', 'v0.9.2.3'), ]
     }
]


def create_workflow(name, tag):
    c = Commands('bespin-cli-dev', 'bespin-cli-loader')
    try:
        c.workflow_create(name, tag)
    except BespinClientErrorException:
        # may already exist
        pass


def create_workflow_version(url, workflow_type, path, version_info_url, version):
    c = Commands('bespin-cli-dev', 'bespin-cli-loader')
    if workflow_type == 'zipped':
        # for zipped workflows, let parser get version from label field
        c.workflow_version_create(url, workflow_type, path, version_info_url)
    else:
        c.workflow_version_create(url, workflow_type, path, version_info_url, version)



for workflow in workflows[-1:]:
    create_workflow(workflow['name'], workflow['tag'])
    for version in workflow['versions']:
        create_workflow_version(version['url'], version['type'], version['path'], version['info_url'], version['version'])
