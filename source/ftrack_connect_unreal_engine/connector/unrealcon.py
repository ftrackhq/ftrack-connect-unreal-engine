# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import uuid

import ftrack_connect.config
from ftrack_connect.connector import base as maincon
from ftrack_connect.connector import FTAssetHandlerInstance
import sys
import logging
import argparse
import signal
import ftrack
import ftrack_api
import ftrack_connect.ui.theme

import unreal as ue

logger = logging.getLogger(__name__)

class Connector(maincon.Connector):
    def __init__(self):
        super(Connector, self).__init__()

    @staticmethod
    def getCurrentEntity():
        return ftrack.Task(
            os.getenv('FTRACK_TASKID'), os.getenv('FTRACK_SHOTID')
        )

    @staticmethod
    def _getTaskParentShotSequence(task):
        session = ftrack_api.Session()
        linksForTask = session.query(
            'select link from Task where id is "' + task.getId() + '"'
        ).first()['link']
        # Remove task itself
        linksForTask.pop()
        linksForTask.reverse()
        parentShotSequence = None

        for item in linksForTask:
            entity = session.get(item['type'], item['id'])
            if (
                entity.__class__.__name__ == 'Shot'
                or entity.__class__.__name__ == 'Sequence'
            ):
                parentShotSequence = entity
                break

        return parentShotSequence

    @staticmethod
    def isTaskPartOfShotOrSequence(task):
        return Connector._getTaskParentShotSequence(task) is not None

    @staticmethod
    def _getLoadedLevelSequence():
        masterLevSeq = None
        actors = ue.EditorLevelLibrary.get_all_level_actors()
        for actor in actors:
            if actor.static_class() == ue.LevelSequenceActor.static_class():
                masterLevSeq = actor.load_sequence()
                break
        return masterLevSeq

    @staticmethod
    def _loadOrCreateMasterSequence(
        sequenceName='TmpSequence', sequenceTarget='/Game'
    ):
        masterSequence = Connector._getLoadedLevelSequence()
        if masterSequence is None:
            pass
            # for now do not create new sequencer based of the information in
            # ftrack but rather assume already it is well setup
            # fn = ue.LevelSequenceFactoryNew()
            # at = ue.AssetToolsHelpers.get_asset_tools()
            # masterSequence = at.create_asset(sequenceName, sequenceTarget,
            #                     ue.LevelSequence.static_class(), fn)
            # if masterSequence:
            #     masterSequence.add_master_track(
            #         ue.MovieSceneCinematicShotTrack().static_class())

            # newActor = ue.EditorLevelLibrary.spawn_actor_from_object(
            #                 masterSequence, [0,0,0])

        return masterSequence

    @staticmethod
    def setTimeLine():
        '''Set time line to FS , FE environment values'''

        if not Connector._getTaskParentShotSequence(
            Connector.getCurrentEntity()
        ):
            return

        # For prototype let's assume it has no shot parent
        # This is for the current frame range
        viewFrameStart = os.getenv('FS')
        viewFrameEnd = os.getenv('FE')
        viewFrameRate = os.getenv('FPS')

        masterSequence = Connector._loadOrCreateMasterSequence()
        if masterSequence:
            masterSequence.set_playback_start(int(viewFrameStart))
            masterSequence.set_playback_end(int(viewFrameEnd))
            masterSequence.set_display_rate(ue.FrameRate(int(viewFrameRate)))
            ue.EditorAssetLibrary.save_loaded_asset(masterSequence)
        else:
            logger.info(
                'No LevelSequence were found in the current map'
                + ' therefore time range cannot be set.'
            )

    @staticmethod
    def getAssets():
        '''Return the available assets in UE project, return the *componentId(s)*'''
        componentIds = []
        assets = (
            ue.AssetRegistryHelpers()
            .get_asset_registry()
            .get_assets_by_path('/Game', True)
        )
        for asset_data in assets:
            # unfortunately to access the tag values objects needs to
            # be in memory....
            asset = asset_data.get_asset()
            asset_component_id = asset_data.get_tag_value(
                'ftrack.AssetComponentId'
            )
            if asset and asset_component_id:
                nameInScene = str(asset.get_name())
                componentIds.append((asset_component_id, nameInScene))

        return componentIds

    @staticmethod
    def getFileName():
        '''Return the *current scene* name'''
        pass

    @staticmethod
    def getMainWindow():
        '''Return the *main window* instance'''
        pass

    @staticmethod
    def wrapinstance(ptr, base=None):
        """
        Utility to convert a pointer to a Qt class instance (PySide/PyQt compatible)

        :param ptr: Pointer to QObject in memory
        :type ptr: long or Swig instance
        :param base: (Optional) Base class to wrap with (Defaults to QObject, which should handle anything)
        :type base: QtGui.QWidget
        :return: QWidget or subclass instance
        :rtype: QtGui.QWidget
        """
        if ptr is None:
            return None

        if not base:
            from QtExt import QtWidgets, QtCore

            base = QtWidgets.QObject

        try:
            from pymel.core.uitypes import pysideWrapInstance
        except ImportError:
            ptr = long(ptr)  # Ensure type
            if 'shiboken' in globals():
                import shiboken

                if base is None:
                    qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
                    metaObj = qObj.metaObject()
                    cls = metaObj.className()
                    superCls = metaObj.superClass().className()
                    if hasattr(QtWidgets, cls):
                        base = getattr(QtWidgets, cls)
                    elif hasattr(QtWidgets, superCls):
                        base = getattr(QtWidgets, superCls)
                    else:
                        base = QtWidgets.QWidget
                return shiboken.wrapInstance(long(ptr), base)
            return None
        else:
            return pysideWrapInstance(ptr, base)

    @staticmethod
    def importAsset(iAObj):
        '''Import the asset provided by *iAObj*'''

        assetHandler = FTAssetHandlerInstance.instance()
        importAsset = assetHandler.getAssetClass(iAObj.assetType)
        if importAsset:
            result = importAsset.importAsset(iAObj)
            Connector.selectObjects(selection=result)
            return 'imported assets ' + str(result)
        else:
            return 'assetType not supported'

    @staticmethod
    def selectObject(applicationObject=''):
        '''Select the *applicationObject*'''
        Connector.selectObjects(selection=[applicationObject])

    @staticmethod
    def selectObjects(selection):
        '''Select the given *selection*'''
        selectionPathNames = []
        assets = (
            ue.AssetRegistryHelpers()
            .get_asset_registry()
            .get_assets_by_path('/Game', True)
        )
        for asset_data in assets:
            # unfortunately to access the tag values objects needs
            # to be in memory....
            asset = asset_data.get_asset()
            if str(asset.get_name()) in selection:
                selectionPathNames.append(asset.get_path_name())

        ue.EditorAssetLibrary.sync_browser_to_objects(selectionPathNames)

    @staticmethod
    def removeObject(applicationObject=''):
        '''Remove the *applicationObject* from the scene'''
        # first get our asset of interest
        componentId = None
        versionId = None
        assets = (
            ue.AssetRegistryHelpers()
            .get_asset_registry()
            .get_assets_by_path('/Game', True)
        )
        for asset_data in assets:
            # unfortunately to access the tag values objects needs to
            # be in memory....
            asset = asset_data.get_asset()
            if str(asset.get_name()) == applicationObject:
                # a single asset can be represented by multiple assets in the
                componentId = ue.EditorAssetLibrary.get_metadata_tag(
                    asset, 'ftrack.AssetComponentId'
                )
                versionId = ue.EditorAssetLibrary.get_metadata_tag(
                    asset, 'ftrack.AssetVersionId'
                )
                break

        if componentId != None and versionId != None:
            for asset_data in assets:
                # unfortunately to access the tag values objects needs to
                # be in memory....
                asset = asset_data.get_asset()
                if (
                    ue.EditorAssetLibrary.get_metadata_tag(
                        asset, 'ftrack.AssetComponentId'
                    )
                    == componentId
                    and ue.EditorAssetLibrary.get_metadata_tag(
                        asset, 'ftrack.AssetVersionId'
                    )
                    == versionId
                ):
                    ue.EditorAssetLibrary.delete_asset(asset.get_path_name())

    @staticmethod
    def getImportedAssetVersion(assetName, assetType, parentTaskId):
        '''Remove the *applicationObject* from the scene'''
        # first get our asset of interest
        candidateVersion = None
        assets = (
            ue.AssetRegistryHelpers()
            .get_asset_registry()
            .get_assets_by_path('/Game', True)
        )
        for asset_data in assets:
            # unfortunately to access the tag values objects needs
            # to be in memory
            asset = asset_data.get_asset()
            assetInstanceName = ue.EditorAssetLibrary.get_metadata_tag(
                asset, 'ftrack.AssetName'
            )
            assetInstanceType = ue.EditorAssetLibrary.get_metadata_tag(
                asset, 'ftrack.AssetType'
            )
            if (
                assetName == assetInstanceName
                and assetType == assetInstanceType
            ):
                currentVersion = ftrack.AssetVersion(
                    ue.EditorAssetLibrary.get_metadata_tag(
                        asset, 'ftrack.AssetVersionId'
                    )
                )
                if currentVersion.get('taskid') == parentTaskId:
                    candidateVersion = currentVersion
                    break

        return candidateVersion

    @staticmethod
    def changeVersion(applicationObject=None, iAObj=None):
        '''Change version of *iAObj* for the given *applicationObject*'''

        assetHandler = FTAssetHandlerInstance.instance()
        changeAsset = assetHandler.getAssetClass(iAObj.assetType)
        if changeAsset:
            result = changeAsset.changeVersion(iAObj, applicationObject)
            return result
        else:
            logger.error('assetType not supported')
            return False

    @staticmethod
    def getSelectedObjects():
        '''Return the selected nodes'''
        pass

    @staticmethod
    def getSelectedAssets():
        '''Return the selected assets'''
        componentIds = []
        selectedAssets = ue.EditorUtilityLibrary.get_selected_assets()
        for asset in selectedAssets:
            assetComponentId = ue.EditorAssetLibrary.get_metadata_tag(
                asset, 'ftrack.AssetComponentId'
            )
            if assetComponentId != None:
                componentIds.append((assetComponentId, str(asset.get_name())))
        return componentIds

    @staticmethod
    def setNodeColor(applicationObject='', latest=True):
        '''Set the node color'''
        pass

    @staticmethod
    def publishAsset(iAObj=None):
        '''Publish the asset provided by *iAObj*'''
        masterSequence = Connector._getLoadedLevelSequence()
        if masterSequence is None:
            return [], 'no sequence available in current map to allow render'
        # ensure that the masterSequence we are operating on is saved
        ue.EditorAssetLibrary.save_loaded_asset(masterSequence)
        assetHandler = FTAssetHandlerInstance.instance()
        pubAsset = assetHandler.getAssetClass(iAObj.assetType)
        if pubAsset:
            publishedComponents, message = pubAsset.publishAsset(
                iAObj, masterSequence
            )
            return publishedComponents, message
        else:
            return [], 'assetType not supported'

    @staticmethod
    def getConnectorName():
        '''Return the connector name'''
        return 'unreal'

    @staticmethod
    def getUniqueSceneName(assetName):
        '''Return a unique scene name for the given *assetName*'''
        pass

    @staticmethod
    def getReferenceNode(assetLink):
        '''Return the references nodes for the given *assetLink*'''
        pass

    @staticmethod
    def takeScreenshot():
        '''Take a screenshot and save it in the temp folder'''
        pass

    @classmethod
    def registerAssets(cls):
        '''Register all the available assets'''
        import ftrack_connect_unreal_engine.connector.unrealassets

        ftrack_connect_unreal_engine.connector.unrealassets.registerAssetTypes()
        super(Connector, cls).registerAssets()
