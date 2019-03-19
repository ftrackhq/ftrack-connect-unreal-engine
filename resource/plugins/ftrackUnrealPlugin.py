# :coding: utf-8
# :copyright: Copyright (c) 2018 Pinta Studios

from unreal_engine.classes import StructureFactory
from unreal_engine.structs import StructVariableDescription
from unreal_engine.enums import EPinContainerType

class ftrackAssetNode():
    def __init__(self):

        # initializer
        self.aLocked = StructVariableDescription()
        self.aLocked.VarName = 'locked'
        self.aLocked.FriendlyName = 'Locked'
        self.aLocked.Category = 'bool'

        self.aAssetLink = StructVariableDescription()
        self.aAssetLink.VarName = 'assetLink'
        self.aAssetLink.FriendlyName = 'Asset Link'
        self.aAssetLink.ContainerType = EPinContainerType.Set
        self.aAssetLink.Category = 'object'

        self.aAssetVersion = StructVariableDescription()
        self.aAssetVersion.VarName = 'assetVersion'
        self.aAssetVersion.FriendlyName = 'Asset Version'
        self.aAssetVersion.Category = 'int'

        self.aAssetId = StructVariableDescription()
        self.aAssetId.VarName = 'assetId'
        self.aAssetId.FriendlyName = 'Asset Id'
        self.aAssetId.Category = 'string'

        self.aAssetPath = StructVariableDescription()
        self.aAssetPath.VarName = 'assetPath'
        self.aAssetPath.FriendlyName = 'Asset Path'
        self.aAssetPath.Category = 'string'

        self.aAssetTake = StructVariableDescription()
        self.aAssetTake.VarName = 'assetTake'
        self.aAssetTake.FriendlyName = 'Asset Take'
        self.aAssetTake.Category = 'name'

        self.aAssetType = StructVariableDescription()
        self.aAssetType.VarName = 'assetType'
        self.aAssetType.FriendlyName = 'Asset Type'
        self.aAssetType.Category = 'string'

        self.aAssetComponentId = StructVariableDescription()
        self.aAssetComponentId.VarName = 'assetComponentId'
        self.aAssetComponentId.FriendlyName = 'Asset Component Id'
        self.aAssetComponentId.Category = 'string'

    def createFtrackStructure(self, name='empty_actor', path='/Game'):
        self.structure_factory = StructureFactory()
        self.structure_ftrack = self.structure_factory.factory_create_new(path + '/' + name)

        # Add the attributes to the node
        self.structure_ftrack.struct_add_variable(self.aLocked)
        self.structure_ftrack.struct_add_variable(self.aAssetLink)
        self.structure_ftrack.struct_add_variable(self.aAssetTake)
        self.structure_ftrack.struct_add_variable(self.aAssetType)
        self.structure_ftrack.struct_add_variable(self.aAssetComponentId)
        self.structure_ftrack.struct_add_variable(self.aAssetVersion)
        self.structure_ftrack.struct_add_variable(self.aAssetId)
        self.structure_ftrack.struct_add_variable(self.aAssetPath)

        # remove default variable (created by the factory using its Guid)
        # we cannot do this before, because structs cannot be empty
        first_var = self.structure_ftrack.struct_get_variables()[0]
        self.structure_ftrack.struct_remove_variable(first_var.VarGuid)

        #self.structure_ftrack.save_package()

    def setFtrackNodeAttr(self, attrName, info):
        #self.structure_ftrack.set_metadata(attr, info)
        var = self.getAttr(attrName)
        var.set_field('DefaultValue', str(info) )
        self.structure_ftrack.struct_remove_variable(var.VarGuid)
        self.structure_ftrack.struct_add_variable(var)
        #self.structure_ftrack.save_package()

    def getAttr(self, attr):
        vars = self.structure_ftrack.struct_get_variables()
        for var in vars:
            #print var.get_field('VarName')
            if attr == var.get_field('VarName'):
                #print var
                return var

    def saveFtrackNode(self):
        self.structure_ftrack.save_package()

    #def getFtrackMetaData(self, attr):
    #   return self.structure_ftrack.get_metadata(attr)


#ftNode = ftrackAssetNode()
#ftNode.createFtrackStructure()
#ftNode.setFtrackNodeAttr('assetVersion', '3')
#print ftNode.getFtrackMetaData('assetVersion')