# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys

from QtExt import QtCore, QtWidgets

from ftrack_connect.ui.widget.asset_manager import (
    FtrackAssetManagerDialog,
    AssetManagerWidget,
)
from ftrack_connect.ui.theme import applyTheme


class FtrackUnrealAssetManagerWidget(AssetManagerWidget):
    def __init__(self, parent, connector=None):
        super(FtrackUnrealAssetManagerWidget, self).__init__(
            parent=parent, connector=connector
        )

    def getSceneSelection(self):
        '''Get selection from scene. It was necessary to override because in UE4
            a ftrack rig asset corresponds to multiple objects.
        '''
        selectedAssets = self.connector.getSelectedAssets()
        self.ui.AssertManagerTableWidget.selectionModel().clearSelection()
        for asset, assetSceneName in selectedAssets:
            foundItems = self.ui.AssertManagerTableWidget.findItems(
                asset, QtCore.Qt.MatchExactly
            )
            indices = []
            for item in foundItems:
                index = self.ui.AssertManagerTableWidget.indexFromItem(item)

                nameItem = self.ui.AssertManagerTableWidget.itemFromIndex(
                    index.sibling(index.row(), 8)
                )
                if nameItem and nameItem.text() == assetSceneName:
                    indices.append(index)

            selModel = self.ui.AssertManagerTableWidget.selectionModel()
            for index in indices:
                selModel.select(
                    index,
                    QtCore.QItemSelectionModel.Select
                    | QtCore.QItemSelectionModel.Rows,
                )


class FtrackUnrealAssetManagerDialog(FtrackAssetManagerDialog):
    def __init__(self, parent=None, connector=None):
        super(FtrackUnrealAssetManagerDialog, self).__init__(
            parent=parent, connector=connector
        )

        # remove the provided AssetManagerWidget to replace it by our own.
        wi = self.horizontalLayout.takeAt(0)
        self.assetManagerWidget.setParent(None)
        self.assetManagerWidget = None
        wi.widget().deleteLater()
        self.assetManagerWidget = FtrackUnrealAssetManagerWidget(
            parent=self.centralwidget, connector=self.connector
        )
        self.horizontalLayout.addWidget(self.assetManagerWidget)

        self.headerWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        applyTheme(self, 'integration')

    def keyPressEvent(self, e):
        '''Handle Esc key press event'''
        if not e.key() == QtCore.Qt.Key_Escape:
            super(FtrackUnrealAssetManagerDialog, self).keyPressEvent(e)
