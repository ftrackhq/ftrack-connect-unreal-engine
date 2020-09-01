# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import os
import re
import shutil

from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages, Command
from pkg_resources import parse_version
import pip

if parse_version(pip.__version__) < parse_version('19.3.0'):
    raise ValueError('Pip should be version 19.3.0 or higher')

from pip._internal import main as pip_main

# Define paths

PLUGIN_NAME = 'ftrack-connect-unreal-engine-{0}'

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')

SOURCE_PATH = os.path.join(ROOT_PATH, 'source')

README_PATH = os.path.join(ROOT_PATH, 'README.rst')

BUILD_PATH = os.path.join(ROOT_PATH, 'build')

STAGING_PATH = os.path.join(BUILD_PATH, PLUGIN_NAME)

HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')

UNREAL_ICON_PATH = os.path.join(RESOURCE_PATH, 'icon')
UNREAL_PLUGINS_PATH = os.path.join(RESOURCE_PATH, 'plugins')


with open(
    os.path.join(SOURCE_PATH, 'ftrack_connect_unreal_engine', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


# Update staging path with the plugin version
STAGING_PATH = STAGING_PATH.format(VERSION)


# Custom commands.
class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest

        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


class BuildPlugin(Command):
    '''Build plugin.'''

    description = 'Download dependencies and build plugin .'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy plugin files
        shutil.copytree(
            UNREAL_PLUGINS_PATH,
            os.path.join(STAGING_PATH, 'resource', 'plugins'),
        )

        # Copy icon files
        shutil.copytree(
            UNREAL_ICON_PATH, os.path.join(STAGING_PATH, 'resource', 'icon')
        )
        # Copy hook files
        shutil.copytree(HOOK_PATH, os.path.join(STAGING_PATH, 'hook'))

        # Copy readme file
        shutil.copyfile(README_PATH, os.path.join(STAGING_PATH, 'README.md'))

        # Install local dependencies
        pip_main.main(
            [
                'install',
                '.',
                '--target',
                os.path.join(STAGING_PATH, 'dependencies')
            ]
        )

        # Generate plugin zip
        shutil.make_archive(
            os.path.join(BUILD_PATH, PLUGIN_NAME.format(VERSION)),
            'zip',
            STAGING_PATH,
        )


# Configuration.
setup(
    name='ftrack connect unreal engine',
    version=VERSION,
    description='Unreal engine integration with ftrack.',
    long_description=open(README_PATH).read(),
    keywords='',
    url='https://bitbucket.org/taotang123/ftrack-connect-unreal/',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={'': 'source'},
    package_data={'': ['*.ico']},
    setup_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 1',
    ],
    install_requires=[
        'appdirs == 1.4.0',
    ],
    tests_require=['pytest >= 2.3.5, < 3'],
    cmdclass={'test': PyTest, 'build_plugin': BuildPlugin},
)
