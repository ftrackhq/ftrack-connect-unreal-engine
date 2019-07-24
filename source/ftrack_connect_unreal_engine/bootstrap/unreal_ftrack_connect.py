# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import traceback
import logging

import unreal
import ftrack
import ftrack_connect.config
from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
from ftrack_connect_unreal_engine.connector.unrealcon import Connector
from ftrack_connect_unreal_engine.ui.asset_manager_unreal import \
    FtrackUnrealAssetManagerDialog
from ftrack_connect_unreal_engine.ui.info import FtrackUnrealInfoDialog
from ftrack_connect_unreal_engine.ui.tasks import FtrackTasksDialog
from ftrack_connect_unreal_engine.ui.publisher import FtrackPublishDialog
from QtExt import QtGui
from QtExt.QtGui import QApplication


class Command(object):
    """
        Command object allowing binding between UI and actions
    """
    def __init__(self, name, display_name, description, command_type = "dialog", user_data = None ):
        self.name = name
        self.displayName = display_name
        self.description = description
        self.commandType = command_type
        self.userData = user_data

class FTrackContext(object):
    """
        Generic context ftrack object allowing caching of python specific data.
    """
    def __init__(self):
        self.connector = None
        self.dialogs = dict()
        self.tickHandle = None
        self._init_commands()
        self._init_tags()
        self._init_capture_arguments()

    def _init_commands(self):
        self.commands = []
        #main menu commands
        self.commands.append(Command("ftrackImportAsset", "Import asset","ftrack import asset","dialog",FtrackImportAssetDialog))
        self.commands.append(Command("", "","","separator"))
        self.commands.append(Command("ftrackAssetManager", "Asset manager","ftrack browser","dialog",FtrackUnrealAssetManagerDialog))
        self.commands.append(Command("", "", "", "separator"))
        self.commands.append(Command("ftrackPublish", "Publish","ftrack publish","dialog",FtrackPublishDialog))
        self.commands.append(Command("", "", "", "separator"))
        self.commands.append(Command("ftrackInfo", "Info","ftrack info","dialog",FtrackUnrealInfoDialog))
        self.commands.append(Command("ftrackTasks", "Tasks","ftrack tasks","dialog",FtrackTasksDialog))

    def _init_tags(self):
        self.tags = []
        tagPrefix = "ftrack."
        self.tags.append(tagPrefix + "IntegrationVersion")
        self.tags.append(tagPrefix + "AssetComponentId")
        self.tags.append(tagPrefix + "AssetVersionId")
        self.tags.append(tagPrefix + "ComponentName")
        self.tags.append(tagPrefix + "AssetId")
        self.tags.append(tagPrefix + "AssetType")
        self.tags.append(tagPrefix + "AssetVersion")

    def _init_capture_arguments(self):
        self.capture_args = []
        self.capture_args.append("-ResX=1280")
        self.capture_args.append("-ResY=720")
        self.capture_args.append("-MovieFrameRate=24")
        self.capture_args.append("-MovieQuality=75")


    def external_init(self):
        self.connector = Connector()

ftrackContext = FTrackContext()


@unreal.uclass()
class FTrackConnectWrapper(unreal.FTrackConnect):
    """
        Main class for binding and interacting between python and ftrack C++ plugin.
    """

    def _post_init(self):
        """
        Equivalent to __init__ but will also be called from C++
        """
        ftrack.setup()

        self.currentEntity = ftrack.Task(
            os.getenv('FTRACK_TASKID'), os.getenv('FTRACK_SHOTID')
        )

        ftrackContext.external_init()
        ftrackContext.connector.registerAssets()
        ftrackContext.connector.setTimeLine()

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            app.setWindowIcon(QtGui.QIcon(os.path.dirname(__file__)+'/UE4Ftrack.ico'))

        def _app_tick(dt):
            QApplication.processEvents()

        ftrackContext.tickHandle = unreal.register_slate_post_tick_callback(_app_tick)

        def _app_quit(dt):
            unreal.register_slate_post_tick_callback(ftrackContext.tickHandle)

        QApplication.instance().aboutToQuit.connect(_app_quit)

        for tag in ftrackContext.tags:
            self.add_global_tag_in_asset_registry(tag)

        # Install the ftrack logging handlers
        ftrack_connect.config.configure_logging('ftrack_connect_unreal', level='INFO')

        self.on_connect_initialized()


    @unreal.ufunction(override=True)
    def shutdown(self):
        QApplication.instance().quit()
        QApplication.processEvents()

    @unreal.ufunction(override=True)
    def get_ftrack_menu_items(self):
        menu_items = []
        for command in ftrackContext.commands:
            menu_item = unreal.FTrackMenuItem()
            menu_item.display_name = command.displayName
            menu_item.name = command.name
            menu_item.type = command.commandType
            menu_item.description = command.description
            menu_items.append(menu_item)
        return menu_items

    @unreal.ufunction(override=True)
    def execute_command(self, command_name):
        for command in ftrackContext.commands:
            if command.name == command_name:
                if command.commandType == "dialog":
                    logging.info('Executing command' + command.name)
                    self._open_dialog(command.userData,command.displayName)
                    break

    def _open_dialog(self, dialog_class, title):
        '''Open *dialog_class* and create if not already existing.'''
        dialog_name = dialog_class

        if (dialog_name == FtrackImportAssetDialog or
            dialog_name == FtrackPublishDialog) \
            and dialog_name in ftrackContext.dialogs:
            ftrackContext.dialogs[dialog_name].deleteLater()
            ftrackContext.dialogs[dialog_name] = None
            del ftrackContext.dialogs[dialog_name]

        if dialog_name not in ftrackContext.dialogs:
            ftrack_dialog = dialog_class(connector=ftrackContext.connector)
            ftrack_dialog.setWindowTitle(title)
            ftrackContext.dialogs[dialog_name] = ftrack_dialog
            #this does not seem to work but is the logical way of operating.
            unreal.parent_external_window_to_slate(ftrack_dialog.effectiveWinId())

        if ftrackContext.dialogs[dialog_name] is not None:
            ftrackContext.dialogs[dialog_name].show()


    @unreal.ufunction(override=True)
    def get_capture_arguments(self):
        str_capture_args = ''
        for capture_arg in ftrackContext.capture_args:
            str_capture_args += capture_arg
            str_capture_args += ' '
        return str_capture_args
