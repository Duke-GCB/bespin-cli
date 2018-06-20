import requests
from bespin.exceptions import JobDoesNotExistException

CONTENT_TYPE = 'application/json'


class BespinApi(object):
    """
    Communicates with Bespin API via REST
    """
    def __init__(self, config, user_agent_str):
        self.config = config
        self.user_agent_str = user_agent_str

    def _build_url(self, url_suffix):
        return '{}{}'.format(self.config.url, url_suffix)

    def _build_headers(self):
        return {
            'user-agent': self.user_agent_str,
            'Authorization': 'Token {}'.format(self.config.token),
            'content-type': CONTENT_TYPE,
        }

    def _get_request(self, url_suffix):
        url = self._build_url(url_suffix)
        headers = self._build_headers()
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError as ex:
            raise BespinException("Failed to connect to {}\n{}".format(self.config.url, ex))
        self._check_response(response)
        return response.json()

    def _post_request(self, url_suffix, data):
        url = self._build_url(url_suffix)
        headers = self._build_headers()
        try:
            response = requests.post(url, headers=headers, json=data)
        except requests.exceptions.ConnectionError as ex:
            raise BespinException("Failed to connect to {}\n{}".format(self.config.url, ex))
        self._check_response(response)
        return response.json()

    def _delete_request(self, url_suffix):
        url = self._build_url(url_suffix)
        headers = self._build_headers()
        try:
            response = requests.delete(url, headers=headers)
        except requests.exceptions.ConnectionError as ex:
            raise BespinException("Failed to connect to {}\n{}".format(self.config.url, ex))
        self._check_response(response)
        return response

    @staticmethod
    def _check_response(response):
        try:
            if response.status_code == 404:
                raise NotFoundException(BespinApi.make_message_for_http_error(response))
            response.raise_for_status()
        except requests.HTTPError:
            raise BespinException(BespinApi.make_message_for_http_error(response))

    @staticmethod
    def make_message_for_http_error(response):
        message = response.text
        try:
            data = response.json()
            if 'detail' in data:
                message = data['detail']
        except ValueError:
            pass  # response was not JSON
        return message

    def jobs_list(self):
        return self._get_request('/jobs/')

    def workflows_list(self):
        return self._get_request('/workflows/')

    def workflow_versions_list(self):
        return self._get_request('/workflow-versions/')

    def workflow_version_get(self, workflow_version):
        return self._get_request('/workflow-versions/{}/'.format(workflow_version))

    def questionnaires_list(self, workflow_version=None, tag=None):
        url = '/job-questionnaires/'
        if workflow_version or tag:
            url += "?"
            if workflow_version:
                url += "workflow_version={}".format(workflow_version)
            if tag:
                if workflow_version:
                    url += "&"
                url += "tag={}".format(tag)
        return self._get_request(url)

    def questionnaire_get(self, questionnaire_id):
        return self._get_request('/job-questionnaires/{}/'.format(questionnaire_id))

    def stage_group_post(self):
        return self._post_request('/job-file-stage-groups/', {})

    def dds_job_input_files_post(self, project_id, file_id, destination_path, sequence_group, sequence,
                                 dds_user_credentials, stage_group_id):
        data = {
            "project_id": project_id,
            "file_id": file_id,
            "destination_path": destination_path,
            "sequence_group": sequence_group,
            "sequence": sequence,
            "dds_user_credentials": dds_user_credentials,
            "stage_group": stage_group_id
        }
        return self._post_request('/dds-job-input-files/', data)

    def job_answer_set_post(self, job_name, fund_code, user_job_order_json, questionnaire_id, stage_group_id):
        data = {
            "job_name": job_name,
            "fund_code": fund_code,
            "user_job_order_json": user_job_order_json,
            "questionnaire": questionnaire_id,
            "stage_group": stage_group_id
        }
        return self._post_request('/job-answer-sets/', data)

    def job_answer_set_create_job(self, job_answer_set_id):
        return self._post_request('/job-answer-sets/{}/create-job/'.format(job_answer_set_id), {})

    def authorize_job(self, job_id, token):
        return self._post_request('/jobs/{}/authorize/'.format(job_id), {'token': token})

    def start_job(self, job_id):
        try:
            return self._post_request('/jobs/{}/start/'.format(job_id), {})
        except NotFoundException as e:
            raise JobDoesNotExistException("No job found for id: {}.".format(job_id))

    def cancel_job(self, job_id):
        try:
            return self._post_request('/jobs/{}/cancel/'.format(job_id), {})
        except NotFoundException as e:
            raise JobDoesNotExistException("No job found for id: {}.".format(job_id))

    def restart_job(self, job_id):
        try:
            return self._post_request('/jobs/{}/restart/'.format(job_id), {})
        except NotFoundException as e:
            raise JobDoesNotExistException("No job found for id: {}.".format(job_id))

    def delete_job(self, job_id):
        try:
            return self._delete_request('/jobs/{}'.format(job_id))
        except NotFoundException as e:
            raise JobDoesNotExistException("No job found for id: {}.".format(job_id))

    def dds_user_credentials_list(self):
        return self._get_request('/dds-user-credentials/')


class BespinException(Exception):
    pass


class NotFoundException(BespinException):
    pass
