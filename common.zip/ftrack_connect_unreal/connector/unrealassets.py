# :coding: utf-8
# :copyright: Copyright (c) 2018 Pinta Studios

import os
import copy

import ftrack
import ftrack_api

from PySide.QtGui import QMessageBox

import unrealcon
#from ftrackUnrealPlugin import ftrackAssetNode

from ftrack_connect.connector import (
    FTAssetHandlerInstance,
    HelpFunctions,
    FTAssetType,
    FTComponent
)

import unreal_engine as ue


class GenericAsset(FTAssetType):
    def __init__(self):
        super(GenericAsset, self).__init__()
        self.importAssetBool = False
        self.referenceAssetBool = False

    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''
        from unreal_engine.classes import PyFbxFactory

        fbx_factory = PyFbxFactory()
        fbx_factory.ImportUI.bImportMesh = iAObj.options['ImportMesh']
        fbx_factory.ImportUI.bImportMaterials = iAObj.options['ImportMaterial']
        fbx_factory.ImportUI.bImportAnimations = False
        fbx_factory.ImportUI.bCreatePhysicsAsset = False

        fbx_path = iAObj.filePath
        import_path = '/Game/' + iAObj.options['ImportFolder']

        uobject_import = fbx_factory.factory_import_object(fbx_path, import_path)

        self.name_import = import_path + '/' + uobject_import.get_name() + '.' + uobject_import.get_name()

        try:
            self.linkToFtrackNode(iAObj)
        except Exception as error:
            print error

        # return 'Imported ' + iAObj.assetType + ' asset'

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''
        pass

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        ftNode = ue.find_object(applicationObject)
        obj = ue.get_asset(ftNode.assetLink.split(',')[0])

        fbx_path = iAObj.filePath.decode('utf-8')

        obj.asset_import_data_set_sources(fbx_path)
        obj.asset_reimport()

        # save package here can cause problem in UE so I comment it here. 
        #obj.save_package()

        try:
            self.updateftrackNode(ftNode, iAObj, applicationObject)
        except Exception as error:
            print error

        return True

    def updateftrackNode(self, ftNode, iAObj, applicationObject):
        '''Update informations in *ftrackNode* with the provided *iAObj*. '''

        ftNode.assetVersion = int(iAObj.assetVersion)
        ftNode.assetPath = iAObj.filePath
        ftNode.assetTake = iAObj.componentName
        ftNode.assetType = iAObj.assetType
        ftNode.assetComponentId = iAObj.componentId
        ftNode.assetId = iAObj.assetVersionId

        ftNode.save_package()



    def linkToFtrackNode(self, iAObj, name, path, linked_obj):

        '''In the ftrack data table, add a new row with all information'''

        data_class = ue.get_asset('/Game/Data/ftrackNodeStruct.ftrackNodeStruct')

        linked_obj_path = linked_obj.get_path_name()

        ftNode = data_class.GeneratedClass(name)
        ftNode.assetVersion = int(iAObj.assetVersion)
        ftNode.assetPath = iAObj.filePath
        ftNode.assetTake = iAObj.componentName
        ftNode.assetType = iAObj.assetType
        ftNode.assetComponentId = iAObj.componentId
        ftNode.assetId = iAObj.assetVersionId
        ftNode.assetLink = linked_obj_path

        ftNode.save_package(path + '/' + name)

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = '''
        <tab name="Options">
            
        </tab>
        '''
        return xml


class RigAsset(GenericAsset):
    def __init__(self):
        super(RigAsset, self).__init__()


    def importAsset(self, iAObj=None):
        '''Import rig asset defined in *iAObj*'''
        from unreal_engine.classes import PyFbxFactory
        from unreal_engine.enums import EFBXImportType

        fbx_factory = PyFbxFactory()

        # import settings
        fbx_factory.ImportUI.bImportAsSkeletal =True
        fbx_factory.ImportUI.bImportMaterials =False
        fbx_factory.ImportUI.bImportAnimations = False
        fbx_factory.ImportUI.bCreatePhysicsAsset = True
        fbx_factory.ImportUI.MeshTypeToImport = EFBXImportType.FBXIT_SkeletalMesh
        fbx_factory.ImportUI.SkeletalMeshImportData.bUseT0AsRefPose = True
        fbx_factory.ImportUI.SkeletalMeshImportData.NormalImportMethod = 2
        fbx_factory.ImportUI.SkeletalMeshImportData.bImportMorphTargets = True
        fbx_factory.ImportUI.SkeletalMeshImportData.bImportMeshesInBoneHierarchy = True
        fbx_path = iAObj.filePath

        ftrack_asset_version = ftrack.AssetVersion(iAObj.assetVersionId)

        ftrack_asset_build = ftrack_asset_version.getParent().getParent()
        char_name = ftrack_asset_build.get('name')
        char_name = upperFirst(char_name)

        # import rig path in UE
        ftrack_node_name='RIG_'+char_name+'_AST_ftrackNode'
        import_path = '/Game/Asset/Actor/' + char_name

        # find out if ftrack node already exists in th project
        ftrack_old_node=None

        try:
            ftrack_old_node=ue.get_asset(import_path+'/'+ftrack_node_name+'.'+ftrack_node_name)
        except Exception as error:
            print error

        if ftrack_old_node!=None:
            msgBox=QMessageBox()
            msgBox.setText('This asset already exists in the project!')
            msgBox.setInformativeText("Do you want to reimport this asset?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No )
            msgBox.setDefaultButton(QMessageBox.No)
            ret = msgBox.exec_()

            if ret==QMessageBox.Yes:
                print('Yes pressed')
                #Delete old asset
                self.changeVersion(iAObj,ftrack_node_name)


            elif ret == QMessageBox.No:
                print('No pressed')


        else:

            uobject_import = fbx_factory.factory_import_object(fbx_path, import_path)

            skeleton_import=uobject_import.skeleton

            uobject_import_name= uobject_import.get_path_name()
            skeleton_import_name = skeleton_import.get_path_name()

            uobject_package_name= ue.get_path(uobject_import_name)+'/SK_'+char_name
            skeleton_package_name = ue.get_path(skeleton_import_name)+'/SKEL_'+char_name

            #rename assets
            ue.rename_asset(uobject_import_name, uobject_package_name)
            ue.rename_asset(skeleton_import_name, skeleton_package_name)

            uobject_import.save_package()
            skeleton_import.save_package()


            physics_import=None
            try:
                physics_import = uobject_import.physicsasset
            except Exception as error:
                print error

            if  physics_import!=None:
                physics_import_name = physics_import.get_path_name()
                physics_package_name = ue.get_path(physics_import_name) + '/PHAT_' + char_name
                ue.rename_asset(physics_import_name, physics_package_name)
                physics_import.PreviewSkeletalMesh = uobject_import
                physics_import.save_package()

            else:
                print('No physics asset for this asset!')


            #generate ftrack node
            try:
                self.linkToFtrackNode(iAObj,ftrack_node_name,import_path, uobject_import,skeleton_import,physics_import)
            except Exception as error:
                print error


            return 'Imported ' + iAObj.assetType + ' asset'



    def linkToFtrackNode(self, iAObj, name, path, sm_obj, sk_obj, phy_obj):
        '''Create ftrackNode and populate the connection with the imported asset'''

        data_class = ue.get_asset('/Game/Data/ftrackNodeStruct.ftrackNodeStruct')

        linked_obj_path = sm_obj.get_path_name() + ',' + sk_obj.get_path_name() + ',' + phy_obj.get_path_name()

        ftNode = data_class.GeneratedClass(name)
        ftNode.assetVersion = int(iAObj.assetVersion)
        ftNode.assetPath = iAObj.filePath
        ftNode.assetTake = iAObj.componentName
        ftNode.assetType = iAObj.assetType
        ftNode.assetComponentId = iAObj.componentId
        ftNode.assetId = iAObj.assetVersionId
        ftNode.assetLink = linked_obj_path
        ftNode.save_package(path + '/' + name)


    @staticmethod
    def importOptions():
        '''Return rig fbx import options for the component'''

        xml = '''
        <tab name="Options">   
            

        </tab>
        '''
        return xml


class AnimationAsset(GenericAsset):
    def __init__(self):
        super(AnimationAsset, self).__init__()


    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''

        from unreal_engine.classes import PyFbxFactory, Skeleton, AlembicImportFactory, AnimSequence
        from unreal_engine.enums import EFBXImportType, EAlembicImportType
        from unreal_engine.classes import Material
        from unreal_engine.structs import SkeletalMaterial, MeshUVChannelInfo

        skeletons = ue.get_assets_by_class('Skeleton')
        skeletonName = iAObj.options['ChooseSkeleton']

        skeletonUobject = None
        for skeleton in skeletons:
            if skeleton.get_name() == skeletonName:  skeletonUobject = skeleton


        fbx_path = iAObj.filePath

        ftrack_asset_version = ftrack.AssetVersion(iAObj.assetVersionId)

        task_name = ftrack_asset_version.getTask().get('name')
        parents = ftrack_asset_version.getParents()
        shot_name = 'shot_name'
        seq_name = 'seq_name'


        for item in parents:
            try:
                if item.get('objecttypename') == 'Shot':
                    shot_name = item.get('name')
                if item.get('objecttypename') == 'Episode':
                    seq_name = item.get('name')
                if item.get('objecttypename') == 'Sequence':
                    seq_name = item.get('name')
                    break

            except Exception as error:
                print error

        #seq_name_short = seq_name.split('_')[0]
        seq_name_short = seq_name.replace('Episode','EP')
        seq_name_short = seq_name_short.replace('DreamSequence', 'DS')

        ftrack_node_name = 'ANIM_' + task_name +'_'+ seq_name_short+ '_'+shot_name + '_SHT_ftrackNode'

        import_path = '/Game/Animation/' + seq_name + '/' + shot_name
        import_path = import_path + '/' + task_name

        ftrack_old_node=None

        try:
            ftrack_old_node=ue.get_asset(import_path+'/'+ftrack_node_name+'.'+ftrack_node_name)
        except Exception as error:
            print error

        if ftrack_old_node!=None:
            msgBox = QMessageBox()
            msgBox.setText('This asset already exists in the project!')
            msgBox.setInformativeText("Do you want to reimport this asset?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)
            ret = msgBox.exec_()
        
            if ret == QMessageBox.Yes:
                print('Yes pressed')
                # Delete old asset
                self.changeVersion(iAObj, ftrack_node_name)
        
            elif ret == QMessageBox.No:
                print('No pressed')

        else:

            fbx_factory = PyFbxFactory()
            fbx_factory.ImportUI.bImportMesh = False
            fbx_factory.ImportUI.bImportAnimations = True
            fbx_factory.ImportUI.MeshTypeToImport = EFBXImportType.FBXIT_Animation
            fbx_factory.ImportUI.Skeleton = skeletonUobject
            fbx_factory.ImportUI.bImportMaterials = False
            fbx_factory.ImportUI.bImportTextures = False
            fbx_factory.ImportUI.SkeletalMeshImportData.bUseT0AsRefPose = True
            fbx_factory.ImportUI.AnimSequenceImportData.bImportBoneTracks = True

            uobject_import = fbx_factory.factory_import_object(fbx_path, import_path)


            #Rename animation asset

            uobject_import_name=uobject_import.get_path_name()

            anim_name = 'A_'+ task_name+'_'+seq_name_short+'_'+shot_name

            uobject_package_name = ue.get_path(uobject_import_name) + '/' + anim_name

            ue.rename_asset(uobject_import_name, uobject_package_name)

            uobject_import.save_package()


            # Create Ftrack Node

            try:
                self.linkToFtrackNode(iAObj,ftrack_node_name,import_path,uobject_import)
            except Exception as error:
                print error


        return 'Imported ' + iAObj.assetType + ' asset'

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Choose Skeleton" accepts="unreal">
                <option type="combo" name="ChooseSkeleton" >{0}</option>
            </row>            

        </tab>
        '''
        skeletons = ue.get_assets_by_class('Skeleton')
        skeletonsInTheScene = ""
        for skeleton in skeletons:
            str= '''<optionitem name="{0}"/>'''.format(skeleton.get_name())
            skeletonsInTheScene += str

        xml = xml.format(skeletonsInTheScene)
        return xml


class GeometryAsset(GenericAsset):
    def __init__(self):
        super(GeometryAsset, self).__init__()

    def importAsset(self, iAObj=None):
        '''Import rig asset defined in *iAObj*'''
        from unreal_engine.classes import PyFbxFactory

        fbx_factory = PyFbxFactory()
        fbx_factory.ImportUI.bImportMaterials = False
        fbx_factory.ImportUI.bImportAnimations = False
        fbx_factory.ImportUI.bOverrideFullName = True

        fbx_factory.ImportUI.SkeletalMeshImportData.NormalImportMethod = 2

        fbx_path = iAObj.filePath

        ftrack_asset_version = ftrack.AssetVersion(iAObj.assetVersionId)

        ftrack_asset_build = ftrack_asset_version.getParent().getParent()
        geo_name = ftrack_asset_build.get('name')
        geo_name = upperFirst(geo_name)

        import_path = '/Game/Asset/Geo/' + geo_name

        ftrack_node_name = 'GEO_' + geo_name + '_AST_ftrackNode'

        ftrack_old_node = None

        try:
            ftrack_old_node = ue.get_asset(import_path + '/' + ftrack_node_name + '.' + ftrack_node_name)
        except Exception as error:
            print error

        if ftrack_old_node != None:
            msgBox = QMessageBox()
            msgBox.setText('This asset already exists in the project!')
            msgBox.setInformativeText("Do you want to reimport this asset?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)
            ret = msgBox.exec_()

            if ret == QMessageBox.Yes:
                print('Yes pressed')
                # Delete old asset
                self.changeVersion(iAObj, ftrack_node_name)


            elif ret == QMessageBox.No:
                print('No pressed')


        else:

            uobject_import = fbx_factory.factory_import_object(fbx_path, import_path)

            uobject_import_name=uobject_import.get_path_name()

            anim_name = 'S_' + geo_name
            uobject_package_name = ue.get_path(uobject_import_name) + '/' + anim_name

            ue.rename_asset(uobject_import_name, uobject_package_name)

            uobject_import.save_package()


            # generate ftrack node
            try:
                self.linkToFtrackNode(iAObj, ftrack_node_name, import_path, uobject_import)
            except Exception as error:
                print error

        return 'Imported ' + iAObj.assetType + ' asset'



def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name="rig", cls=RigAsset)
    assetHandler.registerAssetType(name="anim", cls=AnimationAsset)
    assetHandler.registerAssetType(name="geo", cls=GeometryAsset)



def upperFirst(x):
    return x[0].upper() + x[1:]