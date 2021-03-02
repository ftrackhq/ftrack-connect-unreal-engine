# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import functools
import sys
import os

import ftrack_api


def on_discover_unreal_engine_integration(session, event):


    cwd = os.path.dirname(__file__)
    sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
    ftrack_connect_unreal_engine_resource_path = os.path.abspath(
        os.path.join(cwd, '..',  'resource')
    )
    sys.path.append(sources)

    from ftrack_connect_unreal_engine import __version__ as integration_version


    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    data = {
        'integration': {
            "name": 'ftrack-connect-unreal-engine',
            'version': integration_version,
            'env': {
                'PYTHONPATH.prepend': os.path.pathsep.join(
                    [sources]
                ),
                'QT_PREFERRED_BINDING': 'PySide',
                'FTRACK_TASKID.set': task['id'],
                'FTRACK_SHOTID.set': task['parent']['id'],
                'LOGNAME.set': session._api_user,
                'FTRACK_APIKEY.set': session._api_key,
                'FS.set': task['parent']['custom_attributes'].get('fstart', '1.0'),
                'FE.set': task['parent']['custom_attributes'].get('fend', '100.0'),
                'FPS.set': task['parent']['custom_attributes'].get('fps', '24.0')
            }
        }
    }
    return data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return


    handle_event = functools.partial(
        on_discover_unreal_engine_integration,
        session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=unreal-engine*'
        ' and data.application.version <= 4.25',

        handle_event
    )
    
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=unreal-engine*'
        ' and data.application.version <= 4.25',

        handle_event
    )