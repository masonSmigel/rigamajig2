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

import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.file as file
import rigamajig2.maya.meta as meta
import rigamajig2.shared.common as common
import rigamajig2.shared.path as path
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import core
from rigamajig2.maya.builder import data_manager
from rigamajig2.maya.builder import model
from rigamajig2.maya.cmpts import base

_Component = typing.Type[base.Base]
_StringList = typing.List[str]

logger = logging.getLogger(__name__)

VALID_FILE_TYPES = ["ma", "mb"]


class Builder(object):
    """
    The builder is the foundational class used to construct rigs with Rigamajig2.

    The builder should always work with relative paths both inside the builder class and the builder UI.
    It is only when loading data that paths are converted to absolutePaths but should never be accessed outside of loading.
    """

    VERSIONS_DIRECTORY = "versions"

    def __init__(self, rigFile=None):
        """
        Initialize the builder
        :param rigFile: path to the rig file
        """
        self.path = None
        self.rigFile = None

        # private properties
        self._modelFile = None
        self._jointFiles = None
        self._guideFiles = None
        self._componentFiles = None
        self._controlShapeFiles = None
        self._poseReadersFiles = None
        self._skinsFile = None
        self._deformerFiles = None
        self._deformLayerFiles = None
        self._outputFilePath = None
        self._rigName = None
        self._outFileSuffix = None
        self._outputFileType = None
        self._localPreScripts = None
        self._localPostScripts = None
        self._localPubScripts = None

        self.builderData = {}

        if rigFile: self.setRigFile(rigFile)

        self.componentList = list()
        self._availableComponents = core.findComponents()
        # variables we need
        self.topSkeletonNodes = list()

    def getAvailableComponents(self) -> typing.List[str]:
        """ Get all available components"""
        return self._availableComponents

    def getAbsolutePath(self, filepath: path.RelativePath) -> path.AbsolutePath:
        """
        Get the absolute path of the given path relative to the rigEnvironment

        :param str filepath: Path to get relative to the rig environment
        """
        if filepath:
            filepath = common.getFirstIndex(filepath)
            return os.path.realpath(os.path.join(self.path, filepath))

    @property
    def rigName(self) -> str:
        return self._rigName

    @rigName.setter
    def rigName(self, value: str):
        self._rigName = value

    @property
    def modelFile(self) -> path.RelativePath:
        """Relative path to the model file"""
        return self._modelFile

    @modelFile.setter
    def modelFile(self, value):
        # todo maybe we can check this somehow?
        self._modelFile = value

    @property
    def jointFiles(self) -> typing.List[path.RelativePath]:
        return self._jointFiles

    @jointFiles.setter
    def jointFiles(self, value: typing.List[path.RelativePath]):
        self._jointFiles = value

    @property
    def guideFiles(self) -> typing.List[path.RelativePath]:
        return self._guideFiles

    @guideFiles.setter
    def guideFiles(self, value: typing.List[path.RelativePath]):
        self._guideFiles = value

    @property
    def componentFiles(self) -> typing.List[path.RelativePath]:
        return self._componentFiles

    @componentFiles.setter
    def componentFiles(self, value: typing.List[path.RelativePath]):
        self._componentFiles = value

    @property
    def controlShapeFiles(self) -> typing.List[path.RelativePath]:
        return self._controlShapeFiles

    @controlShapeFiles.setter
    def controlShapeFiles(self, value: typing.List[path.RelativePath]):
        self._controlShapeFiles = value

    @property
    def poseReadersFiles(self) -> typing.List[path.RelativePath]:
        return self._poseReadersFiles

    @poseReadersFiles.setter
    def poseReadersFiles(self, value: typing.List[path.RelativePath]):
        self._poseReadersFiles = value

    @property
    def skinsFile(self) -> path.RelativePath:
        """
        The skins file can either be a single json file or a directory.

        If a single file is used all skin data will be saved into that file.
        If a directory is specified each skinFile will be saved to a separate json file inside that directory.
        """
        return self._skinsFile

    @skinsFile.setter
    def skinsFile(self, value: path.RelativePath):
        self._skinsFile = value

    @property
    def deformerFiles(self) -> typing.List[path.RelativePath]:
        return self._deformerFiles

    @deformerFiles.setter
    def deformerFiles(self, value: typing.List[path.RelativePath]):
        self._deformerFiles = value

    @property
    def deformLayersFile(self) -> path.RelativePath:
        return self._deformLayerFiles

    @deformLayersFile.setter
    def deformLayersFile(self, value: path.RelativePath):
        self._deformLayerFiles = value

    @property
    def outputFilePath(self) -> path.RelativePath:
        return self._outputFilePath

    @outputFilePath.setter
    def outputFilePath(self, value: path.RelativePath):
        self._outputFilePath = value

    @property
    def outputFileSuffix(self) -> str:
        return self._outFileSuffix

    @outputFileSuffix.setter
    def outputFileSuffix(self, value: str):
        self._outFileSuffix = value

    @property
    def outputFileType(self) -> str:
        return self._outputFileType

    @outputFileType.setter
    def outputFileType(self, value: str):
        if value not in VALID_FILE_TYPES:
            logger.error(f"'{value}' is not a valid output file type.")
        self._outputFileType = value

    # TODO: rework the scripts so the local scripts can stay relative and easy to edit. while the full script list can
    # be absoulte
    @property
    def localPreScripts(self) -> typing.List[path.AbsolutePath]:
        """List of pre scripts local to this rig file"""
        scripts = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.PRE_SCRIPT)[0]
        return scripts

    @property
    def localPostScripts(self) -> typing.List[path.AbsolutePath]:
        """List of post scripts local to this rig file"""
        scripts = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.POST_SCRIPT)[0]
        return scripts

    @property
    def localPubScripts(self) -> typing.List[path.AbsolutePath]:
        """List of publish scripts local to this rig file"""
        scripts = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.PUB_SCRIPT)[0]
        return scripts

    @property
    def preScripts(self) -> typing.List[path.AbsolutePath]:
        """List of all pre scripts both local and inherited from archetypes"""
        scriptsDict = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.PRE_SCRIPT)
        scripts = list(scriptsDict.values())
        return common.joinLists(scripts)

    @property
    def postScripts(self) -> typing.List[path.AbsolutePath]:
        """List of all post scripts both local and inherited from archetypes"""
        scriptsDict = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.POST_SCRIPT)
        scripts = list(scriptsDict.values())
        return common.joinLists(scripts)

    @property
    def pubScripts(self) -> typing.List[path.AbsolutePath]:
        """List of all pub scripts both local and inherited from archetypes"""
        scriptsDict = core.GetCompleteScriptList.getScriptList(self.rigFile, constants.PUB_SCRIPT)
        scripts = list(scriptsDict.values())
        return common.joinLists(scripts)

    # --------------------------------------------------------------------------------
    # RIG BUILD STEPS
    # --------------------------------------------------------------------------------
    def importModel(self) -> None:
        """
        Import the model file
        """
        filepath = self.getAbsolutePath(self.modelFile)
        model.importModel(filepath)
        logger.info("Model loaded")

    def loadJoints(self) -> None:
        """
         Load the joint Data to a json file

        :param str filePaths: list of paths Path to the json file. if none is provided use the data from the rigFile
        """
        filePaths = self.jointFiles

        for filepath in common.toList(filePaths):
            absolutePath = self.getAbsolutePath(filepath)
            data_manager.loadJointData(absolutePath)
            logger.info(f"Joints loaded : {filepath}")

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

    def loadComponents(self) -> None:
        """
        Load components from a json file. This will only load the component settings and objects.

        :param str filepaths: Path to the json file. if none is provided use the data from the rigFile
        """
        filepaths = self.componentFiles

        self.setComponents([])
        for filepath in common.toList(filepaths):
            absolutePath = self.getAbsolutePath(filepath)
            data_manager.loadComponentData(self, filepath=absolutePath)
            logger.info(f"components loaded : {filepath}")

    def loadControlShapes(self, applyColor: bool = True) -> None:
        """
        Load the control shapes

        :param list filepaths: Path to the json file. if none is provided use the data from the rigFile
        :param bool applyColor: Apply the control colors.
        """
        filepaths = self.controlShapeFiles

        for filepath in common.toList(filepaths):
            # make the path an absolute

            absPath = self.getAbsolutePath(filepath)
            data_manager.loadControlShapeData(absPath, applyColor=applyColor)
            self.updateMaya()
            logger.info(f"control shapes loaded: {filepath}")

    def loadGuides(self):
        """
        Load guide data

        :param list filepaths: Path to the json file. if none is provided use the data from the rigFile
        """
        filepaths = self.guideFiles

        for filepath in common.toList(filepaths):
            absPath = self.getAbsolutePath(filepath)
            if data_manager.loadGuideData(absPath):
                logger.info(f"guides loaded: {filepath}")

    def loadPoseReaders(self, replace: bool = True) -> None:
        """
        Load pose readers

        :param list filepaths: Path to the json file. if none is provided use the data from the rigFile
        :param replace: Replace existing pose readers.
        """
        filepaths = self.poseReadersFiles or None

        for filepath in common.toList(filepaths):
            absPath = self.getAbsolutePath(filepath)
            if data_manager.loadPoseReaderData(absPath, replace=replace):
                logger.info(f"pose readers loaded: {filepath}")

    def loadDeformationLayers(self) -> None:
        """
        Load the deformation layers

        :param str filepath: Path to the json file. if none is provided use the data from the rigFile
        """
        filepath = self.getAbsolutePath(self.deformLayersFile) or None
        if data_manager.loadDeformationLayerData(filepath):
            logger.info("deformation layers loaded")

    def loadSkinWeights(self) -> None:
        """
        Load the skin weights

        :param str filepath: Path to the json file. if none is provided use the data from the rigFile
        """
        filepath = self.getAbsolutePath(self.skinsFile) or None
        if data_manager.loadSkinWeightData(filepath):
            logger.info("skin weights loaded")

    def loadDeformers(self ) -> None:
        """ Load additional deformers
        :param list filepaths: Path to the json file. if none is provided use the data from the rigFile
        """
        deformerPaths = self.deformerFiles or []

        for filepath in common.toList(deformerPaths):
            absPath = self.getAbsolutePath(filepath)
            if data_manager.loadDeformer(absPath):
                logger.info(f"deformers loaded: {filepath}")

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
    def runPreScripts(self) -> None:
        """ Run pre scripts. use  through the PRE SCRIPT path"""
        core.runAllScripts(self.preScripts)

        logger.info("pre scripts -- complete")

    def runPostScripts(self) -> None:
        """ Run pre scripts. use  through the POST SCRIPT path"""
        core.runAllScripts(self.postScripts)
        logger.info("post scripts -- complete")

    def runPublishScripts(self) -> None:
        """ Run pre scripts. use  through the PUB SCRIPT path"""
        core.runAllScripts(self.pubScripts)
        logger.info("publish scripts -- complete")

    def run(self, publish: bool = False, savePublish: bool = True, versioning: bool = True) -> None:
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
        self.runPreScripts()

        self.importModel()

        self.loadJoints()

        self.loadComponents()
        self.initialize()
        self.guide()

        self.loadGuides()

        self.build()
        self.connect()
        self.finalize()
        self.loadPoseReaders()
        self.runPostScripts()

        self.loadControlShapes()

        self.loadDeformationLayers()
        self.loadSkinWeights()
        self.loadDeformers()

        if publish:
            # self.optimize()
            self.runPublishScripts()
            if savePublish:
                self.publish(versioning=versioning)
        endTime = time.time()
        finalTime = endTime - startTime

        logger.info('\nCompleted Rig Build \t -- time elapsed: {0}\n{1}\n'.format(finalTime, '-' * 70))

    # UTILITY FUNCTION TO PUBLISH THE RIG
    def publish(self, versioning: bool = True) -> None:
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
            if not os.path.exists(versionDirectory):
                os.makedirs(versionDirectory)
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

    def getComponentList(self) -> typing.List[_Component]:
        """Get a list of all components in the builder"""
        return self.componentList

    def getPublishFileInfo(self) -> tuple[None, None] or tuple[str, str]:
        """
        Get the directory and filename for the output rig file.

        :return: Tuple[str, str] - A tuple containing the directory and filename.
        :raises RuntimeError: If an output path or rig name is not provided.
        """
        outputfile = self.getAbsolutePath(self.outputFilePath)

        if path.isFile(outputfile):
            filename = outputfile.split(os.sep)[-1]
            directory = '/'.join(outputfile.split(os.sep)[:-1])
        elif path.isDir(outputfile):
            directory = outputfile

            if not self.rigName:
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
        if includeVersion:
            return f"{self.rigName}{self.outputFileSuffix or ''}_v{version:03d}.{self.outputFileType}"
        return f"{self.rigName}{self.outputFileSuffix or ''}.{self.outputFileType}"

    def getExistingVersions(self) -> list[str] or None:
        """
        Get a list of all existing versions in the currently set output directory.

        :return: List[str] - A list of existing version filenames, sorted in descending order.
        """
        directory, _ = self.getPublishFileInfo()

        versionsDirectory = os.path.join(directory, self.VERSIONS_DIRECTORY)
        existingVersionFiles = []

        if not os.path.exists(versionsDirectory):
            return None

        # Iterate over all files in the directory
        for filename in os.listdir(versionsDirectory):
            if filename.startswith(self.rigName) and filename.lower().endswith(('.ma', '.mb')):
                existingVersionFiles.append(filename)

        existingVersionFiles.sort(reverse=True)
        return existingVersionFiles

    def getComponentFromContainer(self, container: str) -> _Component:
        """
        Get the component object from a container

        :param container: name of the container to get the component for
        :return: component object
        """
        name = cmds.getAttr("{}.name".format(container))

        return self.findComponent(name)

    def findComponent(self, name: str) -> _Component or None:
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
    def setComponents(self, components: typing.List[_Component]) -> None:
        """
        Set the `componentList`

        :param components: list of components to set
        """
        components = common.toList(components)
        self.componentList = components

    def appendComponents(self, components: typing.List[_Component]) -> None:
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

        # setup the rigamajig properties
        self.modelFile = data.get(constants.MODEL_FILE)
        self.jointFiles = data.get(constants.SKELETON_POS)
        self.guideFiles = data.get(constants.GUIDES)
        self.componentFiles = data.get(constants.COMPONENTS)
        self.controlShapeFiles = data.get(constants.CONTROL_SHAPES)
        self.poseReadersFiles = data.get(constants.PSD)
        self.skinsFile = data.get(constants.SKINS)
        self.deformerFiles = data.get(constants.DEFORMERS)
        self.deformLayerFiles = data.get(constants.DEFORM_LAYERS)
        self.outputFilePath = data.get(constants.OUTPUT_RIG)
        self.rigName = data.get(constants.RIG_NAME)
        self.outFileSuffix = data.get(constants.OUTPUT_FILE_SUFFIX)
        self.outputFileType = data.get(constants.OUTPUT_RIG_FILE_TYPE)

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
