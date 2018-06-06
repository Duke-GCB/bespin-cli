import sys
import pkg_resources
from bespin.argparse import ArgParser
from bespin.commands import Commands
from bespin.config import ConfigSetupAbandoned
from bespin.exceptions import UserInputException

APP_NAME = 'bespin'


def main():
    version_str = pkg_resources.get_distribution(APP_NAME).version
    user_agent_str = '{}_{}'.format(APP_NAME, version_str)
    arg_parser = ArgParser(version_str, Commands(version_str, user_agent_str))
    try:
        arg_parser.parse_and_run_commands()
    except ConfigSetupAbandoned:
        pass
    except UserInputException as e:
        print(str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
