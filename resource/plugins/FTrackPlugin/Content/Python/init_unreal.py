# :coding: utf-8
# :Copyright 2019 ftrack. All Rights Reserved.

try:
    import ftrack_connect_unreal_engine.bootstrap
except ImportError:
    print('ftrack connect Unreal plugin is not well initialized ' + 
            'or you did not start Unreal from ftrack connect')