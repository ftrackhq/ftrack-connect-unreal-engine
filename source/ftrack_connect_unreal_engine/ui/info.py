# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from QtExt import QtGui, QtCore, QtWidgets

from ftrack_connector_legacy.ui.widget.info import FtrackInfoDialog
from ftrack_connector_legacy.ui.theme import applyTheme


class FtrackUnrealInfoDialog(FtrackInfoDialog):
    def __init__(self, parent=None, connector=None):
        super(FtrackUnrealInfoDialog, self).__init__(
            parent=parent, connector=connector
        )

        self.headerWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        applyTheme(self, 'integration')

    def keyPressEvent(self, e):
        '''Handle Esc key press event'''
        if not e.key() == QtCore.Qt.Key_Escape:
            super(FtrackUnrealInfoDialog, self).keyPressEvent(e)
