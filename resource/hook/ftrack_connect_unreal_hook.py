# :coding: utf-8
# :copyright: Copyright (c) 2018 pintastudio

import getpass
import logging
import sys
import pprint
import os
import re
import ast
import ftrack
import ftrack_connect.application
import _winreg


class UnrealAction(object):
    '''Launch Unreal action.'''

    # Unique action identifier.
    identifier = 'my-Unreal-launch-action'

    def __init__(self, applicationStore, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(UnrealAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.applicationStore = applicationStore
        self.launcher = launcher

        if self.identifier is None:
            raise ValueError('The action must be given an identifier.')


    def is_valid_selection(self, selection):
        '''Return true if the selection is valid. Unreal can be launched only if the selection is Project'''

        if (
            len(selection) != 1 or
            selection[0]['entityType'] != 'show'
        ):
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

        selection = event['data'].get('selection', [])
        entity = selection[0]
        project = ftrack.Project(entity['entityId'])
        ftrack_project_name = project.getName()

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

        return self.launcher.launch(
            applicationIdentifier, context
        )
    
    def get_version_information(self, event):
        '''Return version information.'''
        return dict(
            name='ftrack connect unreal',
            version=''
        )

class ApplicationStore(ftrack_connect.application.ApplicationStore):
    '''Store used to find and keep track of available applications.'''


    def _checkUnrealLocation(self):
        ''' Return Unreal installation location by reading the data file'''
        prefix = None

        document = open("C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat", "r+")

        context = document.read()

        for item in ast.literal_eval(context)['InstallationList']:
            if item['AppName'].find('UE_') == 0:
                prefix = item['InstallLocation'].split('\\' + item['AppName'])[0].split('\\')

        document.close()

        return prefix



    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.
        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._searchFilesystem(
                expression=prefix + [
                    'Unreal*', 'Unreal.app'
                ],
                label='Unreal {version}',
                applicationIdentifier='Unreal_{version}'
            ))

        elif sys.platform == 'win32':
            prefix = ['D:\\', 'Program Files.*']

            unreal_location = self._checkUnrealLocation()
            if unreal_location:
                prefix = unreal_location


            unreal_version_expression = re.compile(
				r'(?P<version>[\d.]+[\d.]+[\d.])'
			)
            
            self.logger.info('Unreal version:\n{0}'.format(unreal_version_expression))

            applications.extend(self._searchFilesystem(
                expression=(
                    prefix +
                    ['UE+', 'Engine', 'Binaries', 'Win64', 'UE4Editor.exe']
                ),
                versionExpression=unreal_version_expression,
                label='Unreal Engine',
                variant='{version}',
                applicationIdentifier='Unreal_{version}'
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
        project = ftrack.Project(entity['entityId'])


        # Set default task id and shot id for Unreal ftrack plugin to start, this is required although it is useless in Unreal.
        environment['FTRACK_TASKID'] = project.getAssetBuilds()[0].getId()
        
        environment['FTRACK_SHOTID'] = project.getAssetBuilds()[0].get('parent_id')

        # Append or Prepend values to the environment.
        # Note that if you assign manually you will overwrite any
        # existing values on that variable.

        # Add my custom path to the Unreal_SCRIPT_PATH.
        environment = ftrack_connect.application.appendPath(
            'path/to/my/custom/scripts',
            'Unreal_SCRIPT_PATH',
            environment
        )

        # Set an internal user id of some kind.
        environment = ftrack_connect.application.appendPath(
            'my-unique-user-id-123',
            'STUDIO_SPECIFIC_USERID',
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
    action = UnrealAction(applicationStore, launcher)
    action.register()
