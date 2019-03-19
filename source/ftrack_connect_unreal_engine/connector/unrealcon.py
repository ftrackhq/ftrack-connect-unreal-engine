# :coding: utf-8
# :copyright: Copyright (c) 2018 Pinta Studios

import os
import uuid

from ftrack_connect.connector import base as maincon
from ftrack_connect.connector import FTAssetHandlerInstance
import sys
import logging
import argparse
import signal

import ftrack_connect.ui.theme

import unreal_engine as ue


class Connector(maincon.Connector):
    def __init__(self):
        super(Connector, self).__init__()

    @staticmethod
    def setTimeLine():
        '''Set time line to FS , FE environment values'''
        pass

    @staticmethod
    def getAssets():
        '''Return the available assets in UE project, return the *componentId(s)*'''
        allObjects = []
        #get all UserDefinedStruct Type Uobjects in ue
        userDefinedObjs = ue.get_assets_by_class('ftrackNodeStruct_C')

        #get all ftrackdata Type from the pool above
        for obj in userDefinedObjs:
            try:
                if obj.get_name().endswith('ftrackNode'): allObjects.append(obj)
            except:
                pass


        componentIds = []

        for ftrackobj in allObjects:

            assetcomponentid = ftrackobj.assetComponentId

            nameInScene = ftrackobj.get_name()

            componentIds.append((assetcomponentid, nameInScene))

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
            return result
        else:
            return 'assetType not supported'



    @staticmethod
    def selectObject(applicationObject=''):
        '''Select the *applicationObject*'''

        ftNode = ue.find_object(applicationObject)

        obj = ue.get_asset(ftNode.assetLink.split(',')[0])

        ue.sync_browser_to_assets([obj],True)



    @staticmethod
    def selectObjects(selection):
        '''Select the given *selection*'''
        pass


    @staticmethod
    def removeObject(applicationObject=''):
        '''Remove the *applicationObject* from the scene'''

        ftNode = ue.find_object(applicationObject)

        assetLinks = ftNode.assetLink.split(',')

        for asset in assetLinks:
            ue.delete_asset(asset)

        try:
            ue.delete_asset(ftNode.get_full_name().split()[1])
        except Exception as error:
            print error


    @staticmethod
    def changeVersion(applicationObject=None, iAObj=None):
        '''Change version of *iAObj* for the given *applicationObject*'''

        assetHandler = FTAssetHandlerInstance.instance()
        changeAsset = assetHandler.getAssetClass(iAObj.assetType)
        if changeAsset:
            result = changeAsset.changeVersion(iAObj, applicationObject)
            return result
        else:
            print 'assetType not supported'
            return False

    @staticmethod
    def getSelectedObjects():
        '''Return the selected nodes'''
        pass


    @staticmethod
    def getSelectedAssets():
        '''Return the selected assets'''
        pass


    @staticmethod
    def setNodeColor(applicationObject='', latest=True):
        '''Set the node color'''
        pass

    @staticmethod
    def publishAsset(iAObj=None):
        '''Publish the asset provided by *iAObj*'''
        pass

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
        import ftrack_connect_unreal.connector.unrealassets
        ftrack_connect_unreal.connector.unrealassets.registerAssetTypes()
        super(Connector, cls).registerAssets()
