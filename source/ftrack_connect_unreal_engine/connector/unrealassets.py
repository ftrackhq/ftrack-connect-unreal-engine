# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import copy
import os
import sys
import logging
import subprocess
import shutil
import tempfile
from zipfile import ZipFile

import ftrack
import ftrack_api
import unreal as ue
import unrealcon

from ftrack_connect_unreal_engine._version import __version__

from ftrack_connect.connector import (
    FTAssetHandlerInstance,
    FTAssetType,
    FTComponent,
    HelpFunctions,
)
from QtExt.QtGui import QMessageBox


class GenericAsset(FTAssetType):

    def __init__(self):
        super(GenericAsset, self).__init__()
        self.supported_extension = ['.fbx', '.abc']
        self.importAssetBool = False
        self.referenceAssetBool = False
        self._standard_structure = ftrack_api.structure.standard.StandardStructure()

    def _get_asset_import_task(self, iAObj):
        extension = os.path.splitext(iAObj.filePath)[-1]
        if extension == '.fbx':
            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_materials = False
            task.options.import_animations = False
            task.options.override_full_name = True
            task.options.skeletal_mesh_import_data.normal_import_method = (
                ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
            )

        elif extension == '.abc':
            task = ue.AssetImportTask()
            task.options = ue.AbcImportSettings()
            task.options.import_materials = False
            task.options.import_animations = False
            task.options.override_full_name = True

        task.replace_existing = True
        task.automated = True
        task.save = True
        return task

    def importAsset(self, iAObj):
        '''Import asset defined in *iAObj*'''

        if not self._validate_ftrack_asset(iAObj):
            return []

        extension = os.path.splitext(iAObj.filePath)[-1]

        if extension == '.fbx':
            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_mesh = iAObj.options['ImportMesh']
            task.options.import_materials = iAObj.options['ImportMaterial']
            task.options.import_animations = False

        elif extension == '.abc':
            task = ue.AssetImportTask()
            task.options = ue.AbcImportSettings()
            task.options.compression_settings.merge_meshes = False
            task.options.material_settings.find_materials = iAObj.options['ImportMaterial']

        fbx_path = iAObj.filePath
        import_path = '/Game/' + iAObj.options['ImportFolder']

        task.filename = fbx_path
        task.destination_path = import_path
        task.replace_existing = True
        task.automated = True
        # save the file when it is imported, that's right!
        task.save = True

        imported_asset = ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
            [task]
        )

        self.name_import = (
            import_path
            + '/'
            + imported_asset.asset_name
            + '.'
            + imported_asset.asset_name
        )
        importedAssetNames = [str(imported_asset.asset_name)]

        try:
            self.addMetaData(iAObj, imported_asset)
        except Exception as error:
            logging.error(error)

        return importedAssetNames

    def _render(
        self,
        destination_path,
        unreal_map_path,
        sequence_path,
        content_name,
        fps,
        is_image_sequence=False,
    ):
        def __generate_target_file_path(destination_path, content_name):
            # Sequencer can only render to avi file format
            output_filename = (
                "{}.avi".format(content_name)
                if not is_image_sequence
                else ("{}".format(content_name) + '.{frame}.exr')
            )
            output_filepath = os.path.join(destination_path, output_filename)
            return output_filepath

        def __build_process_args(
            destination_path,
            unreal_map_path,
            sequence_path,
            content_name,
            fps,
            is_image_sequence,
        ):
            # Render the sequence to a movie file using the following
            # command-line arguments
            cmdline_args = []

            # Note that any command-line arguments (usually paths) that could
            # contain spaces must be enclosed between quotes
            unreal_exec_path = '"{}"'.format(sys.executable)

            # Get the Unreal project to load
            unreal_project_filename = "{}.uproject".format(
                ue.SystemLibrary.get_game_name()
            )
            unreal_project_path = os.path.join(
                ue.SystemLibrary.get_project_directory(),
                unreal_project_filename,
            )
            unreal_project_path = '"{}"'.format(unreal_project_path)

            # Important to keep the order for these arguments
            cmdline_args.append(unreal_exec_path)  # Unreal executable path
            cmdline_args.append(unreal_project_path)  # Unreal project
            cmdline_args.append(
                unreal_map_path
            )  # Level to load for rendering the sequence

            # Command-line arguments for Sequencer Render to Movie
            # See: https://docs.unrealengine.com/en-us/Engine/Sequencer/Workflow/RenderingCmdLine
            sequence_path = "-LevelSequence={}".format(sequence_path)
            cmdline_args.append(sequence_path)  # The sequence to render

            output_path = '-MovieFolder="{}"'.format(destination_path)
            cmdline_args.append(
                output_path
            )  # output folder, must match the work template

            movie_name_arg = "-MovieName={}".format(content_name)
            cmdline_args.append(movie_name_arg)  # output filename

            cmdline_args.append("-game")
            cmdline_args.append(
                "-MovieSceneCaptureType=/Script/MovieSceneCapture.AutomatedLevelSequenceCapture"
            )
            cmdline_args.append("-ForceRes")
            cmdline_args.append("-Windowed")
            cmdline_args.append("-MovieCinematicMode=yes")
            if is_image_sequence:
                cmdline_args.append("-MovieFormat=EXR")
            else:
                cmdline_args.append("-MovieFormat=Video")
            cmdline_args.append("-MovieFrameRate=" + str(fps))
            ftrack_capture_args = (
                ue.FTrackConnect.get_instance().get_capture_arguments()
            )
            cmdline_args.append(ftrack_capture_args)
            cmdline_args.append("-NoTextureStreaming")
            cmdline_args.append("-NoLoadingScreen")
            cmdline_args.append("-NoScreenMessages")
            return cmdline_args

        output_filepath = __generate_target_file_path(
            destination_path, content_name
        )
        if os.path.isfile(output_filepath):
            # Must delete it first, otherwise the Sequencer will add a number
            # in the filename
            try:
                os.remove(output_filepath)
            except OSError as e:
                logging.warning(
                    "Couldn't delete {}. The Sequencer won't be able to output the movie to that file.".format(
                        output_filepath
                    )
                )
                return False, None

        # Unreal will be started in game mode to render the video
        cmdline_args = __build_process_args(
            destination_path,
            unreal_map_path,
            sequence_path,
            content_name,
            fps,
            is_image_sequence,
        )

        logging.info(
            "Sequencer command-line arguments: {}".format(cmdline_args)
        )

        # Send the arguments as a single string because some arguments could
        # contain spaces and we don't want those to be quoted
        subprocess.call(" ".join(cmdline_args))

        return os.path.isfile(output_filepath), output_filepath

    def _package_current_scene(
        self,
        destination_path,
        unreal_map_package_path,
        content_name
    ):
        # format package folder name
        output_filepath = os.path.normpath(
            os.path.join(destination_path, content_name)
        )

        # use integration-specific logger
        logger = logging.getLogger("ftrack_connect_unreal_engine")

        # zip up folder
        output_zippath = (
            "{}.zip".format(output_filepath)
        )
        if os.path.isfile(output_zippath):
            # must delete it first,
            try:
                os.remove(output_zippath)
            except OSError as e:
                logger.warning(
                    "Couldn't delete {}. The package process won't be able to output to that file.".format(
                        output_zippath
                    )
                )
                return False, None

        # process migration of current scene
        logger.info(
            "Migrate package {0} to folder: {1}".format(
                unreal_map_package_path, output_zippath)
        )

        # create (temporary) destination folder
        try:
            # TODO: Use a context manager like tempfile.TemporaryDirectory() to safely create
            # and cleanup temp folders and files once Unreal provides support for Python 3.2+
            tempdir_filepath = tempfile.mkdtemp(dir = destination_path)
        except OSError:
            logger.warning(
                "Couldn't create {}. The package won't be able to output to that folder.".format(
                    destination_path
                )
            )
            return False, None

        # perform migration
        unreal_windows_logs_dir = os.path.join(
            ue.SystemLibrary.get_project_saved_directory(), "Logs"
        )
        logger.info("Detailed logs of editor ouput during migration found at: {0}".format(unreal_windows_logs_dir))
        
        ue.FTrackConnect.get_instance().migrate_packages(unreal_map_package_path, tempdir_filepath)

        # create a ZipFile object
        with ZipFile(output_zippath, 'w') as zipObj:
            # iterate over all the files in directory
            for folderName, subfolders, filenames in os.walk(tempdir_filepath):
                for filename in filenames:
                    # create complete and relative filepath of file in directory
                    filePath = os.path.join(folderName, filename)
                    truncated_path = os.path.relpath(filePath, tempdir_filepath)
                    # Add file to zip
                    zipObj.write(filePath, truncated_path)

        # remove temporary folder
        if os.path.isdir(tempdir_filepath):
            try:
                shutil.rmtree(tempdir_filepath)
            except OSError as e:
                logger.warning(
                    "Couldn't delete {}. The package process cannot cleanup temporary package folder.".format(
                        tempdir_filepath
                    )
                )
                return False, None

        return os.path.isfile(output_zippath), output_zippath

    def publishAsset(self, iAObj, masterSequence):
        '''Publish the asset defined by the provided *iAObj*.'''
        componentName = "reviewable_asset"
        publishedComponents = []
        dest_folder = os.path.join(
            ue.SystemLibrary.get_project_saved_directory(), 'VideoCaptures'
        )
        unreal_map = ue.EditorLevelLibrary.get_editor_world()
        unreal_map_path = unreal_map.get_path_name()
        unreal_asset_path = masterSequence.get_path_name()

        asset_name = self._standard_structure.sanitise_for_filesystem(iAObj.assetName)
        movie_name = '{}_reviewable'.format(asset_name)

        rendered, path = self._render(
            dest_folder,
            unreal_map_path,
            unreal_asset_path,
            movie_name,
            masterSequence.get_display_rate().numerator,
        )
        if rendered:
            publishedComponents.append(
                FTComponent(componentname=componentName, path=path)
            )

        return publishedComponents, 'Published ' + iAObj.assetType + ' asset'

    def _validate_ftrack_asset(self, iAObj=None):
        # use integration-specific logger
        logger = logging.getLogger("ftrack_connect_unreal_engine")
        
        # Validate the file
        if not os.path.exists(iAObj.filePath):
            error_string = 'ftrack cannot import file "{}" because it does not exist'.format(
                iAObj.filePath
            )
            logger.error(error_string)
            return False

        # Only fbx and alembic files are supported
        (_, src_filename) = os.path.split(iAObj.filePath)
        (_, src_extension) = os.path.splitext(src_filename)
        if src_extension.lower() not in self.supported_extension:
            error_string = 'ftrack in UE4 does not support importing files with extension "{0}" please use {1}'.format(
                src_extension, ', '.join(self.supported_extension)
            )
            logger.error(error_string)

            return False

        return True

    def _find_asset_instance(self, rootPath, assetVersionId, assetType):
        ftrack_asset_version = ftrack.AssetVersion(assetVersionId)
        ftrack_asset_id = ftrack_asset_version.getParent().getId()
        assets = (
            ue.AssetRegistryHelpers()
            .get_asset_registry()
            .get_assets_by_path(rootPath, True)
        )
        for asset_data in assets:
            # unfortunately to access the tag values objects needs to be
            # in memory....
            asset = asset_data.get_asset()
            assetId = ue.EditorAssetLibrary.get_metadata_tag(
                asset, 'ftrack.AssetId'
            )
            currentAssetType = ue.EditorAssetLibrary.get_metadata_tag(
                asset, 'ftrack.AssetType'
            )
            if assetId and currentAssetType:
                if assetId == ftrack_asset_id and currentAssetType == assetType:
                    return asset
        return None

    def _get_asset_relative_path(self, ftrack_asset_version):
        task = ftrack_asset_version.getTask()
        # location.
        session = ftrack_api.Session()
        linksForTask = session.query(
            'select link from Task where id is "' + task.getId() + '"'
        ).first()['link']
        relative_path = ""
        # remove the project
        linksForTask.pop(0)
        for link in linksForTask:
            relative_path += link['name'].replace(' ', '_')
            relative_path += '/'
        return relative_path

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        if not self._validate_ftrack_asset(iAObj):
            return False

        assets = (
            ue.AssetRegistryHelpers()
            .get_asset_registry()
            .get_assets_by_path('/Game', True)
        )
        for asset_data in assets:
            # unfortunately to access the tag values objects needs to be
            # in memory....
            asset = asset_data.get_asset()
            if str(asset.get_name()) == applicationObject:
                task = self._get_asset_import_task(iAObj)
                task.filename = iAObj.filePath
                task.destination_path = str(asset_data.package_path)
                task.destination_name = str(asset_data.asset_name)
                ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
                    [task]
                )
                if len(task.imported_object_paths):
                    self.updateMetaData(iAObj, asset)
                    return True

        return False

    def updateMetaData(self, iAObj, assetObj):
        '''Update informations in *ftrackNode* with the provided *iAObj*. '''
        self.addMetaData(iAObj, assetObj)

    def addMetaData(self, iAObj, linked_obj):
        '''Add meta data to object'''
        if linked_obj:
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.AssetVersion", iAObj.assetVersion
            )
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.AssetPath", iAObj.filePath
            )
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.AssetName", iAObj.assetName
            )
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.ComponentName", iAObj.componentName
            )
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.AssetType", iAObj.assetType
            )
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.AssetId", iAObj.assetId
            )
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.AssetComponentId", iAObj.componentId
            )
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.AssetVersionId", iAObj.assetVersionId
            )
            ue.EditorAssetLibrary.set_metadata_tag(
                linked_obj, "ftrack.IntegrationVersion", __version__
            )  # to be changed at cleanup
            ue.EditorAssetLibrary.save_loaded_asset(linked_obj)

    def _rename_object_with_prefix(self, loaded_obj, prefix):
        '''This method allow renaming a UObject to put a prefix to work along with UE4 naming convention
            https://github.com/Allar/ue4-style-guide'''
        assert loaded_obj != None
        newNameWithPrefix = ''
        if loaded_obj:
            object_ad = ue.EditorAssetLibrary.find_asset_data(
                loaded_obj.get_path_name()
            )
            if object_ad:
                if ue.EditorAssetLibrary.rename_asset(
                    object_ad.object_path,
                    str(object_ad.package_path)
                    + '/'
                    + prefix
                    + '_'
                    + str(object_ad.asset_name),
                ):
                    newNameWithPrefix = '{}_{}'.format(
                        prefix, object_ad.asset_name
                    )
        return newNameWithPrefix

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

    def _get_asset_import_task(self, iAObj):
        extension = os.path.splitext(iAObj.filePath)[-1]
        if extension == '.fbx':
            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_as_skeletal = True
            task.options.import_materials = False
            task.options.import_animations = False
            task.options.create_physics_asset = True
            task.options.automated_import_should_detect_type = False
            task.options.mesh_type_to_import = ue.FBXImportType.FBXIT_SKELETAL_MESH
            task.options.skeletal_mesh_import_data = ue.FbxSkeletalMeshImportData()
            task.options.skeletal_mesh_import_data.set_editor_property(
                'use_t0_as_ref_pose', True
            )
            task.options.skeletal_mesh_import_data.normal_import_method = (
                ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
            )
            task.options.skeletal_mesh_import_data.set_editor_property(
                'import_morph_targets', True
            )
            task.options.skeletal_mesh_import_data.set_editor_property(
                'import_meshes_in_bone_hierarchy', True
            )

        elif extension == '.abc':
            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_materials = False
            task.options.import_animations = False
            task.options.override_full_name = True

        task.replace_existing = True
        task.automated = True
        # task.save = True
        return task

    def importAsset(self, iAObj=None):
        '''Import rig asset defined in *iAObj*'''

        if not self._validate_ftrack_asset(iAObj):
            return []

        # import settings
        fbx_path = iAObj.filePath

        ftrack_asset_version = ftrack.AssetVersion(iAObj.assetVersionId)

        asset_name = ftrack_asset_version.getParent().get('name')
        asset_name = upperFirst(asset_name)
        import_path = (
            '/Game/'
            + self._get_asset_relative_path(ftrack_asset_version)
            + asset_name
        )

        # find out if ftrack node already exists in th project
        ftrack_old_node = None

        try:
            ftrack_old_node = self._find_asset_instance(
                import_path, iAObj.assetVersionId, iAObj.assetType
            )
        except Exception as error:
            logging.error(error)

        importedAssetNames = []
        if ftrack_old_node != None:
            msgBox = QMessageBox()
            msgBox.setText('This asset already exists in the project!')
            msgBox.setInformativeText("Do you want to reimport this asset?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)
            ret = msgBox.exec_()
            old_node_name = str(ftrack_old_node.get_name())

            if ret == QMessageBox.Yes:
                # Delete old asset
                self.changeVersion(iAObj, old_node_name)
                importedAssetNames.append(old_node_name)
                logging.info(
                    'Changed version of existing asset ' + old_node_name
                )

            elif ret == QMessageBox.No:
                logging.info(
                    'Not changing version of existing asset ' + old_node_name
                )

        else:
            task = self._get_asset_import_task(iAObj)
            task.filename = fbx_path
            task.destination_path = import_path
            task.options.create_physics_asset = iAObj.options[
                'CreatePhysicsAsset'
            ]
            skeletons = (
                ue.AssetRegistryHelpers()
                .get_asset_registry()
                .get_assets_by_class('Skeleton')
            )
            skeletonName = iAObj.options['ChooseSkeleton']

            skeletonAD = None
            for skeleton in skeletons:
                if skeleton.asset_name == skeletonName:
                    skeletonAD = skeleton

            if skeletonAD != None:
                task.options.set_editor_property(
                    'skeleton', skeletonAD.get_asset()
                )
            task.options.import_materials = iAObj.options['importMaterial']
            ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            self.name_import = task.imported_object_paths[0]
            loaded_skeletal_mesh = ue.EditorAssetLibrary.load_asset(
                task.imported_object_paths[0]
            )
            importedAssetNames.append(
                self._rename_object_with_prefix(loaded_skeletal_mesh, 'SK')
            )

            mesh_skeleton = loaded_skeletal_mesh.skeleton
            if mesh_skeleton:
                importedAssetNames.append(
                    self._rename_object_with_prefix(mesh_skeleton, 'SKEL')
                )

            mesh_physics_asset = loaded_skeletal_mesh.physics_asset
            if mesh_physics_asset:
                importedAssetNames.append(
                    self._rename_object_with_prefix(mesh_physics_asset, 'PHAT')
                )

            # add meta data
            try:
                self.addMetaData(iAObj, loaded_skeletal_mesh)
                self.addMetaData(iAObj, mesh_skeleton)
                self.addMetaData(iAObj, mesh_physics_asset)
            except Exception as error:
                logging.error(error)

            return importedAssetNames

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        if not self._validate_ftrack_asset(iAObj):
            return False
        assets = (
            ue.AssetRegistryHelpers()
            .get_asset_registry()
            .get_assets_by_path('/Game', True)
        )
        for asset_data in assets:
            # rig asset import
            if str(asset_data.get_class().get_name()) == 'SkeletalMesh':
                # unfortunately to access the tag values objects needs to
                # be in memory....
                asset = asset_data.get_asset()
                if str(asset.get_name()) == applicationObject:
                    task = self._get_asset_import_task(iAObj)
                    task.options.create_physics_asset = iAObj.options[
                        'CreatePhysicsAsset'
                    ]
                    task.options.import_materials = iAObj.options[
                        'importMaterial'
                    ]
                    task.options.set_editor_property(
                        'skeleton', asset.skeleton)
                    task.filename = iAObj.filePath
                    task.destination_path = str(asset_data.package_path)
                    task.destination_name = str(asset_data.asset_name)
                    ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
                        [task]
                    )
                    if len(task.imported_object_paths):
                        self.updateMetaData(iAObj, asset)
                        return True
        return False

    @staticmethod
    def exportOptions():
        '''Return export options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Make Reviewable" accepts="unreal" enabled="False">
                <option type="checkbox" name="MakeReviewable" value="True"/>
            </row>
        </tab>
        '''
        return xml

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Choose Skeleton" accepts="unreal">
                <option type="combo" name="ChooseSkeleton" >{0}</option>
            </row>
            <row name="Create Physics Asset" accepts="unreal">                
                <option type="checkbox" name="CreatePhysicsAsset" value="True"/>
            </row>
            <row name="Import Material" accepts="unreal">                
                <option type="checkbox" name="importMaterial" value="True"/>
            </row>
        </tab>
        '''

        assetRegistry = ue.AssetRegistryHelpers.get_asset_registry()
        skeletons = assetRegistry.get_assets_by_class('Skeleton')
        skeletonsInTheScene = '''<optionitem name="None"/>'''
        for skeleton in skeletons:
            str = '''<optionitem name="{0}"/>'''.format(skeleton.asset_name)
            skeletonsInTheScene += str

        xml = xml.format(skeletonsInTheScene)
        return xml


class AnimationAsset(GenericAsset):
    def __init__(self):
        super(AnimationAsset, self).__init__()

    def _get_asset_import_task(self, iAObj):
        extension = os.path.splitext(iAObj.filePath)[-1]
        if extension == '.fbx':

            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_as_skeletal = False
            task.options.import_materials = False
            task.options.import_mesh = False
            task.options.import_animations = True
            task.options.create_physics_asset = False
            task.options.automated_import_should_detect_type = False
            task.options.set_editor_property(
                'mesh_type_to_import', ue.FBXImportType.FBXIT_ANIMATION
            )
            task.options.anim_sequence_import_data = ue.FbxAnimSequenceImportData()
            task.options.anim_sequence_import_data.set_editor_property(
                'import_bone_tracks', True
            )
            task.options.anim_sequence_import_data.set_editor_property(
                'import_custom_attribute', True
            )

        elif extension == '.abc':
            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_materials = False
            task.options.import_animations = False
            task.options.override_full_name = True

        task.replace_existing = True
        task.automated = True
        return task

    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''

        if not self._validate_ftrack_asset(iAObj):
            return []

        assetRegistry = ue.AssetRegistryHelpers.get_asset_registry()
        skeletons = assetRegistry.get_assets_by_class('Skeleton')
        skeletonName = iAObj.options['ChooseSkeleton']

        skeletonAD = None
        for skeleton in skeletons:
            if skeleton.asset_name == skeletonName:
                skeletonAD = skeleton

        fbx_path = iAObj.filePath

        ftrack_asset_version = ftrack.AssetVersion(iAObj.assetVersionId)
        asset_name = ftrack_asset_version.getParent().get('name')
        import_path = (
            '/Game/'
            + self._get_asset_relative_path(ftrack_asset_version)
            + asset_name
        )

        # ensure there is no spaces
        import_path = import_path.replace(' ', '_')
        ftrack_old_node = None
        try:
            ftrack_old_node = self._find_asset_instance(
                import_path, iAObj.assetVersionId, iAObj.assetType
            )
        except Exception as error:
            logging.error(error)

        importedAssetNames = []
        if ftrack_old_node != None:
            msgBox = QMessageBox()
            msgBox.setText('This asset already exists in the project!')
            msgBox.setInformativeText("Do you want to reimport this asset?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)
            ret = msgBox.exec_()
            old_node_name = str(ftrack_old_node.get_name())

            if ret == QMessageBox.Yes:
                # Delete old asset
                self.changeVersion(iAObj, old_node_name)
                importedAssetNames.append(old_node_name)
                logging.info(
                    'Changed version of existing asset ' + old_node_name
                )

            elif ret == QMessageBox.No:
                logging.info(
                    'Not changing version of existing asset ' + old_node_name
                )

        else:
            task = self._get_asset_import_task(iAObj)
            if iAObj.options['UseCustomRange']:
                task.options.anim_sequence_import_data.set_editor_property(
                    'animation_length',
                    ue.FBXAnimationLengthImportType.FBXALIT_SET_RANGE,
                )
                rangeInterval = ue.Int32Interval()
                rangeInterval.set_editor_property(
                    'min', iAObj.options['AnimRangeMin']
                )
                rangeInterval.set_editor_property(
                    'max', iAObj.options['AnimRangeMax']
                )
                task.options.anim_sequence_import_data.set_editor_property(
                    'frame_import_range', rangeInterval
                )
            else:
                task.options.anim_sequence_import_data.set_editor_property(
                    'animation_length',
                    ue.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME,
                )

            task.options.set_editor_property(
                'skeleton', skeletonAD.get_asset())
            task.filename = fbx_path
            task.destination_path = import_path

            ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            self.name_import = task.imported_object_paths[0]
            loaded_anim = ue.EditorAssetLibrary.load_asset(
                task.imported_object_paths[0]
            )
            importedAssetNames.append(
                self._rename_object_with_prefix(loaded_anim, 'A')
            )

            # Add ftrack data to object
            try:
                self.addMetaData(iAObj, loaded_anim)
            except Exception as error:
                logging.error(error)

        return importedAssetNames

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''

        if not self._validate_ftrack_asset(iAObj):
            return False

        assets = (
            ue.AssetRegistryHelpers()
            .get_asset_registry()
            .get_assets_by_path('/Game', True)
        )
        for asset_data in assets:
            # unfortunately to access the tag values objects needs to be
            # in memory....
            asset = asset_data.get_asset()
            if str(asset.get_name()) == applicationObject:
                task = self._get_asset_import_task(iAObj)
                task.options.set_editor_property(
                    'skeleton', asset.get_editor_property('skeleton')
                )
                task.filename = iAObj.filePath
                task.destination_path = str(asset_data.package_path)
                task.destination_name = str(asset_data.asset_name)
                ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
                    [task]
                )
                if len(task.imported_object_paths):
                    self.updateMetaData(iAObj, asset)
                    return True
        return False

    @staticmethod
    def exportOptions():
        '''Return export options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Make Reviewable" accepts="unreal" enabled="False">
                <option type="checkbox" name="MakeReviewable" value="True"/>
            </row>
        </tab>
        '''
        return xml

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Choose Skeleton" accepts="unreal">
                <option type="combo" name="ChooseSkeleton" >{0}</option>
            </row>            
            <row name="Use Custom Animation Range" accepts="unreal">                
                <option type="checkbox" name="UseCustomRange" value="False"/>
            </row>
            <row name="Range" accepts="unreal"> 
                <option type="float" name="AnimRangeMin" value="1"/>
                <option type="float" name="AnimRangeMax" value="100"/>
            </row>
        </tab>
        '''
        assetRegistry = ue.AssetRegistryHelpers.get_asset_registry()
        skeletons = assetRegistry.get_assets_by_class('Skeleton')
        skeletonsInTheScene = ""
        for skeleton in skeletons:
            str = '''<optionitem name="{0}"/>'''.format(skeleton.asset_name)
            skeletonsInTheScene += str

        xml = xml.format(skeletonsInTheScene)
        return xml


class GeometryAsset(GenericAsset):
    def __init__(self):
        super(GeometryAsset, self).__init__()

    def _get_asset_import_task(self, iAObj):
        extension = os.path.splitext(iAObj.filePath)[-1]

        if extension == '.fbx':
            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_mesh = True
            task.options.import_as_skeletal = False
            task.options.import_materials = False
            task.options.import_animations = False
            task.options.create_physics_asset = False
            task.options.override_full_name = True
            task.options.automated_import_should_detect_type = False
            task.options.mesh_type_to_import = ue.FBXImportType.FBXIT_STATIC_MESH
            task.options.static_mesh_import_data = ue.FbxStaticMeshImportData()
            task.options.static_mesh_import_data.set_editor_property(
                'combine_meshes', True
            )

        elif extension == '.abc':
            task = ue.AssetImportTask()
            task.options = ue.FbxImportUI()
            task.options.import_materials = False
            task.options.import_animations = False
            task.options.override_full_name = True

        task.replace_existing = True
        task.automated = True
        task.save = True
        return task

    def importAsset(self, iAObj=None):
        '''Import geometry asset defined in *iAObj*'''

        if not self._validate_ftrack_asset(iAObj):
            return []

        fbx_path = iAObj.filePath
        ftrack_asset_version = ftrack.AssetVersion(iAObj.assetVersionId)
        ftrack_asset = ftrack_asset_version.getParent()
        asset_name = ftrack_asset.get('name')
        asset_name = upperFirst(asset_name)

        import_path = (
            '/Game/'
            + self._get_asset_relative_path(ftrack_asset_version)
            + asset_name
        )

        # ensure there is no spaces
        import_path = import_path.replace(' ', '_')
        ftrack_old_node = None
        try:
            ftrack_old_node = self._find_asset_instance(
                import_path, iAObj.assetVersionId, iAObj.assetType
            )
        except Exception as error:
            logging.error(error)

        importedAssetNames = []
        if ftrack_old_node != None:
            msgBox = QMessageBox()
            msgBox.setText('This asset already exists in the project!')
            msgBox.setInformativeText("Do you want to reimport this asset?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)
            ret = msgBox.exec_()
            old_node_name = str(ftrack_old_node.get_name())

            if ret == QMessageBox.Yes:
                # Delete old asset
                self.changeVersion(iAObj, old_node_name)
                importedAssetNames.append(old_node_name)
                logging.info(
                    'Changed version of existing asset ' + old_node_name
                )

            elif ret == QMessageBox.No:
                logging.info(
                    'Not changing version of existing asset ' + old_node_name
                )

        else:
            task = self._get_asset_import_task(iAObj)
            task.filename = fbx_path
            task.destination_path = import_path
            task.options.import_materials = iAObj.options['importMaterial']
            ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            self.name_import = task.imported_object_paths[0]
            loaded_mesh = ue.EditorAssetLibrary.load_asset(
                task.imported_object_paths[0]
            )
            importedAssetNames.append(
                self._rename_object_with_prefix(loaded_mesh, 'S')
            )

            # add meta data
            try:
                self.addMetaData(iAObj, loaded_mesh)
            except Exception as error:
                logging.error(error)

        return importedAssetNames

    @staticmethod
    def exportOptions():
        '''Return export options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Make Reviewable" accepts="unreal" enabled="False">
                <option type="checkbox" name="MakeReviewable" value="True"/>
            </row>
        </tab>
        '''
        return xml

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Import Material" accepts="unreal">                
                <option type="checkbox" name="importMaterial" value="True"/>
            </row>
        </tab>
        '''
        return xml


class ImgSequenceAsset(GenericAsset):
    def __init__(self):
        super(ImgSequenceAsset, self).__init__()

    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''

        if not self._validate_ftrack_asset(iAObj, '.zip'):
            return []

        # unzip package asset
        zip_path = iAObj.filePath
        override_existing = iAObj.options['OverrideExisting']
        importedAssetNames = []

        # use integration-specific logger
        logger = logging.getLogger("ftrack_connect_unreal_engine")
        logger.info("Importing pacakge asset: {0}".format(zip_path))

        with ZipFile(zip_path, 'r') as package_asset:
            map_package_path = None

            # In Unreal, asset paths are relative to the Content directory.
            # In order to migrate assets correctly between projects, they must
            # be moved from one Content directory to another. 
            content_dir = ue.SystemLibrary.get_project_content_directory()

            for asset in package_asset.namelist():
                # override existing assets if specified by user
                asset_path = os.path.normpath(
                    os.path.join(content_dir, asset)
                )

                if override_existing or not os.path.isfile(asset_path):
                    importedAssetNames.append(asset)
                
                    # check if asset is a umap file
                    (_, src_name) = os.path.split(asset_path)
                    (_, src_extension) = os.path.splitext(src_name)
                    if src_extension.lower() == ".umap":
                        map_package_path = asset_path
            
            import_count = len(importedAssetNames)
            # extract contents of the package_asset
            if import_count > 0:
                try:
                    # Note: ZipFile.extractall overwrites existing files by default
                    package_asset.extractall(path = content_dir, members = importedAssetNames)
                except Exception as error:
                    logger.error(error)
                    return []

                # load the extracted map, if one was imported
                if map_package_path:
                    logger.info("Loading the map imported from package: {0}".format(map_package_path))
                    try:
                        ue.EditorLoadingAndSavingUtils.load_map(map_package_path)
                    except Exception as error:
                        logger.error(error)

            logging.info("Number of assets imported: {0}".format(import_count))

        return importedAssetNames

    def publishAsset(self, iAObj, masterSequence):
        '''Publish the asset defined by the provided *iAObj*.'''
        dest_folder = os.path.join(
            ue.SystemLibrary.get_project_saved_directory(), 'VideoCaptures'
        )
        unreal_map = ue.EditorLevelLibrary.get_editor_world()
        unreal_map_package_path = unreal_map.get_outermost().get_path_name()
        unreal_map_path = unreal_map.get_path_name()
        unreal_asset_path = masterSequence.get_path_name()

        publishReviewable = iAObj.options.get('MakeReviewable')
        publishCurrentScene = iAObj.options.get('CurrentScene')

        asset_name = self._standard_structure.sanitise_for_filesystem(iAObj.assetName)

        publishedComponents = []

        # Publish Component: reviewable
        if publishReviewable:
            componentName = "reviewable_asset"
            movie_name = "{}_reviewable".format(asset_name)
            rendered, path = self._render(
                dest_folder,
                unreal_map_path,
                unreal_asset_path,
                movie_name,
                masterSequence.get_display_rate().numerator,
            )
            if rendered:
                publishedComponents.append(
                    FTComponent(componentname=componentName, path=path)
                )

        # Publish Component: image_sequence
        imgComponentName = "image_sequence"

        rendered, path = self._render(
            dest_folder,
            unreal_map_path,
            unreal_asset_path,
            asset_name,
            masterSequence.get_display_rate().numerator,
            True,
        )

        # try to get start and end frames from sequence this allow local control for test publish(subset of sequence)
        frameStart = masterSequence.get_playback_start()
        frameEnd = masterSequence.get_playback_end() - 1
        base_file_path = path[:-12] if path.endswith('.{frame}.exr') else path

        imgComponentPath = "{0}.%04d.{1} [{2}-{3}]".format(
            base_file_path, 'exr', frameStart, frameEnd
        )
        publishedComponents.append(
            FTComponent(componentname=imgComponentName, path=imgComponentPath)
        )

        # Publish Component: Current Scene
        if publishCurrentScene:
            componentName = "package_asset"
            package_name = "{}_package".format(asset_name)
            package_result, package_path = self._package_current_scene(
                dest_folder,
                unreal_map_package_path,
                package_name
            )
            if package_result:
                publishedComponents.append(
                    FTComponent(componentname=componentName, path=package_path)
                )

        return publishedComponents, 'Published ' + iAObj.assetType + ' asset'

    @staticmethod
    def exportOptions():
        '''Return export options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Make Reviewable" accepts="unreal" enabled="True">
                <option type="checkbox" name="MakeReviewable" value="True"/>
            </row>
            <row name="Publish Current Scene" accepts="unreal" enabled="True">
                <option type="checkbox" name="CurrentScene" value="True"/>
            </row>        
        </tab>
        '''
        return xml

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Override Existing Assets" accepts="unreal">                
                <option type="checkbox" name="OverrideExisting" value="True"/>
            </row>
        </tab>
        '''
        return xml

def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name="rig", cls=RigAsset)
    assetHandler.registerAssetType(name="anim", cls=AnimationAsset)
    assetHandler.registerAssetType(name="geo", cls=GeometryAsset)
    assetHandler.registerAssetType(name="img", cls=ImgSequenceAsset)

def upperFirst(x):
    return x[0].upper() + x[1:]
