# :coding: utf-8
# :copyright: Copyright (c) 2018 Pinta Studios

import functools
import logging
import os
import traceback
import sys

import ftrack
import ftrack_connect.asset_version_scanner
import ftrack_connect.config
import ftrack_connect.util
import unreal as ue
from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
from ftrack_connect_unreal_engine.connector.unrealcon import Connector
from ftrack_connect_unreal_engine.ui.asset_manager_unreal import \
    FtrackUnrealAssetManagerDialog
from ftrack_connect_unreal_engine.ui.info import FtrackUnrealInfoDialog
from ftrack_connect_unreal_engine.ui.tasks import FtrackTasksDialog
from QtExt import QtGui
from QtExt.QtGui import QApplication


ftrack.setup()

currentEntity = ftrack.Task(
    os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
)

created_dialogs = dict()
connector = Connector()


def ue_exception(_type, value, back):
    ue.log_error(value)
    tb_lines = traceback.format_exception(_type, value, back)
    for line in tb_lines:
        ue.log_error(line)


def QApplicationInit():
    os.sys.excepthook = ue_exception

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        app.setWindowIcon(QtGui.QIcon(os.path.dirname(__file__)+'/UE4Ftrack.ico'))
    else:
        print("App already running.")

def loadAndInit():
    '''Load and Init the unreal plugin, build the widgets and set the menu'''
    # Load the ftrack unreal plugin
    #TODO:Need to implement unreal_ftrack Node here by Hao

    # Create new connector and register the assets
    connector.registerAssets()
    QApplicationInit()
    def _app_tick(dt):
        QApplication.processEvents()
    ue.register_slate_post_tick_callback(_app_tick)
    



def refAssetManager():
    '''Refresh asset manager'''
    from ftrack_connect.connector import panelcom
    panelComInstance = panelcom.PanelComInstance.instance()
    panelComInstance.refreshListeners()


def framerateInit():
    '''Set the initial framerate with the values set on the shot'''
    import ftrack
    shotId = os.getenv('FTRACK_SHOTID')
    shot = ftrack.Shot(id=shotId)
    fps = str(int(shot.get('fps')))

    mapping = {
        '15': 'game',
        '24': 'film',
        '25': 'pal',
        '30': 'ntsc',
        '48': 'show',
        '50': 'palf',
        '60': 'ntscf',
    }

    fpsType = mapping.get(fps, 'pal')
    ue.log('Setting current unit to {0}'.format(fps))

def open_dialog(dialog_class, title):
    '''Open *dialog_class* and create if not already existing.'''
    QApplicationInit()

    dialog_name = dialog_class

    if dialog_name == FtrackImportAssetDialog and dialog_name in created_dialogs:
        created_dialogs[dialog_name].deleteLater()
        created_dialogs[dialog_name]=None
        del created_dialogs[dialog_name]

    if dialog_name not in created_dialogs:
        ftrack_dialog = dialog_class(connector=connector)
        ftrack_dialog.setWindowTitle(title)
        created_dialogs[dialog_name] = ftrack_dialog
        #this does not seem to work but is the logical way of operating.
        ue.parent_external_window_to_slate(ftrack_dialog.effectiveWinId())

    if created_dialogs[dialog_name]!=None:
        created_dialogs[dialog_name].show()


def openAssetManagerDialog():
    open_dialog(FtrackUnrealAssetManagerDialog, 'Asset manager')

def openImportAssetDialog():
    open_dialog(FtrackImportAssetDialog, 'Import asset')

def openInfoDialog():
    open_dialog(FtrackUnrealInfoDialog, 'Info')

def openTasksDialog():
    open_dialog(FtrackTasksDialog, 'Tasks')

if not Connector.batch():
    refAssetManager()
    loadAndInit()

ftrack_connect.config.configure_logging(
    'ftrack_connect_unreal', level='WARNING'
)
