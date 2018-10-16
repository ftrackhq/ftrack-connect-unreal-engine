# :coding: utf-8
# :copyright: Copyright (c) 2018 pintastudio
import os
os.sys.path.append( os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__), '..', 'plugins'
                        )
                    )
                )
os.sys.path.append( os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__), '..', '..', '..', 'library.zip'
                        )
                    )
                )
import logging
import ftrack
import functools

import ftrack_connect.util
import ftrack_connect.asset_version_scanner
import ftrack_connect.config

from ftrack_connect_unreal.connector import Connector
from ftrack_connect_unreal.ui.asset_manager_unreal import FtrackAssetManagerDialog
from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
from ftrack_connect_unreal.ui.tasks import FtrackTasksDialog

from QtExt.QtGui import QApplication
from QtExt import QtGui

import traceback
import unreal_engine as ue
from unreal_engine.classes import BlueprintFactory,PrimaryDataAsset

ftrack.setup()

currentEntity = ftrack.Task(
    os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
)


dialogs = [
    (FtrackImportAssetDialog, 'Import asset'),

    (FtrackAssetManagerDialog, 'Asset manager'),

    (FtrackTasksDialog, 'Tasks')
]

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
        #print 'DEBUG: '+ os.path.dirname(__file__)
        app.setWindowIcon(QtGui.QIcon(os.path.dirname(__file__)+'/UE4Ftrack.ico'))
    else:
        print("App already running.")


def open_dialog(dialog_class):
    '''Open *dialog_class* and create if not already existing.'''
    QApplicationInit()

    dialog_name = dialog_class

    if dialog_name ==FtrackImportAssetDialog and dialog_name in created_dialogs:

        created_dialogs[dialog_name].deleteLater()
        created_dialogs[dialog_name]=None
        del created_dialogs[dialog_name]


    if dialog_name not in created_dialogs:
        ftrack_dialog = dialog_class(connector=connector)

        created_dialogs[dialog_name] = ftrack_dialog

    if created_dialogs[dialog_name]!=None:
        created_dialogs[dialog_name].show()

def open_menu(menu):
    '''this generates the menu entries'''

    menu.begin_section('Ftrack','Ftrack')

    for item in dialogs:
        
        dialog_class, label = item
        menu.add_menu_entry(label,label, open_dialog, dialog_class)

    menu.end_section()

def loadAndInit():
    '''Load and Init the unreal plugin, build the widgets and set the menu'''
    # Load the ftrack unreal plugin
    # Create new connector and register the assets
    
    connector.registerAssets()

    ue.add_menu_bar_extension('Ftrack', open_menu)
        
    # Check if ftrack struct exists in the project, if not, create a new one.

    bp = ue.find_object('ftrackNodeStruct')

    if not bp:
        bp = ue.create_blueprint(PrimaryDataAsset, '/Game/Data/ftrackNodeStruct')

        ue.blueprint_add_member_variable(bp, 'assetVersion', 'integer')
        ue.blueprint_add_member_variable(bp, 'assetId', 'string')
        ue.blueprint_add_member_variable(bp, 'assetPath', 'string')
        ue.blueprint_add_member_variable(bp, 'assetTake', 'name')
        ue.blueprint_add_member_variable(bp, 'assetType', 'string')
        ue.blueprint_add_member_variable(bp, 'assetComponentId', 'string')
        ue.blueprint_add_member_variable(bp, 'assetLink', 'string')

        ue.compile_blueprint(bp)

        bp.save_package()




def handle_scan_result(result, scanned_ftrack_nodes):
    '''Handle scan *result*.'''
    pass


def scan_for_new_assets():
    '''Check whether there is any new asset.'''
    pass


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


if not Connector.batch():
    
    refAssetManager()
    loadAndInit()



ftrack_connect.config.configure_logging(
    'ftrack_connect_unreal', level='WARNING'
)
