from setuptools import setup

setup(name='bespin',
      version='0.0.1',
      description='Command line tool to run workflows via Bespin.',
      author='John Bradley',
      license='MIT',
      packages=['bespin'],
      install_requires=[
          'DukeDSClient',
          'future',
          'PyYAML',
          'requests',
          'six',
          'tabulate',
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
      )
