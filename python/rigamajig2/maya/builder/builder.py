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
from typing import *

import maya.api.OpenMaya as om2
import maya.cmds as cmds

import rigamajig2.maya.data.abstractData as abstractData
import rigamajig2.maya.file as file
import rigamajig2.maya.meta as meta
import rigamajig2.shared.common as common
import rigamajig2.shared.path as path
from rigamajig2.maya.builder import componentManager, scriptManager
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import core
from rigamajig2.maya.builder import dataIO
from rigamajig2.maya.builder import model
from rigamajig2.maya.components import base

_Component = Type[base.BaseComponent]
_StringList = List[str]

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
        self.rigEnvironment = None
        self.rigFile = None

        self._availableComponents = componentManager.findComponents()
        self.componentList = []

        # rig file properties
        self._archetypeParent = None
        self._rigName = None
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
        self._outFileSuffix = None
        self._outputFileType = None
        self._localPreScripts = None
        self._localPostScripts = None
        self._localPubScripts = None

        if rigFile:
            self.setRigFile(rigFile)

    def getAvailableComponents(self) -> List[str]:
        """Get all available components"""
        return self._availableComponents

    def getAbsolutePath(self, filepath: path.RelativePath) -> path.AbsolutePath:
        """
        Get the absolute path of the given path relative to the rigEnvironment

        :param str filepath: Path to get relative to the rig environment
        """
        if filepath:
            filepath = common.getFirst(filepath)
            return os.path.realpath(os.path.join(self.rigEnvironment, filepath))

    @property
    def archetypeParent(self) -> str or List[str]:
        return self._archetypeParent

    @archetypeParent.setter
    def archetypeParent(self, value: str or List[str]):
        self._archetypeParent = value

    @property
    def rigName(self) -> str:
        return self._rigName

    @rigName.setter
    def rigName(self, value: str):
        logger.debug(f"Set Rig name to: {value}")
        self._rigName = value

    @property
    def modelFile(self) -> path.RelativePath:
        """Relative path to the model file"""
        return self._modelFile

    @modelFile.setter
    def modelFile(self, value: path.RelativePath):
        logger.debug(f"Set model file to: {value}")
        self._modelFile = value

    @property
    def jointFiles(self) -> List[path.RelativePath]:
        return self._jointFiles

    @jointFiles.setter
    def jointFiles(self, value: List[path.RelativePath]):
        logger.debug(f"Set joint files to: {value}")
        self._jointFiles = value

    @property
    def guideFiles(self) -> List[path.RelativePath]:
        return self._guideFiles

    @guideFiles.setter
    def guideFiles(self, value: List[path.RelativePath]):
        logger.debug(f"Set guide files to: {value}")
        self._guideFiles = value

    @property
    def componentFiles(self) -> List[path.RelativePath]:
        return self._componentFiles

    @componentFiles.setter
    def componentFiles(self, value: List[path.RelativePath]):
        logger.debug(f"Set component files to: {value}")
        self._componentFiles = value

    @property
    def controlShapeFiles(self) -> List[path.RelativePath]:
        return self._controlShapeFiles

    @controlShapeFiles.setter
    def controlShapeFiles(self, value: List[path.RelativePath]):
        logger.debug(f"Set controlShape files to: {value}")
        self._controlShapeFiles = value

    @property
    def poseReadersFiles(self) -> List[path.RelativePath]:
        return self._poseReadersFiles

    @poseReadersFiles.setter
    def poseReadersFiles(self, value: List[path.RelativePath]):
        logger.debug(f"Set pose Reader files to: {value}")

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
        logger.debug(f"Set skins files to: {value}")
        self._skinsFile = value

    @property
    def deformerFiles(self) -> List[path.RelativePath]:
        return self._deformerFiles

    @deformerFiles.setter
    def deformerFiles(self, value: List[path.RelativePath]):
        logger.debug(f"Set deformer files to: {value}")
        self._deformerFiles = value

    @property
    def deformLayersFile(self) -> path.RelativePath:
        return self._deformLayerFiles

    @deformLayersFile.setter
    def deformLayersFile(self, value: path.RelativePath):
        logger.debug(f"Set deform Layer files to: {value}")
        self._deformLayerFiles = value

    @property
    def outputFilePath(self) -> path.RelativePath:
        return self._outputFilePath

    @outputFilePath.setter
    def outputFilePath(self, value: path.RelativePath):
        logger.debug(f"Set output path files to: {value}")
        self._outputFilePath = value

    @property
    def outputFileSuffix(self) -> str:
        return self._outFileSuffix

    @outputFileSuffix.setter
    def outputFileSuffix(self, value: str):
        logger.debug(f"Set output suffix to: {value}")
        self._outFileSuffix = value

    @property
    def outputFileType(self) -> str:
        return self._outputFileType

    @outputFileType.setter
    def outputFileType(self, value: str):
        if value not in VALID_FILE_TYPES:
            logger.error(f"'{value}' is not a valid output file type.")
        logger.debug(f"Set output file type to: {value}")
        self._outputFileType = value

    @property
    def localPreScripts(self) -> List[path.RelativePath]:
        """List of pre scripts local to this rig file"""
        return self._localPreScripts

    @localPreScripts.setter
    def localPreScripts(self, value):
        relativeScriptList = []
        for script in common.toList(value):
            relativeScriptList.append(path.getRelativePath(script, self.rigEnvironment))
        logger.debug(f"Set local pre scripts to: {relativeScriptList}")
        self._localPreScripts = relativeScriptList

    @property
    def localPostScripts(self) -> List[path.RelativePath]:
        """List of post scripts local to this rig file"""
        return self._localPostScripts

    @localPostScripts.setter
    def localPostScripts(self, value):
        relativeScriptList = []
        for script in common.toList(value):
            relativeScriptList.append(path.getRelativePath(script, self.rigEnvironment))
        logger.debug(f"Set local post scripts to: {relativeScriptList}")
        self._localPostScripts = relativeScriptList

    @property
    def localPubScripts(self) -> List[path.RelativePath]:
        """List of publish scripts local to this rig file"""
        return self._localPubScripts

    @localPubScripts.setter
    def localPubScripts(self, value):
        relativeScriptList = []
        for script in common.toList(value):
            relativeScriptList.append(path.getRelativePath(script, self.rigEnvironment))
        logger.debug(f"Set local pub scripts to: {relativeScriptList}")
        self._localPubScripts = relativeScriptList

    # --------------------------------------------------------------------------------
    # RIG BUILD STEPS
    # --------------------------------------------------------------------------------
    def importModel(self) -> None:
        """
        Import the model file from the `modelFile` property
        """
        filepath = self.getAbsolutePath(self.modelFile)
        model.importModel(filepath)
        logger.info("Model loaded")

    def loadJoints(self) -> None:
        """
        Load the joint Data from the `jointFiles` property
        """
        filePaths = self.jointFiles

        for filepath in common.toList(filePaths):
            absolutePath = self.getAbsolutePath(filepath)
            dataIO.loadJointData(absolutePath)
            logger.info(f"Joints loaded : {filepath}")

    def initialize(self) -> None:
        """
        Initialize rig (this is where the user can make changes)
        """

        for component in self.componentList:
            logger.info("Initializing: {}".format(component.name))
            component.initializeComponent()

        logger.info("initialize -- complete")

    def guide(self) -> None:
        """
        guide the rig
        """

        if not cmds.objExists("guides"):
            cmds.createNode("transform", name="guides")

        for component in self.componentList:
            logger.info("Guiding: {}".format(component.name))
            component.guideComponent()
            if hasattr(component, "guidesHierarchy") and component.guidesHierarchy:
                parent = cmds.listRelatives(component.guidesHierarchy, p=True)
                if parent and parent[0] == "guides":
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
            if component.getComponentType() == "main.main":
                self.componentList.remove(component)
                self.componentList.insert(0, component)

        # now we can safely build all the components in the scene
        for component in self.componentList:
            logger.info("Building: {}".format(component.name))
            component.buildComponent()

            if cmds.objExists("rig") and component.getComponentType() != "main.main":
                if hasattr(component, "rootHierarchy"):
                    if not cmds.listRelatives(component.rootHierarchy, p=True):
                        cmds.parent(component.rootHierarchy, "rig")

            # refresh the viewport after each component is built.
            self.updateMaya()

        # parent the bind joints to the bind group. if one exists
        if cmds.objExists("bind"):
            topSkeletonNodes = meta.getTagged("skeleton_root")
            if topSkeletonNodes:
                for topSkeletonNode in topSkeletonNodes:
                    if not cmds.listRelatives(topSkeletonNode, p=True):
                        cmds.parent(topSkeletonNodes, common.BINDTAG)

        # if the model group exists. parent the model
        if cmds.objExists("model"):
            topModelNodes = meta.getTagged("model_root")
            if topModelNodes:
                if not cmds.listRelatives(topModelNodes, p=True):
                    cmds.parent(topModelNodes, "model")

        logger.info("build -- complete")

    def connect(self) -> None:
        """
        connect rig
        """
        for component in self.componentList:
            logger.info("Connecting: {}".format(component.name))
            component.connectComponent()
            self.updateMaya()
        logger.info("connect -- complete")

    def finalize(self) -> None:
        """
        finalize rig
        """
        for component in self.componentList:
            logger.info("Finalizing: {}".format(component.name))
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
            logger.info("Optimizing {}".format(component.name))
            component.optimizeComponent()
            self.updateMaya()
        logger.info("optimize -- complete")

    def loadComponents(self) -> None:
        """
        Load components from  the `componentFiles` property.
        This will only load the component settings and objects.
        """
        filepaths = self.componentFiles

        self.setComponents([])
        for filepath in common.toList(filepaths):
            absolutePath = self.getAbsolutePath(filepath)
            dataIO.loadComponentData(self, filepath=absolutePath)
            logger.info(f"components loaded : {filepath}")

    def loadControlShapes(self, applyColor: bool = True) -> None:
        """
        Load the control shapes from the `controlShapeFiles` property

        :param bool applyColor: Apply the control colors.
        """
        filepaths = self.controlShapeFiles

        for filepath in common.toList(filepaths):
            # make the path an absolute

            absPath = self.getAbsolutePath(filepath)
            dataIO.loadControlShapeData(absPath, applyColor=applyColor)
            self.updateMaya()
            logger.info(f"control shapes loaded: {filepath}")

    def loadGuides(self):
        """
        Load guide data from the `guideFiles` property
        """
        filepaths = self.guideFiles

        for filepath in common.toList(filepaths):
            absPath = self.getAbsolutePath(filepath)
            if dataIO.loadGuideData(absPath):
                logger.info(f"guides loaded: {filepath}")

    def loadPoseReaders(self, replace: bool = True) -> None:
        """
        Load pose readers from the `poseReadersFiles` property

        :param replace: Replace existing pose readers.
        """
        filepaths = self.poseReadersFiles or None

        for filepath in common.toList(filepaths):
            absPath = self.getAbsolutePath(filepath)
            if dataIO.loadPoseReaderData(absPath, replace=replace):
                logger.info(f"pose readers loaded: {filepath}")

    def loadDeformationLayers(self) -> None:
        """
        Load the deformation layers from the `deformLayersFile` property
        """
        filepath = self.getAbsolutePath(self.deformLayersFile) or None
        if dataIO.loadDeformationLayerData(filepath):
            logger.info("deformation layers loaded")

    def loadSkinWeights(self) -> None:
        """
        Load the skin weights from the `skinsFile` property
        """
        filepath = self.getAbsolutePath(self.skinsFile) or None
        if dataIO.loadSkinWeightData(filepath):
            logger.info("skin weights loaded")

    def loadDeformers(self) -> None:
        """
        Load additional deformers from the `deformerFiles` property
        """
        deformerPaths = self.deformerFiles or []

        for filepath in common.toList(deformerPaths):
            absPath = self.getAbsolutePath(filepath)
            if dataIO.loadDeformer(absPath):
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
                if component.getComponentType() == "main.main":
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

            if cmds.objExists("rig") and component.getComponentType() != "main.Main":
                if hasattr(component, "rootHierarchy"):
                    if not cmds.listRelatives(component.rootHierarchy, p=True):
                        cmds.parent(component.rootHierarchy, "rig")

            logger.info("build: {} -- complete".format(component.name))

    # --------------------------------------------------------------------------------
    # RUN SCRIPTS UTILITIES
    # --------------------------------------------------------------------------------

    def runBuilderScripts(self, scriptStep):
        """
        Run builder scripts for a specific script Type

        :param scriptStep: script type to run. This can be either
        """
        if scriptStep == constants.PRE_SCRIPT:
            localScripts = self.localPreScripts
            niceScriptStepName = "Pre script"
        elif scriptStep == constants.POST_SCRIPT:
            localScripts = self.localPostScripts
            niceScriptStepName = "Post script"
        elif scriptStep == constants.PUB_SCRIPT:
            localScripts = self.localPubScripts
            niceScriptStepName = "Pub script"
        else:
            raise KeyError(f"'{scriptStep} is not a valid script type")

        absoluteScripts = [self.getAbsolutePath(script) for script in localScripts]
        scriptManager.runAllScripts(absoluteScripts)
        if len(absoluteScripts):
            logger.info(f"{niceScriptStepName}: local scripts -- complete")

        # next get scripts to inherit
        scriptDict = scriptManager.GetCompleteScriptList.getScriptList(
            self.rigFile, scriptStep
        )

        inheritedScripts = {
            recursion: scripts
            for recursion, scripts in scriptDict.items()
            if recursion > 0
        }
        scripts = list(inheritedScripts.values())
        completeScriptList = common.joinLists(scripts)
        scriptManager.runAllScripts(completeScriptList)
        if len(completeScriptList):
            logger.info(f"{niceScriptStepName}: inherited scripts -- complete")

    def run(
        self, publish: bool = False, savePublish: bool = True, versioning: bool = True
    ) -> None:
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
        if not self.rigEnvironment:
            logger.error(
                "you must provide a build environment path. Use `_setRigFile()`"
            )
            return

        startTime = time.time()
        logger.info(
            f"\n" f"Begin Rig Build\n{'-' * 70}\n" f"build env: {self.rigEnvironment}\n"
        )

        self.runBuilderScripts(constants.PRE_SCRIPT)

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
        self.runBuilderScripts(constants.POST_SCRIPT)

        self.loadControlShapes()

        self.loadDeformationLayers()
        self.loadSkinWeights()
        self.loadDeformers()

        if publish:
            # self.optimize()
            self.runBuilderScripts(constants.PUB_SCRIPT)
            if savePublish:
                self.publish(versioning=versioning)
        endTime = time.time()
        finalTime = endTime - startTime

        logger.info(
            f"\nCompleted Rig Build \t -- time elapsed: {finalTime}\n{'-' * 70}\n"
        )

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
                includeVersion=True, version=nextVersion
            )

            topNodes = cmds.ls(assemblies=True)
            topTransformNodes = cmds.ls(topNodes, exactType="transform")
            for node in topTransformNodes:
                cmds.addAttr(
                    node,
                    longName="__version__",
                    attributeType="short",
                    defaultValue=nextVersion,
                    keyable=False,
                )
                cmds.setAttr("{}.__version__".format(node), lock=True)
                cmds.setAttr("{}.__version__".format(node), channelBox=True)

            versionPath = os.path.join(versionDirectory, versionFileName)

            # make the output directory and save the file. This will also make the directory for the main publish
            if not os.path.exists(versionDirectory):
                os.makedirs(versionDirectory)
            outputVersionPath = file.saveAs(versionPath, log=False)
            logger.info(
                "out rig versioned: {}   ({})".format(
                    versionFileName, outputVersionPath
                )
            )

        # create output directory and save
        publishPath = os.path.join(outputDirectory, outputFileName)
        file.saveAs(publishPath, log=False)
        logger.info("out rig published: {}  ({})".format(outputFileName, publishPath))

    def updateMaya(self) -> None:
        """Update maya if in an interactive session"""
        # refresh the viewport after each component is built.
        if not om2.MGlobal.mayaState():
            cmds.refresh(force=True)

    # --------------------------------------------------------------------------------
    # GET
    # --------------------------------------------------------------------------------
    def getRigEnvironment(self) -> str:
        """Get the rig environment"""
        return self.rigEnvironment

    def getRigFile(self) -> str:
        """Get the rig file"""
        return self.rigFile

    def getComponentList(self) -> List[_Component]:
        """Get a list of all components in the builder"""
        return self.componentList

    def getPublishFileInfo(self) -> Tuple[str, str]:
        """
        Get the directory and filename for the output rig file.

        :return: Tuple[str, str] - A tuple containing the directory and filename.
        :raises RuntimeError: If an output path or rig name is not provided.
        """
        outputfile = self.getAbsolutePath(self.outputFilePath)

        if path.isFile(outputfile):
            filename = outputfile.split(os.sep)[-1]
            directory = "/".join(outputfile.split(os.sep)[:-1])
        elif path.isDir(outputfile):
            directory = outputfile

            if not self.rigName:
                raise RuntimeError(
                    "Must select an output path or rig name to publish a rig"
                )

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
            if filename.startswith(self.rigName) and filename.lower().endswith(
                (".ma", ".mb")
            ):
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

        logger.warning(
            "No component: '{}' found within current build".format(name, type)
        )
        return None

    # --------------------------------------------------------------------------------
    # SET
    # --------------------------------------------------------------------------------
    def setComponents(self, components: List[_Component]) -> None:
        """
        Set the `componentList`

        :param components: list of components to set
        """
        components = common.toList(components)
        self.componentList = components

    def appendComponents(self, components: List[_Component]) -> None:
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

        rigData = abstractData.AbstractData()
        rigData.read(self.rigFile)
        data = rigData.getData()
        if "rig_env" not in data:
            rigEnvironmentPath = "../"
        else:
            rigEnvironmentPath = data["rig_env"]
        self.rigEnvironment = os.path.abspath(
            os.path.join(self.rigFile, rigEnvironmentPath)
        )

        # setup the rigamajig properties
        self.rigName = data.get(constants.RIG_NAME)
        self.archetypeParent = data.get(constants.BASE_ARCHETYPE)
        self.modelFile = data.get(constants.MODEL_FILE)
        self.jointFiles = data.get(constants.SKELETON_POS)
        self.guideFiles = data.get(constants.GUIDES)
        self.componentFiles = data.get(constants.COMPONENTS)
        self.controlShapeFiles = data.get(constants.CONTROL_SHAPES)
        self.poseReadersFiles = data.get(constants.PSD)
        self.deformLayersFile = data.get(constants.DEFORM_LAYERS)
        self.skinsFile = data.get(constants.SKINS)
        self.deformerFiles = data.get(constants.DEFORMERS)
        self.outputFilePath = data.get(constants.OUTPUT_RIG)
        self.outFileSuffix = data.get(constants.OUTPUT_FILE_SUFFIX)
        self.outputFileType = data.get(constants.OUTPUT_RIG_FILE_TYPE)

        self.localPreScripts = data.get(constants.PRE_SCRIPT)
        self.localPostScripts = data.get(constants.POST_SCRIPT)
        self.localPubScripts = data.get(constants.PUB_SCRIPT)

        # also set the rig file and rig environment into environment variables to access in other scripts if needed.
        os.environ["RIGAMJIG_FILE"] = self.rigFile
        os.environ["RIGAMJIG_ENV"] = self.rigEnvironment

        logger.info("\nRig Environment path: {0}".format(self.rigEnvironment))

    def saveRigFile(self):
        """
        Save a rig file based on current instance property values.
        """
        data = abstractData.AbstractData()
        data.read(self.rigFile)
        newData = data.getData()

        newBuilderData = {
            constants.RIG_NAME: self.rigName,
            constants.BASE_ARCHETYPE: self.archetypeParent,
            constants.MODEL_FILE: self.modelFile,
            constants.SKELETON_POS: self.jointFiles,
            constants.GUIDES: self.guideFiles,
            constants.COMPONENTS: self.componentFiles,
            constants.CONTROL_SHAPES: self.controlShapeFiles,
            constants.PSD: self.poseReadersFiles,
            constants.DEFORM_LAYERS: self.deformLayersFile,
            constants.SKINS: self.skinsFile,
            constants.DEFORMERS: self.deformerFiles,
            constants.OUTPUT_RIG: self.outputFilePath,
            constants.OUTPUT_FILE_SUFFIX: self.outFileSuffix,
            constants.OUTPUT_RIG_FILE_TYPE: self.outputFileType,
            constants.PRE_SCRIPT: self.localPreScripts,
            constants.POST_SCRIPT: self.localPostScripts,
            constants.PUB_SCRIPT: self.localPubScripts,
        }

        newData.update(newBuilderData)

        data.setData(newData)
        data.write(self.rigFile)

        logger.info(f"data saved to : {self.rigFile}")

    @staticmethod
    def getRigData(rigFile: str, key: str) -> Any:
        """
        read the data from the self.rig_file. Kept here for compatibility of old code. Should probably be deleted!

        :param rigFile: path to thr rig file to get date from
        :param key: name of the dictionary key to get the data from
        :return:
        """
        return core.getRigData(rigFile=rigFile, key=key)
