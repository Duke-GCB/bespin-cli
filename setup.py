import os
import sys
from setuptools import setup
# version checking derived from https://github.com/levlaz/circleci.py/blob/master/setup.py
from setuptools.command.install import install

# bespin-cli version
VERSION = "0.5.0"


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


setup(name='bespin-cli',
      version=VERSION,
      description='Command line tool to run workflows via Bespin.',
      author='John Bradley',
      license='MIT',
      packages=['bespin'],
      install_requires=[
          'DukeDSClient',
          'future',
          'PyYAML',
          'requests>=2.20.0',
          'six',
          'tabulate',
          'cwltool==1.0.20181217162649',
          'html5lib==1.0.1',
      ],
      entry_points={
          'console_scripts': [
              'bespin = bespin.__main__:main'
          ]
      },
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Topic :: Utilities',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ],
      cmdclass={
        'verify': VerifyVersionCommand,
      },
      test_suite='nose2.collector.collector',
      )
