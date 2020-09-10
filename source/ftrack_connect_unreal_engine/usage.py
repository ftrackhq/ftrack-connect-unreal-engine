# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import ftrack_connect_unreal_engine
import ftrack_connect.usage
import platform


def send_event(event_name, metadata=None):
    '''Send usage information to server.'''

    if metadata is None:
        metadata = {
            'operating_system': platform.platform(),
            'ftrack_connect_unreal_engine_version': ftrack_connect_unreal_engine.__version__
        }

    ftrack_connect.usage.send_event(
        event_name, metadata
    )
