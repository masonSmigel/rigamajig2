#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: model.py
    author: masonsmigel
    date: 07/2022
    description: This module contains our rig builder.
                 It acts as a wrapper to manage all functions of the rig_builder.
"""
import logging
import os
import time
import typing

import maya.api.OpenMaya as om2
import maya.cmds as cmds

import rigamajig2.maya.builder.data
import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.data.component_data as component_data
import rigamajig2.maya.file as file
import rigamajig2.maya.meta as meta
import rigamajig2.shared.common as common
import rigamajig2.shared.path as rig_path
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import core
from rigamajig2.maya.builder import model
from rigamajig2.maya.cmpts import base

Component = typing.Type[base.Base]
_StringList = typing.List[str]

logger = logging.getLogger(__name__)


# pylint:disable=too-many-public-methods
class Builder(object):
    """
    The builder is the foundational class used to construct rigs with Rigamajig2.
    """

    VERSIONS_DIRECTORY = "versions"

    def __init__(self, rigFile=None):
        """
        Initialize the builder
        :param rigFile: path to the rig file
        """
        self.path = None
        self.rigFile = None
        self.builderData = {}

        if rigFile: self.setRigFile(rigFile)

        self.componentList = list()
        self._availableComponents = core.findComponents()
        # variables we need
        self.topSkeletonNodes = list()

    def getAvailableComponents(self) -> typing.List[str]:
        """ Get all available components"""
        return self._availableComponents

    def getAbsolutePath(self, path) -> str:
        """
        Get the absolute path of the given path relative to the rigEnvironment

        :param str path: Path to get relative to the rig environment
        """
        if path:
            path = common.getFirstIndex(path)
            # TODO: add in a check if this is a single file or multipleFiles
            return os.path.realpath(os.path.join(self.path, path))

    # --------------------------------------------------------------------------------
    # RIG BUILD STEPS
    # --------------------------------------------------------------------------------
    def importModel(self, path: str = None) -> None:
        """
        Import the model file

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsolutePath(self.builderData.get(constants.MODEL_FILE))
        model.importModel(path)
        logger.info("Model loaded")

    def loadJoints(self, paths: str = None) -> None:
        """
         Load the joint Data to a json file

        :param str paths: list of paths Path to the json file. if none is provided use the data from the rigFile
        """
        paths = paths or self.builderData.get(constants.SKELETON_POS)

        for path in common.toList(paths):
            absolutePath = self.getAbsolutePath(path)
            rigamajig2.maya.builder.data.loadJoints(absolutePath)
            logger.info(f"Joints loaded : {path}")

    def saveJoints(self, fileStack: _StringList = None, method="merge") -> _StringList:

        """
        Save the joint Data to a json file

        :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
        :param str method: method of data merging to apply. Default is "merge"
        """
        fileStack = common.toList(fileStack)
        dataToSave = rigamajig2.maya.builder.data.gatherJoints()

        layeredSaveInfo = rigamajig2.maya.builder.data.gatherLayeredSaveData(
            dataToSave=dataToSave,
            fileStack=fileStack,
            dataType="JointData",
            method=method)

        savedFiles = rigamajig2.maya.builder.data.performLayeredSave(layeredSaveInfo, dataType="JointData", prompt=True)

        if savedFiles:
            logger.info("Joint positions Saved -- complete")
            return savedFiles

    def initialize(self) -> None:
        """
        Initialize rig (this is where the user can make changes)
        """

        for component in self.componentList:
            logger.info('Initializing: {}'.format(component.name))
            component.initializeComponent()

        logger.info("initialize -- complete")

    def guide(self) -> None:
        """
        guide the rig
        """

        if not cmds.objExists("guides"):
            cmds.createNode("transform", name="guides")

        for component in self.componentList:
            logger.info('Guiding: {}'.format(component.name))
            component.guideComponent()
            if hasattr(component, "guidesHierarchy") and component.guidesHierarchy:
                parent = cmds.listRelatives(component.guidesHierarchy, p=True)
                if parent and parent[0] == 'guides':
                    break
                cmds.parent(component.guidesHierarchy, "guides")
            self.updateMaya()

        self.loadGuideData()
        logger.info("guide -- complete")

    def build(self) -> None:
        """
        build rig
        """

        # we need to make sure the main.main component gets built first if it exists in the list.
        # this is because all components that use the joint.connectChains function check for a bind group
        # to build the proper scale constraints
        for component in self.componentList:
            if component.getComponentType() == 'main.main':
                self.componentList.remove(component)
                self.componentList.insert(0, component)

        # now we can safely build all the components in the scene
        for component in self.componentList:
            logger.info('Building: {}'.format(component.name))
            component.buildComponent()

            if cmds.objExists('rig') and component.getComponentType() != 'main.main':
                if hasattr(component, "rootHierarchy"):
                    if not cmds.listRelatives(component.rootHierarchy, p=True):
                        cmds.parent(component.rootHierarchy, 'rig')

            # refresh the viewport after each component is built.
            self.updateMaya()

        # parent the bind joints to the bind group. if one exists
        if cmds.objExists('bind'):
            topSkeletonNodes = meta.getTagged('skeleton_root')
            if topSkeletonNodes:
                for topSkeletonNode in topSkeletonNodes:
                    if not cmds.listRelatives(topSkeletonNode, p=True):
                        cmds.parent(topSkeletonNodes, common.BINDTAG)

        # if the model group exists. parent the model
        if cmds.objExists('model'):
            topModelNodes = meta.getTagged('model_root')
            if topModelNodes:
                if not cmds.listRelatives(topModelNodes, p=True):
                    cmds.parent(topModelNodes, 'model')

        logger.info("build -- complete")

    def connect(self) -> None:
        """
        connect rig
        """
        for component in self.componentList:
            logger.info('Connecting: {}'.format(component.name))
            component.connectComponent()
            self.updateMaya()
        logger.info("connect -- complete")

    def finalize(self) -> None:
        """
        finalize rig
        """
        for component in self.componentList:
            logger.info('Finalizing: {}'.format(component.name))
            component.finalizeComponent()
            self.updateMaya()

        # delete the guide group
        cmds.delete("guides")

        logger.info("finalize -- complete")

    def optimize(self) -> None:
        """
        optimize rig
        """
        for component in self.componentList:
            logger.info('Optimizing {}'.format(component.name))
            component.optimizeComponent()
            self.updateMaya()
        logger.info("optimize -- complete")

    def saveComponents(self, fileStack: _StringList = None, method: str = "merge") -> _StringList or None:
        """
        Save out components to a file.
        This only saves component settings such as name, inputs, spaces and names.

        :param str fileStack: path to the component data file
        :param str method: method of data merging to apply. Default is "merge"
        """

        # because component data is gathered from the class but saved with the name as a key
        # this needs to be done in steps. First we can define our save dictionaries using the layered save...
        componentNameList = [c.name for c in self.componentList]
        saveDict = rigamajig2.maya.builder.data.gatherLayeredSaveData(
            dataToSave=componentNameList,
            fileStack=fileStack,
            dataType="ComponentData",
            method=method)

        # if we escape from the save then we can return
        if not rigamajig2.maya.builder.data.layeredSavePrompt(saveDataDict=saveDict, dataType="ComponentData"):
            return

        # ... next loop through the save dict and gather component data based on the component name.
        for dataFile in saveDict:
            componentDataObj = component_data.ComponentData()

            # loop through the list of component names
            for componentName in saveDict[dataFile][rigamajig2.maya.builder.data.CHANGED]:
                component = self.findComponent(name=componentName)
                componentDataObj.gatherData(component)
            componentDataObj.write(dataFile)
            logger.info(f"Component Data saved to {dataFile}")

        if saveDict:
            logger.info("Components Saved -- Complete")

        return [filepath for filepath in saveDict.keys()]

    def loadComponents(self, paths: str = None) -> None:
        """
        Load components from a json file. This will only load the component settings and objects.

        :param str paths: Path to the json file. if none is provided use the data from the rigFile
        """
        paths = paths or self.builderData.get(constants.COMPONENTS)

        self.setComponents(list())
        for path in common.toList(paths):
            path = self.getAbsolutePath(path)

            componentDataObj = component_data.ComponentData()
            componentDataObj.read(path)

            # look through each component and add it to the builder list
            # check before adding it so only one instance of each exists in the list
            for component in componentDataObj.getKeys():
                instance = common.getFirstIndex(componentDataObj.applyData(component))

                # we only want to add components with a new name. Each component should have a unique name
                componentNameList = [c.name for c in self.componentList]
                if instance.name not in componentNameList:
                    self.componentList.append(instance)

        logger.info("components loaded -- complete")

    def loadControlShapes(self, paths: str = None, applyColor: bool = True) -> None:
        """
        Load the control shapes

        :param list paths: Path to the json file. if none is provided use the data from the rigFile
        :param bool applyColor: Apply the control colors.
        """
        paths = paths or self.builderData.get(constants.CONTROL_SHAPES)

        for path in common.toList(paths):
            # make the path an absolute

            absPath = self.getAbsolutePath(path)
            rigamajig2.maya.builder.data.loadControlShapes(absPath, applyColor=applyColor)
            self.updateMaya()
            logger.info(f"control shapes loaded: {path}")

    def saveControlShapes(self, fileStack: _StringList = None, method: str = 'merge') -> _StringList:
        """
        Save the control shapes

        :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
        :param str method: method of data merging to apply. Default is "merge"
        """
        layeredSaveInfo = rigamajig2.maya.builder.data.gatherLayeredSaveData(
            dataToSave=rigamajig2.maya.builder.data.gatherControlShapes(),
            fileStack=fileStack,
            dataType="CurveData",
            method=method)

        savedFiles = rigamajig2.maya.builder.data.performLayeredSave(layeredSaveInfo, dataType="CurveData", prompt=True)
        if savedFiles:
            logger.info("Control Shapes Save -- Complete")
            return savedFiles

    def loadGuideData(self, paths: str = None):
        """
        Load guide data

        :param list paths: Path to the json file. if none is provided use the data from the rigFile
        """
        paths = paths or self.builderData.get(constants.GUIDES)

        for path in common.toList(paths):
            absPath = self.getAbsolutePath(path)
            if rigamajig2.maya.builder.data.loadGuideData(absPath):
                logger.info(f"guides loaded: {path}")

    def saveGuideData(self, fileStack: _StringList = None, method: str = "merge") -> _StringList:
        """
        Save guides data

        :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
        :param str method: method of data merging to apply. Default is "merge"
        """
        # rigFileData = common.toList(self.getAbsolutePath(self.builderData.get(constants.GUIDES)))[-1]
        # path = path or rigFileData
        fileStack = common.toList(fileStack)
        dataToSave = rigamajig2.maya.builder.data.gatherGuides()
        layeredSaveInfo = rigamajig2.maya.builder.data.gatherLayeredSaveData(dataToSave=dataToSave, fileStack=fileStack, dataType="GuideData",
                                                                             method=method)
        savedFiles = rigamajig2.maya.builder.data.performLayeredSave(saveDataDict=layeredSaveInfo, dataType="GuideData", prompt=True)

        if savedFiles:
            logger.info("Guides Save  -- complete")
            return savedFiles

    def loadPoseReaders(self, paths: str = None, replace: bool = True) -> None:
        """
        Load pose readers

        :param list paths: Path to the json file. if none is provided use the data from the rigFile
        :param replace: Replace existing pose readers.
        """
        paths = paths or self.builderData.get(constants.PSD) or ''

        for path in common.toList(paths):
            absPath = self.getAbsolutePath(path)
            if rigamajig2.maya.builder.data.loadPoseReaders(absPath, replace=replace):
                logger.info(f"pose readers loaded: {path}")

    def savePoseReaders(self, fileStack: _StringList = None) -> _StringList:
        """
        Save out pose readers

        :param str fileStack: Path to the json file. if none is provided use the data from the rigFile.
        """

        # path = path or self.getAbsolutePath(self.builderData.get(constants.PSD))

        allPoseReaders = rigamajig2.maya.builder.data.gatherPoseReaders()

        layeredSaveInfo = rigamajig2.maya.builder.data.gatherLayeredSaveData(
            dataToSave=allPoseReaders,
            fileStack=fileStack,
            dataType="PSDData",
            method="merge")

        savedFiles = rigamajig2.maya.builder.data.performLayeredSave(layeredSaveInfo, dataType="PSDData", prompt=True)

        # deform._savePoseReaders(path)
        if savedFiles:
            logger.info("Pose Readers Save -- Complete")
            return savedFiles

    def loadDeformationLayers(self, path: str = None) -> None:
        """
        Load the deformation layers

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsolutePath(self.builderData.get(constants.DEFORM_LAYERS)) or ''
        if rigamajig2.maya.builder.data.loadDeformLayers(path):
            logger.info("deformation layers loaded")

    def saveDeformationLayers(self, path: str = None) -> None:
        """
        Load the deformation layers

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsolutePath(self.builderData.get(constants.DEFORM_LAYERS)) or ''
        rigamajig2.maya.builder.data.saveDeformLayers(path)
        logger.info("deformation layers saved to: {}".format(path))

    def mergeDeformLayers(self) -> None:
        """Merge all deformation layers for all models"""
        import rigamajig2.maya.rig.deformLayer as deformLayer

        if len(meta.getTagged("hasDeformLayers")) > 0:
            for mesh in meta.getTagged("hasDeformLayers"):
                layer = deformLayer.DeformLayer(mesh)
                layer.stackDeformLayers(cleanup=True)

            logger.info("deformation layers merged")

    def loadSkinWeights(self, path: str = None) -> None:
        """
        Load the skin weights

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsolutePath(self.builderData.get(constants.SKINS)) or ''
        if rigamajig2.maya.builder.data.loadSkinWeights(path):
            logger.info("skin weights loaded")

    def saveSkinWeights(self, path: str = None) -> None:
        """
        Save the skin weights

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsolutePath(self.builderData.get(constants.SKINS)) or ''
        rigamajig2.maya.builder.data.saveSkinWeights(path)
        logger.info("skin weights for: {} saved to:{}".format(cmds.ls(sl=True), path))

    def loadDeformers(self, paths: _StringList = None) -> None:
        """ Load additional deformers
        :param list paths: Path to the json file. if none is provided use the data from the rigFile
        """
        if not paths:
            deformerPaths = self.builderData.get(constants.DEFORMERS) or []
            shapesPaths = self.builderData.get(constants.SHAPES) or []

            # if we have both deformerPaths and shapesPaths we need to join the two paths
            paths = common.toList(shapesPaths) + common.toList(deformerPaths)

        for path in common.toList(paths):
            absPath = self.getAbsolutePath(path)
            if rigamajig2.maya.builder.data.loadDeformer(absPath):
                logger.info(f"deformers loaded: {path}")

    # TODO: Fix this or delete it.
    def deleteComponents(self, clearList=True):
        """
        Delete all components

        :param bool clearList: clear the builder component list
        """
        mainComponent = None
        for component in self.componentList:
            if cmds.objExists(component.container):
                if component.getComponentType() == 'main.main':
                    mainComponent = component
                else:
                    component.deleteSetup()
        if mainComponent:
            mainComponent.deleteSetup()
        if clearList:
            self.componentList = list()

    # TODO: Fix this or delete it.
    def buildSingleComponent(self, name):
        """
        Build a single component based on the name and component type.
        If a component with the given name and type exists within the self.componentList build that component.

        Warning: Building a single component without necessary connection nodes in the scene may lead
        to unpredictable results. ONLY USE THIS FOR RND!

        :param name: name of the component to build
        :return:
        """
        component = self.findComponent(name=name)

        if component:
            component._intialize_cmpt()
            component._build_cmpt()
            component._connect_cmpt()
            component._finalize_cmpt()

            if cmds.objExists('rig') and component.getComponentType() != 'main.Main':
                if hasattr(component, "rootHierarchy"):
                    if not cmds.listRelatives(component.rootHierarchy, p=True):
                        cmds.parent(component.rootHierarchy, 'rig')

            logger.info("build: {} -- complete".format(component.name))

    # --------------------------------------------------------------------------------
    # RUN SCRIPTS UTILITIES
    # --------------------------------------------------------------------------------
    def preScript(self) -> None:
        """ Run pre scripts. use  through the PRE SCRIPT path"""
        scripts = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.PRE_SCRIPT)
        core.runAllScripts(scripts)

        logger.info("pre scripts -- complete")

    def postScript(self) -> None:
        """ Run pre scripts. use  through the POST SCRIPT path"""
        scripts = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.POST_SCRIPT)
        core.runAllScripts(scripts)
        logger.info("post scripts -- complete")

    def publishScript(self) -> None:
        """ Run pre scripts. use  through the PUB SCRIPT path"""
        scripts = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.PUB_SCRIPT)
        core.runAllScripts(scripts)
        logger.info("publish scripts -- complete")

    def run(self, publish:bool = False, savePublish:bool = True, versioning:bool = True) -> None:
        """
        Build a rig.

        This method orchestrates the entire rig building process. It encompasses loading components,
        building the rig, connecting elements, and finalizing the rig. Optionally, it can run the
        publishing steps if `publish` is set to True.

        :param publish: If True, the publishing steps will be executed.
        :param savePublish: If True, the publishing file will be saved. This is effective only when `publish` is True.
        :param versioning: Enable versioning. If True, a new version will be created in the publishing directory
                           each time the publishing file is overwritten. This allows for version control.
        """
        if not self.path:
            logger.error('you must provide a build environment path. Use _setRigFile()')
            return

        startTime = time.time()
        logger.info(f"\n"
                    f"Begin Rig Build\n{'-' * 70}\n"
                    f"build env: {self.path}\n"
                    )

        core.loadRequiredPlugins()
        self.preScript()

        self.importModel()

        self.loadJoints()

        self.loadComponents()
        self.initialize()
        self.guide()

        self.build()
        self.connect()
        self.finalize()
        self.loadPoseReaders()
        self.postScript()

        self.loadControlShapes()

        self.loadDeformationLayers()
        self.loadSkinWeights()
        self.loadDeformers()

        if publish:
            # self.optimize()
            self.mergeDeformLayers()
            self.publishScript()
            if savePublish:
                self.publish(versioning=versioning)
        endTime = time.time()
        finalTime = endTime - startTime

        logger.info('\nCompleted Rig Build \t -- time elapsed: {0}\n{1}\n'.format(finalTime, '-' * 70))

    # UTILITY FUNCTION TO PUBLISH THE RIG
    def publish(self, versioning:bool=True) -> None:
        """
        Publish a rig.

        This method saves the rig file into the output directory specified in `builderData`.
        If `versioning` is enabled, a new version is created in the publishing directory, allowing
        for version control.

        The output path and filename is built from the "output_file", "rig_name", "output_file_suffix"
        and "output_file_type" keys of the build file.

        :param versioning: If True, versioning will be applied to the published rig.
        :return: None
        """

        outputDirectory, outputFileName = self.getPublishFileInfo()

        # if we want to save a version as well
        if versioning:
            versionDirectory = os.path.join(outputDirectory, self.VERSIONS_DIRECTORY)

            existingVersions = self.getExistingVersions()
            nextVersion = len(existingVersions) + 1 if existingVersions else 1

            versionFileName = self.getPublishFileName(
                includeVersion=True,
                version=nextVersion
            )

            topNodes = cmds.ls(assemblies=True)
            topTransformNodes = cmds.ls(topNodes, exactType='transform')
            for node in topTransformNodes:
                cmds.addAttr(node, longName="__version__", attributeType='short', dv=nextVersion, k=False)
                cmds.setAttr("{}.__version__".format(node), lock=True)
                cmds.setAttr("{}.__version__".format(node), cb=True)

            versionPath = os.path.join(versionDirectory, versionFileName)

            # make the output directory and save the file. This will also make the directory for the main publish
            rig_path.mkdir(versionDirectory)
            outputVersionPath = file.saveAs(versionPath, log=False)
            logger.info("out rig versioned: {}   ({})".format(versionFileName, outputVersionPath))

        # create output directory and save
        publishPath = os.path.join(outputDirectory, outputFileName)
        file.saveAs(publishPath, log=False)
        logger.info("out rig published: {}  ({})".format(outputFileName, publishPath))

    def updateMaya(self) -> None:
        """ Update maya if in an interactive session"""
        # refresh the viewport after each component is built.
        if not om2.MGlobal.mayaState():
            cmds.refresh(f=True)

    # --------------------------------------------------------------------------------
    # GET
    # --------------------------------------------------------------------------------
    def getRigEnvironment(self) -> str:
        """Get the rig environment"""
        return self.path

    def getRigFile(self) -> str:
        """Get the rig file"""
        return self.rigFile

    def getComponentList(self) -> typing.List[Component]:
        """Get a list of all components in the builder"""
        return self.componentList

    def getPublishFileInfo(self) -> tuple[None, None] or tuple[str, str]:
        """
        Get the directory and filename for the output rig file.

        :return: Tuple[str, str] - A tuple containing the directory and filename.
        :raises RuntimeError: If an output path or rig name is not provided.
        """
        outputfile = self.getAbsolutePath(self.builderData.get(constants.OUTPUT_RIG))
        outputRigName = self.builderData.get(constants.RIG_NAME)

        if rig_path.isFile(outputfile):
            filename = outputfile.split(os.sep)[-1]
            directory = '/'.join(outputfile.split(os.sep)[:-1])
        elif rig_path.isDir(outputfile):
            directory = outputfile

            if not outputRigName:
                raise RuntimeError("Must select an output path or rig name to publish a rig")

            filename = self.getPublishFileName(includeVersion=False, version=None)
        else:
            return None, None

        return directory, filename

    def getPublishFileName(self, includeVersion=False, version: int = None):
        """
        Format the file name for an output Maya file.

        :param includeVersion: Whether to include the version number in the filename.
        :param version: The version number to include in the filename.
        :return: str - The formatted output file name.
        """
        outputRigName = self.builderData.get(constants.RIG_NAME)
        fileType = self.builderData.get(constants.OUTPUT_RIG_FILE_TYPE)
        suffix = self.builderData.get(constants.OUTPUT_FILE_SUFFIX) or ""
        if includeVersion:
            return f"{outputRigName}{suffix}_v{version:03d}.{fileType}"
        return f"{outputRigName}{suffix}.{fileType}"

    def getExistingVersions(self) -> list[str] or None:
        """
        Get a list of all existing versions in the currently set output directory.

        :return: List[str] - A list of existing version filenames, sorted in descending order.
        """
        directory, _ = self.getPublishFileInfo()
        outputRigName = self.builderData.get(constants.RIG_NAME)

        versionsDirectory = os.path.join(directory, self.VERSIONS_DIRECTORY)
        existingVersionFiles = []

        if not os.path.exists(versionsDirectory):
            return None

        # Iterate over all files in the directory
        for filename in os.listdir(versionsDirectory):
            if filename.startswith(outputRigName) and filename.lower().endswith(('.ma', '.mb')):
                existingVersionFiles.append(filename)

        existingVersionFiles.sort(reverse=True)
        return existingVersionFiles

    def getComponentFromContainer(self, container: str) -> Component:
        """
        Get the component object from a container

        :param container: name of the container to get the component for
        :return: component object
        """
        name = cmds.getAttr("{}.name".format(container))

        return self.findComponent(name)

    def findComponent(self, name: str) -> Component or None :
        """
        Find a component within the self.componentList.

        :param name: name of the component to find
        :return: component object
        """
        for component in self.componentList:
            _name = component.name
            _type = component.componentType
            if name == _name:
                return component

        logger.warning("No component: '{}' found within current build".format(name, type))
        return None

    # --------------------------------------------------------------------------------
    # SET
    # --------------------------------------------------------------------------------
    def setComponents(self, components: typing.List[Component]) -> None:
        """
        Set the `componentList`

        :param components: list of components to set
        """
        components = common.toList(components)
        self.componentList = components

    def appendComponents(self, components: typing.List[Component]) -> None:
        """
        append a component

        :param components: list of components to append
        """
        components = common.toList(components)
        for component in components:
            self.componentList.append(component)

    def setRigFile(self, rigFile: str) -> None:
        """
        Set the rig file.
        This will update the `rigFile` and `path` parameters

        :param rigFile: Path of the rig file to set.
        """
        if not os.path.exists(rigFile):
            raise RuntimeError("'{0}' does not exist".format(rigFile))
        self.rigFile = rigFile

        rigData = abstract_data.AbstractData()
        rigData.read(self.rigFile)
        data = rigData.getData()
        if "rig_env" not in data:
            rigEnvironmentPath = '../'
        else:
            rigEnvironmentPath = data["rig_env"]
        self.path = os.path.abspath(os.path.join(self.rigFile, rigEnvironmentPath))
        self.builderData = data

        # also set the rig file and rig environment into environment variables to access in other scripts if needed.
        os.environ['RIGAMJIG_FILE'] = self.rigFile
        os.environ['RIGAMJIG_ENV'] = self.path

        logger.info('\nRig Environment path: {0}'.format(self.path))

    def saveRigFile(self, dataDict):
        """
        Save a rig file.

        :param dataDict: dictionary of rig data to save to the rigFile
        :return:
        """
        data = abstract_data.AbstractData()
        data.read(self.rigFile)
        newData = data.getData()

        newData.update(dataDict)

        data.setData(newData)
        data.write(self.rigFile)

        logger.info(f"data saved to : {self.rigFile}")

    @staticmethod
    def getRigData(rigFile: str, key: str) -> typing.Any:
        """
        read the data from the self.rig_file. Kept here for compatibility of old code. Should probably be deleted!

        :param rigFile: path to thr rig file to get date from
        :param key: name of the dictionary key to get the data from
        :return:
        """
        return core.getRigData(rigFile=rigFile, key=key)
