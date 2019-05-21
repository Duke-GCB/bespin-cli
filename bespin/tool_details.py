import os
from bespin.workflow import BespinWorkflowLoader, BespinWorkflowParser
class DockerToolDetail(object):

    def __init__(self, req_dict):
        self.docker_image_name = req_dict.get('dockerPull')

    def add_info(self, info_dict):
        docker_infos = [{'image_name': self.docker_image_name}]
        info_dict['docker'] = docker_infos


class SoftwareToolDetail(object):

    def __init__(self, req_dict):
        self.packages = req_dict.get('packages')

    def add_info(self, info_dict):
        software_info = []
        for package in self.packages:
            package_info = {}
            package_info['package'] = package.get('package',)
            package_info['versions'] = package.get('version', [])
            package_info['citation'] = package.get('https://schema.org/citation')
            software_info.append(package_info)
        info_dict['software'] = software_info


class ToolDetailsExtractor(object):

    def __init__(self, prefix):
        self.details = []
        self.prefix = prefix

    def accept(self, visitor):
        visitor.visit(self.extract_tool_details)

    def tool_exists(self, tool_name):
        return tool_name in [detail['tool_name'] for detail in self.details]

    @staticmethod
    def extract_requirements(requirements, tool_info):
        for req in requirements:
            if req.get('class') == 'DockerRequirement':
                tool_detail = DockerToolDetail(req)
                tool_detail.add_info(tool_info)
            elif req.get('class') == 'SoftwareRequirement':
                tool_detail = SoftwareToolDetail(req)
                tool_detail.add_info(tool_info)

    def extract_tool_details(self, node):
        if node.get('class') == 'CommandLineTool':
            print('replacing', self.prefix)
            tool_name = node.get('id').replace(self.prefix, '', 1)
            if self.tool_exists(tool_name):  # skip if already extracted
                return
            tool_info = {} # Need to unique these
            reqs = node.get('requirements')
            if reqs:
                self.extract_requirements(reqs, tool_info)
            hints = node.get('hints')
            if hints:
                self.extract_requirements(hints, tool_info)
            if tool_info: # only add if we have data
                self.details.append({'tool_name': tool_name, 'tool_info': tool_info})

    def make_details_list(self):
        details_list = []
        for detail in self.details:
            tool_name = detail.get('tool_name', '')
            docker_infos_list = detail.get('tool_info', {}).get('docker', {})
            docker_images = [d.get('image_name','') for d in docker_infos_list]
            software_infos_list = detail.get('tool_info', {}).get('software', {})
            packages_and_versions = []
            for info in software_infos_list:
                packages_and_versions.append({'package': info.get('package'), 'versions': info.get('versions'), 'citation': info.get('citation')})
            tool_detail = {
              'tool_name': tool_name,
              'docker_images': docker_images,
              'packages': packages_and_versions,
            }
            details_list.append(tool_detail)
        return details_list


def extract_tool_details(workflow_version):
    loader = BespinWorkflowLoader(workflow_version)
    parser = BespinWorkflowParser(loader.load())
    prefix = loader.get_prefix()
    extractor = ToolDetailsExtractor(prefix)
    extractor.accept(parser.loaded_workflow)
    return extractor.make_details_list()
