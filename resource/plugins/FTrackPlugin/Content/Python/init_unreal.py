# :coding: utf-8
# :Copyright 2019 ftrack. All Rights Reserved.
import logging

logger = logging.getLogger('ftrack_connect_unreal')

try:
    import ftrack_connect_unreal_engine.bootstrap
except ImportError as error:
    logger.error(
        'ftrack connect Unreal plugin is not well initialized '
        'or you did not start Unreal from ftrack connect.'
        'Error {}'.format(error),
        exc_info=True
    )
