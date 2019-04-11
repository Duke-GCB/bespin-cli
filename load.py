#!/usr/bin/env python

from bespin.api import BespinClientErrorException
from bespin.commands import Commands


def make_zipped_version_dicts(repo, tag, versions):
    return [make_zipped_version_dict(repo, tag, version) for version in versions]


def make_packed_version_dicts(filename, versions):
    return [make_packed_version_dict(filename, version) for version in versions]


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
    {'name': 'Packed/Legacy Whole Exome Sequence analysis using GATK3',
     'tag': 'packed-exomeseq-gatk3',
     'versions': make_packed_version_dicts('exomeseq', ['v0.9.0','v0.9.1','v0.9.2','v0.9.3','v0.9.4','v0.9.5','v0.9.2.1','v0.9.2.2','v0.9.2.3'])
     },
    {'name': 'Packed/Legacy Whole Exome Sequence preprocessing using GATK3',
     'tag': 'packed-exomeseq-gatk3-preprocessing',
     'versions': make_packed_version_dicts('exomeseq-preprocessing', ['v0.9.4', 'v0.9.5'])
     },
    {'name': 'Packed/Legacy Whole Exome Sequence analysis using GATK4',
     'tag': 'packed-exomeseq-gatk4',
     'versions': make_packed_version_dicts('exomeseq-gatk4', ['v0.9.5'])
     },
    {'name': 'Packed/Legacy Whole Exome Sequence preprocessing using GATK4',
     'tag': 'packed-exomeseq-gatk4-preprocessing',
     'versions': make_packed_version_dicts('exomeseq-gatk4-preprocessing', ['v0.9.4','v0.9.5'])
     }
]


def create_workflow(name, tag):
    c = Commands('bespin-cli-dev', 'bespin-cli-loader')
    try:
        c.workflow_create(name, tag)
    except BespinClientErrorException:
        # may already exist
        pass


def create_workflow_version(url, workflow_type, path, version_info_url, tag, version):
    c = Commands('bespin-cli-dev', 'bespin-cli-loader')
    if workflow_type == 'zipped':
        # for zipped workflows, let parser get version and tag from label field
        c.workflow_version_create(url, workflow_type, path, version_info_url, validate=True)
    else:
        c.workflow_version_create(url, workflow_type, path, version_info_url, override_version=version,
                                  override_tag=tag, validate=False)



for workflow in workflows:
    create_workflow(workflow['name'], workflow['tag'])
    for version in workflow['versions']:
        create_workflow_version(version['url'], version['type'], version['path'], version['info_url'], workflow['tag'], version['version'])
