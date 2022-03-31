# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import functools
import sys
import os

import ftrack_api

cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
sys.path.append(sources)

def on_discover_unreal_engine_integration(session, event):

    from ftrack_connect_unreal_engine import __version__ as integration_version

    data = {
        'integration': {
            "name": 'ftrack-connect-unreal-engine',
            'version': integration_version
        }
    }

    return data

def on_launch_unreal_engine_integration(session, event):
    unreal_base_data = on_discover_unreal_engine_integration(session, event)

    unreal_base_data['integration']['env'] = {
        'PYTHONPATH.prepend': os.path.pathsep.join([sources]),
        'QT_PREFERRED_BINDING': 'PySide',
        'LOGNAME.set': session._api_user,
        'FTRACK_APIKEY.set': session._api_key,
    }

    selection = event['data'].get('context', {}).get('selection', [])
    
    if selection:
        task = session.get('Context', selection[0]['entityId'])
        unreal_base_data['integration']['env']['FTRACK_TASKID.set'] =  task['id']
        unreal_base_data['integration']['env']['FTRACK_SHOTID.set'] =  task['parent']['id']
        unreal_base_data['integration']['env']['FS.set'] = task['parent']['custom_attributes'].get('fstart', '1.0')
        unreal_base_data['integration']['env']['FE.set'] = task['parent']['custom_attributes'].get('fend', '100.0')
        unreal_base_data['integration']['env']['FPS.set'] = task['parent']['custom_attributes'].get('fps', '24.0')

    return unreal_base_data

def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_unreal_engine_integration,
        session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=unreal-engine*'
        ' and data.application.version <= 4.25.0',
        handle_discovery_event
    )


    handle_launch_event = functools.partial(
        on_launch_unreal_engine_integration,
        session
    )    

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=unreal-engine*'
        ' and data.application.version <= 4.25.0',
        handle_launch_event
    )
    
