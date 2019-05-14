# :coding: utf-8
# :copyright: Copyright (c) 2018 Pinta Studios

import sys

from QtExt import QtCore, QtWidgets

from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog
from ftrack_connect.ui.theme import applyTheme


class FtrackUnrealAssetManagerDialog(FtrackAssetManagerDialog):
    def __init__(self, parent=None, connector=None):
        print("connector " + str(connector))
        super(FtrackUnrealAssetManagerDialog, self).__init__(
            parent=parent,
            connector=connector
        )

        self.headerWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        applyTheme(self, 'integration')

    def keyPressEvent(self, e):
        '''Handle Esc key press event'''
        if not e.key() == QtCore.Qt.Key_Escape:
            super(FtrackUnrealAssetManagerDialog, self).keyPressEvent(e)
