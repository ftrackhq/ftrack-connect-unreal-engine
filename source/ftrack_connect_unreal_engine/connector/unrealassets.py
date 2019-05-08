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

import unreal as ue


class GenericAsset(FTAssetType):
    def __init__(self):
        super(GenericAsset, self).__init__()
        self.importAssetBool = False
        self.referenceAssetBool = False

    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''

        task = ue.AssetImportTask()
        task.options = ue.FbxImportUI()
        task.options.import_mesh = iAObj.options['ImportMesh']
        task.options.import_materials = iAObj.options['ImportMaterial']
        task.options.import_animations = False
        task.options.import_animations = False

        fbx_path = iAObj.filePath
        import_path = '/Game/' + iAObj.options['ImportFolder']

        task.filename = fbx_path
        task.destination_path = import_path
        task.replace_existing = True
        task.automated = True
        #save the file when it is imported, that's right!
        task.save = True

        imported_asset = ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        #let's check what files were imported/created:
        imported_skelmesh = task.imported_object_paths

        self.name_import = import_path + '/' + imported_asset.asset_name + '.' + imported_asset.asset_name

        try:
            self.addMetaData(iAObj)
        except Exception as error:
            print(error)

        return 'Imported ' + iAObj.assetType + ' asset'
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
            print(error)

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



    def addMetaData(self, iAObj, name, path, linked_obj):
        '''Add meta data to object'''
        if linked_obj:
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetVersion", iAObj.assetVersion)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetPath", iAObj.filePath)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetTake", iAObj.componentName)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetType", iAObj.assetType)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetComponentId", iAObj.componentId)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetVersionId", iAObj.assetVersionId)
            ue.EditorAssetLibrary.save_loaded_asset(linked_obj)

    def _rename_object_with_prefix(self, loaded_obj, prefix):
        '''This method allow renaming a UObject to put a prefix to work along with UE4 naming convention
            https://github.com/Allar/ue4-style-guide'''
        assert(loaded_obj != None)
        if loaded_obj:        
            object_ad = ue.EditorAssetLibrary.find_asset_data(loaded_obj.get_path_name())
            if object_ad:
                ue.EditorAssetLibrary.rename_asset(object_ad.object_path, str(object_ad.package_path) + '/' + prefix +'_'  + str(object_ad.asset_name))


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
        
        # import settings
        task = ue.AssetImportTask()
        task.options = ue.FbxImportUI()
        task.options.import_as_skeletal = True
        task.options.import_materials = False
        task.options.import_animations = False
        task.options.create_physics_asset = True
        task.options.mesh_type_to_import = ue.FBXImportType.FBXIT_SKELETAL_MESH
        task.options.skeletal_mesh_import_data = ue.FbxSkeletalMeshImportData()
        task.options.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose',True)
        task.options.skeletal_mesh_import_data.normal_import_method = ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        task.options.skeletal_mesh_import_data.set_editor_property('import_morph_targets',True)
        task.options.skeletal_mesh_import_data.set_editor_property('import_meshes_in_bone_hierarchy', True)
        
        fbx_path = iAObj.filePath

        ftrack_asset_version = ftrack.AssetVersion(iAObj.assetVersionId)

        ftrack_asset_build = ftrack_asset_version.getParent().getParent()
        char_name = ftrack_asset_build.get('name')
        char_name = upperFirst(char_name)

        # import rig path in UE
        ftrack_node_name='RIG_'+char_name+'_AST_ftrackNode'
        import_path = '/Game/Assets/Actor/' + char_name

        task.filename = fbx_path
        task.destination_path = import_path
        task.replace_existing = True
        task.automated = True
        #save the file when it is imported, that's right!
        #task.save = True

        # find out if ftrack node already exists in th project
        ftrack_old_node=None

        try:
            ftrack_old_node=ue.get_asset(import_path + '/' + ftrack_node_name + '.' + ftrack_node_name)
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
            ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

            self.name_import = task.imported_object_paths[0]
            loaded_skeletal_mesh = ue.EditorAssetLibrary.load_asset(task.imported_object_paths[0])
            self._rename_object_with_prefix(loaded_skeletal_mesh, 'SK')

            mesh_skeleton = loaded_skeletal_mesh.skeleton
            if mesh_skeleton:
                 self._rename_object_with_prefix(mesh_skeleton, 'SKEL')

            mesh_physics_asset = loaded_skeletal_mesh.physics_asset
            if mesh_physics_asset:
                 self._rename_object_with_prefix(mesh_physics_asset, 'PHAT')

            #add meta data
            try:
                self.addMetaData(iAObj,ftrack_node_name,import_path, loaded_skeletal_mesh)
                self.addMetaData(iAObj,ftrack_node_name,import_path, mesh_skeleton)
                self.addMetaData(iAObj,ftrack_node_name,import_path, mesh_physics_asset)
            except Exception as error:
                print(error)

            return 'Imported ' + iAObj.assetType + ' asset'


    def addMetaData(self, iAObj, name, path, linked_obj):
        '''Create ftrack metadata on the imported asset'''
        if linked_obj:
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetVersion", iAObj.assetVersion)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetPath", iAObj.filePath)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetTake", iAObj.componentName)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetType", iAObj.assetType)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetComponentId", iAObj.componentId)
            ue.EditorAssetLibrary.set_metadata_tag(linked_obj, "FTrack.AssetVersionId", iAObj.assetVersionId)
            ue.EditorAssetLibrary.save_loaded_asset(linked_obj)


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

        assetRegistry = ue.AssetRegistryHelpers.get_asset_registry()
        skeletons = assetRegistry.get_assets_by_class('Skeleton')
        skeletonName = iAObj.options['ChooseSkeleton']

        skeletonAD = None        
        for skeleton in skeletons:
            if skeleton.asset_name == skeletonName:  skeletonAD = skeleton

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
                print(error)

        #seq_name_short = seq_name.split('_')[0]
        seq_name_short = seq_name.replace('Episode','EP')
        seq_name_short = seq_name_short.replace('DreamSequence', 'DS')

        ftrack_node_name = 'ANIM_' + task_name +'_'+ seq_name_short+ '_'+shot_name + '_SHT_ftrackNode'

        import_path = '/Game/Animation/' + seq_name + '/' + shot_name
        if shot_name == 'shot_name' and seq_name == 'seq_name':
            ftrack_task_context = ftrack_asset_version.getParent().getParent()
            task_context = ftrack_task_context.get('name')
            import_path = '/Game/Assets/Animation/' + str(task_context)
        elif seq_name == 'seq_name':
            import_path = '/Game/Animation/' + shot_name

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
            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_as_skeletal = False
            task.options.import_materials = False
            task.options.import_mesh = False
            task.options.import_animations = True
            task.options.create_physics_asset = False
            task.options.automated_import_should_detect_type = False
            task.options.set_editor_property('skeleton',skeletonAD.get_asset())
            task.options.set_editor_property('mesh_type_to_import', ue.FBXImportType.FBXIT_ANIMATION)
            task.options.anim_sequence_import_data = ue.FbxAnimSequenceImportData()
            task.options.anim_sequence_import_data.set_editor_property('import_bone_tracks',True)
            task.options.anim_sequence_import_data.set_editor_property('import_custom_attribute',True)

            task.filename = fbx_path
            task.destination_path = import_path
            task.replace_existing = False
            task.automated = True
            ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            self.name_import = task.imported_object_paths[0]
            loaded_anim = ue.EditorAssetLibrary.load_asset(task.imported_object_paths[0])
            self._rename_object_with_prefix(loaded_anim,'A')

            # Add ftrack data to object
            try:
                self.addMetaData(iAObj,ftrack_node_name,import_path,loaded_anim)
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
        assetRegistry = ue.AssetRegistryHelpers.get_asset_registry()
        skeletons = assetRegistry.get_assets_by_class('Skeleton')
        skeletonsInTheScene = ""
        for skeleton in skeletons:
            str= '''<optionitem name="{0}"/>'''.format(skeleton.asset_name)
            skeletonsInTheScene += str

        xml = xml.format(skeletonsInTheScene)
        return xml


class GeometryAsset(GenericAsset):
    def __init__(self):
        super(GeometryAsset, self).__init__()

    def importAsset(self, iAObj=None):
        '''Import rig asset defined in *iAObj*'''
        task = ue.AssetImportTask()
        task.options = ue.FbxImportUI()        
        task.options.import_materials = False
        task.options.import_animations = False
        task.options.override_full_name = True
        task.options.skeletal_mesh_import_data.normal_import_method = ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS

        fbx_path = iAObj.filePath

        ftrack_asset_version = ftrack.AssetVersion(iAObj.assetVersionId)

        ftrack_asset_build = ftrack_asset_version.getParent().getParent()
        geo_name = ftrack_asset_build.get('name')
        geo_name = upperFirst(geo_name)

        import_path = '/Game/Assets/Geo/' + geo_name

        task.filename = fbx_path
        task.destination_path = import_path
        task.replace_existing = True
        task.automated = True
        #save the file when it is imported, that's right!
        task.save = True

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
            ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            self.name_import = task.imported_object_paths[0]
            loaded_mesh = ue.EditorAssetLibrary.load_asset(task.imported_object_paths[0])
            self._rename_object_with_prefix(loaded_mesh, 'S')

            # add meta data
            try:
                self.addMetaData(iAObj, ftrack_node_name, import_path, loaded_mesh)
            except Exception as error:
                print(error)

        return 'Imported ' + iAObj.assetType + ' asset'



def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name="rig", cls=RigAsset)
    assetHandler.registerAssetType(name="anim", cls=AnimationAsset)
    assetHandler.registerAssetType(name="geo", cls=GeometryAsset)


def upperFirst(x):
    return x[0].upper() + x[1:]