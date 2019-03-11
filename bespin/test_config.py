from __future__ import absolute_import
from unittest import TestCase
from bespin.config import ConfigFile, Config, ConfigSetupAbandoned, DEFAULT_BESPIN_URL
from mock import patch, Mock, mock_open
import yaml

class ConfigFileTestCase(TestCase):
    @patch('bespin.config.os')
    def test_read_or_create_config_file_exists(self, mock_os):
        config_file = ConfigFile(filename='/tmp/test.yml')
        config_file.read_config = Mock()
        config_file.write_config = Mock()
        config_file._prompt_user_for_token = Mock()

        mock_os.path.exists.return_value = True
        config = config_file.read_or_create_config()

        self.assertEqual(config, config_file.read_config.return_value)
        config_file.read_config.assert_called()
        config_file.write_config.assert_not_called()

    @patch('bespin.config.os')
    def test_read_or_create_config_file_doesnt_exist(self, mock_os):
        config_file = ConfigFile(filename='/tmp/test.yml')
        config_file.read_config = Mock()
        config_file.write_config = Mock()
        config_file._prompt_user_for_token = Mock()

        mock_os.path.exists.return_value = False
        config = config_file.read_or_create_config()

        self.assertEqual(config.token, config_file._prompt_user_for_token.return_value)
        config_file.read_config.assert_not_called()
        config_file.write_config.assert_called()
        config_file._prompt_user_for_token.assert_called()

    def test_read_config(self):
        sample_data = "token: Secret\nurl: someurl"
        config_file = ConfigFile(filename='/tmp/test.yml')
        with patch('bespin.config.open', mock_open(read_data=sample_data)):
            config = config_file.read_config()
        self.assertEqual(config.token, 'Secret')
        self.assertEqual(config.url, 'someurl')

    def test_write_config(self):
        config = Config({'token': 'Secret', 'url': 'someurl'})
        config_file = ConfigFile(filename='/tmp/test.yml')
        mocked_open = mock_open()
        with patch('bespin.config.open', mocked_open):
            config_file.write_config(config)
        write_call_args = mocked_open.return_value.write.call_args_list
        write_strs = ''.join([acall[0][0] for acall in write_call_args])
        self.assertEqual({"token": "Secret", "url": "someurl"}, yaml.safe_load(write_strs))

    def test_prompt_user_for_token(self):
        config_file = ConfigFile(filename='/tmp/test.yml')
        config_file.prompt_user = Mock()
        config_file.prompt_user.return_value = 'stuff'
        self.assertEqual(config_file._prompt_user_for_token(), 'stuff')
        config_file.prompt_user.return_value = None
        with self.assertRaises(ConfigSetupAbandoned):
            config_file._prompt_user_for_token()


class ConfigTestCase(TestCase):
    def setUp(self):
        self.config = Config({
            'token': 'secret',
            'url': 'someurl',
        })

    def test_url(self):
        self.assertEqual(self.config.url, 'someurl')
        self.config._url = None
        self.assertEqual(self.config.url, DEFAULT_BESPIN_URL)

    def test_to_dict(self):
        expected_config_dict = {
            'token': 'secret',
            'url': 'someurl',
        }
        self.assertEqual(self.config.to_dict(), expected_config_dict)

        self.config._url = None
        expected_config_dict = {
            'token': 'secret',
        }
        self.assertEqual(self.config.to_dict(), expected_config_dict)

        self.config._url = None
        self.config.token = None
        expected_config_dict = {
        }
        self.assertEqual(self.config.to_dict(), expected_config_dict)
