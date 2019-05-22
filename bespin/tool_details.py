"""
Classes in this file are designed to extract software package names, versions, Docker images, and web links (citations)
from the tools included in a parsed and in-memory CWL workflow. It relies heavily on the CWL v1.0 requirements
documented at https://www.commonwl.org/v1.0/CommandLineTool.html, namely DockerRequirement, SoftwareRequirement,
and SoftwarePackage

"""
from bespin.workflow import BespinWorkflowLoader, BespinWorkflowParser


class DockerToolDetail(object):
    """
    Extracts the Docker image name from a DockerRequirement
    """

    def __init__(self, req_dict):
        self.docker_image_name = req_dict.get('dockerPull')

    def add_info(self, info_dict):
        """
        Update the provided dictionary with this object's docker image name
        :param info_dict: A dictionary of tool info to update
        """
        docker_infos = [{'image_name': self.docker_image_name}]
        info_dict['docker'] = docker_infos


class SoftwareToolDetail(object):
    """
    Extracts the software package name, versions, and citation link from a SoftwareRequirement
    """

    def __init__(self, req_dict):
        self.packages = req_dict.get('packages')

    def add_info(self, info_dict):
        """
        Update the provided dictionary with this object's software details
        :param info_dict: A dictionary of tool info to update
        :return:
        """
        software_info = []
        for package in self.packages:
            software_info.append({
                'package': package.get('package'),
                'versions': package.get('version', []),
                'citation': package.get('https://schema.org/citation')
            })
        info_dict['software'] = software_info


class ToolDetailsBuilder(object):
    """
    Tallies a list of tool details, using a loaded cwltool workflow's visit() method to pull details out of
    every node in the workflow graph of class CommandLineTool
    """

    def __init__(self, prefix):
        self.details = []
        self.prefix = prefix

    def accept(self, visitor):
        visitor.visit(self.extract_tool_details)

    def tool_exists(self, tool_name):
        return tool_name in [detail['tool_name'] for detail in self.details]

    @staticmethod
    def extract_requirements(requirements, tool_info):
        """
        Looks through provided list of requirements, extracting tool details based on the requirement class and updating
        the provided tool_info dictionary
        :param requirements: list containing dicts where 'class' is 'DockerRequirement' and/or 'SoftwareRequirement'
        :param tool_info: A dictionary to update with details pulled out of the requirements
        """
        for req in requirements:
            if req.get('class') == 'DockerRequirement':
                tool_detail = DockerToolDetail(req)
                tool_detail.add_info(tool_info)
            elif req.get('class') == 'SoftwareRequirement':
                tool_detail = SoftwareToolDetail(req)
                tool_detail.add_info(tool_info)

    def extract_tool_details(self, node):
        """
        Visitor function to handle a node in the CWL workflow graph and update self.details
        :param node: A CWL object from the graph, that has a 'class' property
        """
        if node.get('class') == 'CommandLineTool':
            # The id of a tool is a long URI string prefixed with the workflow's URL at time of loading
            # For readability, replace that prefix so that
            #    'file:///tmp/folder1/ba4wt23/workflow-dir/tools/Tool.cwl' can become 'tools/Tool.cwl'
            tool_name = node.get('id').replace(self.prefix, '', 1)
            # Avoid duplicating tools included multiple times in the same workflow
            if self.tool_exists(tool_name):
                return
            tool_info = {}
            reqs = node.get('requirements')
            if reqs:
                self.extract_requirements(reqs, tool_info)
            hints = node.get('hints')
            if hints:
                self.extract_requirements(hints, tool_info)
            if tool_info: # only add if we have data
                self.details.append({'tool_name': tool_name, 'tool_info': tool_info})

    def build(self):
        """
        Provides a simplified details list, restructured from the raw CWL requirements
        :return: A list of dictionaries, one for each tool in self.details
        """
        details_list = []
        for detail in self.details:
            tool_name = detail.get('tool_name', '')
            docker_infos_list = detail.get('tool_info', {}).get('docker', {})
            docker_images = [d.get('image_name','') for d in docker_infos_list]
            software_infos_list = detail.get('tool_info', {}).get('software', {})
            packages_and_versions = []
            for info in software_infos_list:
                packages_and_versions.append({k: info[k] for k in ['package', 'versions', 'citation']})
            tool_detail = {
              'tool_name': tool_name,
              'docker_images': docker_images,
              'packages': packages_and_versions,
            }
            details_list.append(tool_detail)
        return details_list


class ToolDetails(object):
    """
    Given a CWLWorkflowVersion, fetch, load, and parse it. Then build a list of tool details from it.
    """

    def __init__(self, workflow_version):
        loader = BespinWorkflowLoader(workflow_version)
        parser = BespinWorkflowParser(loader.load())
        prefix = loader.get_prefix()
        builder = ToolDetailsBuilder(prefix)
        builder.accept(parser.loaded_workflow)
        self.version = parser.version
        self.tag = parser.tag
        self.contents = builder.build()

    def create(self, api):
        """
        Look up the WorkflowVersion id by tag/version, then POST tool_details for it using the provided BespinApi
        :param api: a BespinApi instance
        :return: response data from the API server
        """
        # To create a ToolDetails, we must first look up the WorkflowVersion by the tag/version for its id
        api_workflow_version = api.workflow_version_find_by_tag_version(self.tag, self.version)
        workflow_version_id = api_workflow_version['id']
        return api.workflow_version_tool_details_post(workflow_version_id, self.contents)
