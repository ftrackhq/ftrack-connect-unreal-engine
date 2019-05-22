# :coding: utf-8
# :copyright: Copyright (c) 2018 Pinta Studios

import getpass
import logging
import os
import pprint
import re
import sys

import ftrack
import ftrack_connect.application

cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
ftrack_connect_unreal_engine_resource_path = os.path.abspath(
    os.path.join(cwd, '..', 'resource'))
sys.path.append(sources)

import ftrack_connect_unreal_engine

class LaunchApplicationAction(object):
    '''Discover and launch unreal engine.'''

    # Unique action identifier.
    identifier = 'ftrack-connect-launch-unreal-engine'

    def __init__(self, applicationStore, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchApplicationAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.applicationStore = applicationStore
        self.launcher = launcher

        if self.identifier is None:
            raise ValueError('The action must be given an identifier.')

    def is_valid_selection(self, selection):
        '''Return true if the selection is valid.

        Unreal can be launched only if the selection is Project.
        '''

        entity = selection[0]
        task = ftrack.Task(entity['entityId'])

        if task.getObjectType() != 'Task':
            return False

        return True

    def register(self):
        '''Register discover actions on logged in user.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.plugin.debug-information',
            self.get_version_information
        )

    def discover(self, event):
        '''Return available actions based on *event*.

        Each action should contain

            actionIdentifier - Unique identifier for the action
            label - Nice name to display in ftrack
            icon(optional) - predefined icon or URL to an image
            applicationIdentifier - Unique identifier to identify application
                                    in store.

        '''

        if not self.is_valid_selection(
                event['data'].get('selection', [])
        ):
            return

        items = []
        applications = self.applicationStore.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'variant': application.get('variant', None),
                'description': application.get('description', None),
                'icon': application.get('icon', 'default'),
                'applicationIdentifier': applicationIdentifier
            })

        return {
            'items': items
        }

    def launch(self, event):
        '''Callback method for Unreal action.'''
        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()
        context['source'] = event['source']#Martin to check doc :-) https://help.ftrack.com/developing-with-ftrack/key-concepts/events

        return self.launcher.launch(
            applicationIdentifier, context
        )

    def get_version_information(self, event):
        '''Return version information.'''
        return dict(
            name='ftrack connect unreal engine',
            version=ftrack_connect_unreal_engine.__version__
        )


class ApplicationStore(ftrack_connect.application.ApplicationStore):
    '''Store used to find and keep track of available applications.'''

    def _checkUnrealLocation(self):
        ''' Return Unreal installation location by reading the data file'''
        prefix = None

        document = open(
            "C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat",
            "r+")

        context = document.read()

        import ast
        for item in ast.literal_eval(context)['InstallationList']:
            if item['AppName'].find('UE_') == 0:
                prefix = item['InstallLocation'].split(
                    '\\' + item['AppName'])[0].split('\\')

        document.close()

        return prefix

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.
        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Users', 'Shared', 'Epic Games']
            applications.extend(self._searchFilesystem(
                expression=prefix + [
                    'UE_.+', 'Engine', 'Binaries', 'Mac', 'UE4Editor.app'],
                versionExpression=re.compile(
                    r'(?P<version>[\d.]+[\d.]+[\d.])'
                ),
                applicationIdentifier='Unreal_{version}',
                label='Unreal Engine',
                variant='{version}',
                icon='https://cdn4.iconfinder.com/data/icons/various-icons-2/476/Unreal_Engine.png'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            unreal_location = self._checkUnrealLocation()
            if unreal_location:
                prefix = unreal_location

            unreal_version_expression = re.compile(
                r'(?P<version>[\d.]+[\d.]+[\d.])'
            )

            applications.extend(self._searchFilesystem(
                expression=(
                    prefix +
                    ['UE.+', 'Engine', 'Binaries', 'Win64', 'UE4Editor.exe']
                ),
                versionExpression=unreal_version_expression,
                label='Unreal Engine',
                variant='{version}',
                applicationIdentifier='Unreal_{version}',
                icon='https://cdn4.iconfinder.com/data/icons/various-icons-2/476/Unreal_Engine.png'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):
    '''Custom launcher to modify environment before launch.'''

    def _getApplicationEnvironment(
        self, application, context=None
    ):
        '''Override to modify environment before launch.'''

        # Make sure to call super to retrieve original environment
        # which contains the selection and ftrack API.
        environment = super(
            ApplicationLauncher, self
        )._getApplicationEnvironment(application, context)


        entity = context['selection'][0]
        environment['FTRACK_CONTEXTID'] = entity['entityId']
        environment['QT_PREFERRED_BINDING'] = 'PySide'
        task = ftrack.Task(entity['entityId'])
        environment['FTRACK_TASKID'] = task.getId()
        environment['FTRACK_SHOTID'] = task.get('parent_id')

        environment = ftrack_connect.application.appendPath(
            sources,
            'PYTHONPATH',
            environment
        )

        #get absolute path of ftrack installation from executable
        ftrack_installation_path = os.path.dirname(sys.executable)

        self.logger.debug(
            'sys executable:\n{0}'.format(
                pprint.pformat(ftrack_installation_path)
            )
        )

        environment = ftrack_connect.application.appendPath(
            ftrack_installation_path,
            'PYTHONPATH',
            environment
        )

        environment = ftrack_connect.application.appendPath(
           ftrack_installation_path,
           'QT_PLUGIN_PATH',
           environment
       )

        environment = ftrack_connect.application.appendPath(
            os.path.join(ftrack_installation_path, "library.zip"),
            'PYTHONPATH',
            environment
        )

        # Always return the environment at the end.
        return environment


def register(registry, **kw):
    '''Register hooks.'''

    # Validate that registry is the correct ftrack.Registry. If not,
    # assume that register is being called with another purpose or from a
    # new or incompatible API and return without doing anything.
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    # Create store containing applications.
    applicationStore = ApplicationStore()

    # Create a launcher with the store containing applications.
    launcher = ApplicationLauncher(
        applicationStore
    )

    # Create action and register to respond to discover and launch actions.
    action = LaunchApplicationAction(applicationStore, launcher)
    action.register()
