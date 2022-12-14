# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import logging
import getpass
import unreal as ue

from QtExt import QtWidgets, QtCore, QtGui

import ftrack
import ftrack_api
from ftrack_api import event
from ftrack_connector_legacy import connector as ftrack_connector
from ftrack_connector_legacy.ui.widget import header
from ftrack_connector_legacy.ui.theme import applyTheme
from ftrack_connector_legacy.ui.widget.context_selector import ContextSelector
from ftrack_connect_unreal_engine.ui.export_asset_options_widget import (
    ExportAssetOptionsWidget,
)
from ftrack_connect_unreal_engine.ui.export_options_widget import (
    ExportOptionsWidget,
)
from ftrack_connect_unreal_engine.connector.unrealcon import Connector


class FtrackPublishDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, connector=None):
        if not connector:
            raise ValueError(
                'Please provide a connector object for {0}'.format(
                    self.__class__.__name__
                )
            )
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.connector = connector
        if not parent:
            self.parent = self.connector.getMainWindow()

        self.currentEntity = Connector.getCurrentEntity()

        super(FtrackPublishDialog, self).__init__(self.parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )
        )
        applyTheme(self, 'integration')

        self.assetType = None
        self.assetName = None
        self.status = None

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.mainWidget = QtWidgets.QWidget(self)
        self.scrollLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.scrollLayout.setSpacing(6)

        self.scrollArea = QtWidgets.QScrollArea(self)
        self.mainLayout.addWidget(self.scrollArea)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.scrollArea.setWidget(self.mainWidget)

        self.headerWidget = header.Header(getpass.getuser(), self)
        self.scrollLayout.addWidget(self.headerWidget)

        if 'FTRACK_TASKID' in os.environ:
            self.browseMode = 'Task'
        else:
            self.browseMode = 'Shot'

        self.browseTasksWidget = ContextSelector(
            currentEntity=self.currentEntity, parent=self
        )

        self.scrollLayout.addWidget(self.browseTasksWidget)

        self.exportAssetOptionsWidget = ExportAssetOptionsWidget(
            self, browseMode=self.browseMode
        )

        self.scrollLayout.addWidget(self.exportAssetOptionsWidget)

        self.exportOptionsWidget = ExportOptionsWidget(
            self, connector=self.connector
        )

        self.scrollLayout.addWidget(self.exportOptionsWidget)

        spacerItem = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.scrollLayout.addItem(spacerItem)

        self.setObjectName('ftrackPublishAsset')
        self.setWindowTitle("ftrackPublishAsset")
        panelComInstance = ftrack_connector.panelcom.PanelComInstance.instance()
        panelComInstance.addSwitchedShotListener(self.reset_context_browser)
        panelComInstance.addSwitchedShotListener(self.resetOptions)

        self.exportAssetOptionsWidget.clickedAssetTypeSignal.connect(
            self.exportOptionsWidget.setStackedWidget
        )

        self.browseTasksWidget.entityChanged.connect(
            self.exportAssetOptionsWidget.updateView
        )

        self.exportOptionsWidget.ui.publishButton.clicked.connect(
            self.publishAsset
        )

        panelComInstance.publishProgressSignal.connect(
            self.exportOptionsWidget.setProgress
        )

        self.browseTasksWidget.reset()

    def reset_context_browser(self):
        '''Reset task browser to the value stored in the environments'''
        entity_id = os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
        entity = ftrack.Task(entity_id)
        self.browseTasksWidget.reset(entity)
        self.currentEntity = entity

    def resetOptions(self):
        '''Reset options'''
        self.exportOptionsWidget.resetOptions()
        self.exportAssetOptionsWidget.setAssetType(self.assetType)
        self.exportAssetOptionsWidget.setAssetName(self.assetName)
        self.exportOptionsWidget.setComment('')

        self.exportAssetOptionsWidget.updateTasks(self.currentEntity)
        self.exportAssetOptionsWidget.updateView(self.currentEntity)

    def setAssetType(self, assetType):
        '''Set to the provided *assetType*'''
        self.exportAssetOptionsWidget.setAssetType(assetType)
        self.assetType = assetType

    def setAssetName(self, assetName):
        '''Set to the provided *assetName*'''
        self.exportAssetOptionsWidget.setAssetName(assetName)
        self.assetName = assetName

    def setComment(self, comment):
        '''Set the provided *comment*'''
        self.exportOptionsWidget.setComment(comment)

    def publishAsset(self):
        '''Publish the asset'''
        task = self.exportAssetOptionsWidget.getTask()
        taskId = task.getId()
        shot = self.exportAssetOptionsWidget.getShot()

        assetType = self.exportAssetOptionsWidget.getAssetType()
        assetName = self.exportAssetOptionsWidget.getAssetName()
        status = self.exportAssetOptionsWidget.getStatus()

        comment = self.exportOptionsWidget.getComment()
        options = self.exportOptionsWidget.getOptions()

        if assetName == '':
            self.showWarning('Missing assetName', 'assetName can not be blank')
            return

        # check that the current map has been saved
        current_map_package = ue.EditorLevelLibrary.get_editor_world().get_outermost()

        if current_map_package in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages():
            self.logger.warning('Please save the following map to publish: {0}'.format(
                current_map_package.get_path_name())
            )
            self.showWarning('Unsaved Map', 'Map must be saved before publishing')
            return

        prePubObj = ftrack_connector.FTAssetObject(
            options=options, taskId=taskId
        )

        result, message = self.connector.prePublish(prePubObj)

        if not result:
            self.showWarning('Prepublish failed', message)
            return

        self.exportOptionsWidget.setProgress(0)
        asset = shot.createAsset(assetName, assetType)

        assetVersion = asset.createVersion(comment=comment, taskid=taskId)

        #####
        # get version that is in project
        #  - given the name,type and parent task id of asset
        # Don't need to do this for image sequences as they will not have
        # sub-component that we need to propagate to new version.
        if assetType != "img":
            oldAssetVersion = Connector.getImportedAssetVersion(
                assetName, assetType, taskId
            )
            if not oldAssetVersion:
                self.showError("Publish failed: Selected asset not in project")
                return

            # copy over used versions and components
            usesVersions = list(oldAssetVersion.usesVersions())
            usesVersions.append(oldAssetVersion)
            assetVersion.addUsesVersions(usesVersions)

            oldComponents = oldAssetVersion.getComponents()
            for oldComp in oldComponents:
                compName = oldComp.getName()
                if compName == 'thumbnail' or compName == 'ftrackreview-mp4':
                    continue
                assetVersion.createComponent(
                    name=oldComp.getName(), path=oldComp.getFilesystemPath()
                )

        #####

        pubObj = ftrack_connector.FTAssetObject(
            assetVersionId=assetVersion.getId(), options=options
        )
        try:
            publishedComponents, message = self.connector.publishAsset(pubObj)
            self.exportOptionsWidget.setProgress(40)
        except:
            self.exportOptionsWidget.setProgress(100)
            self.showError('Publish failed. Please check the console.')
            raise

        if publishedComponents:
            session = ftrack_api.Session()
            for componentNumber, ftComponent in enumerate(publishedComponents):
                path = ftComponent.path
                compName = ftComponent.componentname
                location = Connector.pickLocation(copyFiles=True)
                try:
                    # TODO: find a better way to check if this is a reviewable
                    if "reviewable" in compName:
                        ftrack.Review.makeReviewable(assetVersion, path)
                    else:
                        assetVersion.createComponent(name=compName, path=path)
                    assetVersion.publish()
                except Exception as error:
                    self.logger.error(str(error))
            self.exportOptionsWidget.setProgress(90)
        else:
            self.exportOptionsWidget.setProgress(100)

        # Update status of task.
        ftTask = ftrack.Task(id=taskId)
        if (
            ftTask
            and ftTask.get('object_typeid')
            == '11c137c0-ee7e-4f9c-91c5-8c77cec22b2c'
        ):
            for taskStatus in ftrack.getTaskStatuses():
                if taskStatus.getName() == status and taskStatus.get(
                    'statusid'
                ) != ftTask.get('statusid'):
                    try:
                        ftTask.setStatus(taskStatus)
                    except Exception as error:
                        self.logger.error('{0}'.format(error))

                    break

        self.headerWidget.setMessage(message, 'info')
        self.exportOptionsWidget.setComment('')
        self.resetOptions()
        self.exportAssetOptionsWidget.emitAssetType(
            self.exportAssetOptionsWidget.ui.ListAssetsComboBox.currentIndex()
        )
        self.exportOptionsWidget.setProgress(100)

    def keyPressEvent(self, e):
        '''Handle Escape key press'''
        if not e.key() == QtCore.Qt.Key_Escape:
            super(FtrackPublishDialog, self).keyPressEvent(e)

    def getShotPath(self, shot):
        '''Return the full path to the shot'''
        shotparents = shot.getParents()
        shotpath = ''

        for parent in reversed(shotparents):
            shotpath += parent.getName() + '.'
        shotpath += shot.getName()
        return shotpath

    def showWarning(self, subject, message):
        '''Helper method for *showWarning*'''
        self.headerWidget.setMessage(message, 'warning')

    def showError(self, message):
        '''Helper method for *showError'''
        self.headerWidget.setMessage(message, 'error')
