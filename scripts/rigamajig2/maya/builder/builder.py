#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: model.py
    author: masonsmigel
    date: 07/2022
    discription: This module contains our rig builder.
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

    BUILD_LOGGER_SCOPE = ["rigamajig2.maya", "rigamajig2.shared"]

    def __init__(self, rigFile=None):
        """
        Initalize the builder
        :param rigFile: path to the rig file
        """
        self.path = None

        if rigFile: self.setRigFile(rigFile)

        self.componentList = list()

        self._availableComponents = core.findComponents()

        # varibles we need
        self.topSkeletonNodes = list()

    def getAvailableComponents(self) -> typing.List[str]:
        """ Get all available components"""
        return self._availableComponents

    def getAbsoultePath(self, path) -> str:
        """
        Get the absoulte path of the given path relative to the rigEnviornment

        :param str path: Path to get relative to the rig enviornment
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
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, constants.MODEL_FILE))
        model.importModel(path)
        logger.info("Model loaded")

    def loadJoints(self, paths: str = None) -> None:
        """
         Load the joint Data to a json file

        :param str paths: list of paths Path to the json file. if none is provided use the data from the rigFile
        """
        paths = paths or self.getRigData(self.rigFile, constants.SKELETON_POS)

        for path in common.toList(paths):
            absPath = self.getAbsoultePath(path)
            rigamajig2.maya.builder.data.loadJoints(absPath)
            logger.info(f"Joints loaded : {path}")

    def saveJoints(self, fileStack: _StringList = None, method="merge") -> _StringList:

        """
        Save the joint Data to a json file

        :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
        :param str method: method of data merging to apply. Default is "merge"
        """
        #
        # path = path or self.getAbsoultePath(self.getRigData(self.rigFile, constants.SKELETON_POS))
        # guides.saveJoints(path)

        fileStack = common.toList(fileStack)
        dataToSave = rigamajig2.maya.builder.data.gatherJoints()
        savedFiles = core.performLayeredSave(dataToSave=dataToSave, fileStack=fileStack, dataType="JointData",
                                             method=method)
        if savedFiles:
            logger.info("Joint positions Saved -- complete")
            return savedFiles

    def initalize(self) -> None:
        """
        Initalize rig (this is where the user can make changes)
        """

        for cmpt in self.componentList:
            logger.info('Initalizing: {}'.format(cmpt.name))
            cmpt._initalizeComponent()

        logger.info("initalize -- complete")

    def guide(self) -> None:
        """
        guide the rig
        """

        if not cmds.objExists("guides"):
            cmds.createNode("transform", name="guides")

        for cmpt in self.componentList:
            logger.info('Guiding: {}'.format(cmpt.name))
            cmpt._guideComponent()
            if hasattr(cmpt, "guidesHierarchy") and cmpt.guidesHierarchy:
                parent = cmds.listRelatives(cmpt.guidesHierarchy, p=True)
                if parent and parent[0] == 'guides':
                    break
                cmds.parent(cmpt.guidesHierarchy, "guides")
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
        for cmpt in self.componentList:
            if cmpt.getComponenetType() == 'main.main':
                self.componentList.remove(cmpt)
                self.componentList.insert(0, cmpt)

        # now we can safely build all the components in the scene
        for cmpt in self.componentList:
            logger.info('Building: {}'.format(cmpt.name))
            cmpt._buildComponent()

            # if the component is not a main parent the cmpt.rootHierarchy to the rig
            if cmds.objExists('rig') and cmpt.getComponenetType() != 'main.main':
                if hasattr(cmpt, "rootHierarchy"):
                    if not cmds.listRelatives(cmpt.rootHierarchy, p=True):
                        cmds.parent(cmpt.rootHierarchy, 'rig')

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
        for cmpt in self.componentList:
            logger.info('Connecting: {}'.format(cmpt.name))
            cmpt._connectComponent()
            self.updateMaya()
        logger.info("connect -- complete")

    def finalize(self) -> None:
        """
        finalize rig
        """
        for cmpt in self.componentList:
            logger.info('Finalizing: {}'.format(cmpt.name))
            cmpt._finalizeComponent()
            self.updateMaya()

        # delete the guide group
        cmds.delete("guides")

        logger.info("finalize -- complete")

    def optimize(self) -> None:
        """
        optimize rig
        """
        for cmpt in self.componentList:
            logger.info('Optimizing {}'.format(cmpt.name))
            cmpt._optimizeComponent()
            self.updateMaya()
        logger.info("optimize -- complete")

    def saveComponents(self, fileStack: _StringList = None, method: str = "merge") -> _StringList:
        """
        Save out components to a file.
        This only saves compoonent settings such as name, inputs, spaces and names.

        :param str fileStack: path to the component data file
        :param str method: method of data merging to apply. Default is "merge"
        """

        # because component data is gathered from the class but saved with the name as a key
        # this needs to be done in steps. First we can define our save dictionaries using the layered save...
        componentNameList = [c.name for c in self.componentList]
        saveDict = core.performLayeredSave(dataToSave=componentNameList,
                                           fileStack=fileStack,
                                           dataType="ComponentData",
                                           method=method,
                                           doSave=False)

        # if we escape from the save then we can return
        if not saveDict:
            return

        # ... next loop throught the save dict and gather component data based on the component name.
        for dataFile in saveDict:
            componentDataObj = component_data.ComponentData()

            # loop through the list of component names
            for componentName in saveDict[dataFile]:
                cmpt = self.findComponent(name=componentName)
                componentDataObj.gatherData(cmpt)
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
        paths = paths or self.getRigData(self.rigFile, constants.COMPONENTS)

        self.setComponents(list())
        for path in common.toList(paths):
            path = self.getAbsoultePath(path)

            componentDataObj = component_data.ComponentData()
            componentDataObj.read(path)

            # look through each component and add it to the builder list
            # check before adding it so only one instance of each exists in the list
            for cmpt in componentDataObj.getKeys():
                instance = common.getFirstIndex(componentDataObj.applyData(cmpt))

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
        paths = paths or self.getRigData(self.rigFile, constants.CONTROL_SHAPES)

        for path in common.toList(paths):
            # make the path an absoulte

            absPath = self.getAbsoultePath(path)
            rigamajig2.maya.builder.data.loadControlShapes(absPath, applyColor=applyColor)
            self.updateMaya()
            logger.info(f"control shapes loaded: {path}")

    def saveControlShapes(self, fileStack: _StringList = None, method: str = 'merge') -> _StringList:
        """
        Save the control shapes

        :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
        :param str method: method of data merging to apply. Default is "merge"
        """

        allControls = rigamajig2.maya.builder.data.gatherControlShapes()
        savedFiles = core.performLayeredSave(dataToSave=allControls, fileStack=fileStack, dataType="CurveData",
                                             method=method)
        if savedFiles:
            logger.info("Control Shapes Save -- Complete")
            return savedFiles

    def loadGuideData(self, paths: str = None) -> str:
        """
        Load guide data

        :param list paths: Path to the json file. if none is provided use the data from the rigFile
        """
        paths = paths or self.getRigData(self.rigFile, constants.GUIDES)

        for path in common.toList(paths):
            absPath = self.getAbsoultePath(path)
            if rigamajig2.maya.builder.data.loadGuideData(absPath):
                logger.info(f"guides loaded: {path}")

    def saveGuideData(self, fileStack: _StringList = None, method: str = "merge") -> _StringList:
        """
        Save guides data

        :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
        :param str method: method of data merging to apply. Default is "merge"
        """
        # rigFileData = common.toList(self.getAbsoultePath(self.getRigData(self.rigFile, constants.GUIDES)))[-1]
        # path = path or rigFileData
        fileStack = common.toList(fileStack)
        dataToSave = rigamajig2.maya.builder.data.gatherGuides()
        savedFiles = core.performLayeredSave(dataToSave=dataToSave, fileStack=fileStack, dataType="GuideData",
                                             method=method)
        if savedFiles:
            logger.info("Guides Save  -- complete")
            return savedFiles

    def loadPoseReaders(self, paths: str = None, replace: bool = True) -> None:
        """
        Load pose readers

        :param list paths: Path to the json file. if none is provided use the data from the rigFile
        :param replace: Replace existing pose readers.
        """
        paths = paths or self.getRigData(self.rigFile, constants.PSD) or ''

        for path in common.toList(paths):
            absPath = self.getAbsoultePath(path)
            if rigamajig2.maya.builder.data.loadPoseReaders(absPath, replace=replace):
                logger.info(f"pose readers loaded: {path}")

    def savePoseReaders(self, fileStack: _StringList = None, method: str = "merge") -> _StringList:
        """
        Save out pose readers

        :param str fileStack: Path to the json file. if none is provided use the data from the rigFile.
        :param str method: method of data merging to apply. Default is "merge"
        """
        # path = path or self.getAbsoultePath(self.getRigData(self.rigFile, constants.PSD))

        allPsds = rigamajig2.maya.builder.data.gatherPoseReaders()
        savedFiles = core.performLayeredSave(dataToSave=allPsds, fileStack=fileStack, dataType="PSDData",
                                             method="merge")
        # deform._savePoseReaders(path)
        if savedFiles:
            logger.info("Pose Readers Save -- Complete")
            return savedFiles

    def loadDeformationLayers(self, path: str = None) -> None:
        """
        Load the deformation layers

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, constants.DEFORM_LAYERS)) or ''
        if rigamajig2.maya.builder.data.loadDeformLayers(path):
            logger.info("deformation layers loaded")

    def saveDeformationLayers(self, path: str = None) -> None:
        """
        Load the deformation layers

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, constants.DEFORM_LAYERS)) or ''
        rigamajig2.maya.builder.data.saveDeformLayers(path)
        logger.info("deformation layers saved to: {}".format(path))

    def mergeDeformLayers(self) -> None:
        """Merge all deformation layers for all models"""
        import rigamajig2.maya.rig.deformLayer as deformLayer

        if len(meta.getTagged("hasDeformLayers")) > 0:
            for model in meta.getTagged("hasDeformLayers"):
                layer = deformLayer.DeformLayer(model)
                layer.stackDeformLayers(cleanup=True)

            logger.info("deformation layers merged")

    def loadSkinWeights(self, path: str = None) -> None:
        """
        Load the skin weights

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, constants.SKINS)) or ''
        if rigamajig2.maya.builder.data.loadSkinWeights(path):
            logger.info("skin weights loaded")

    def saveSkinWeights(self, path: str = None) -> None:
        """
        Save the skin weights

        :param str path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, constants.SKINS)) or ''
        rigamajig2.maya.builder.data.saveSkinWeights(path)
        logger.info("skin weights for: {} saved to:{}".format(cmds.ls(sl=True), path))

    def loadDeformers(self, paths: _StringList = None) -> None:
        """ Load additional deformers
        :param list paths: Path to the json file. if none is provided use the data from the rigFile
        """
        if not paths:
            deformerPaths = self.getRigData(self.rigFile, constants.DEFORMERS) or []
            shapesPaths = self.getRigData(self.rigFile, constants.SHAPES) or []

            # if we have both deformerPaths and shapesPaths we need to join the two paths
            paths = common.toList(shapesPaths) + common.toList(deformerPaths)

        for path in common.toList(paths):
            absPath = self.getAbsoultePath(path)
            if rigamajig2.maya.builder.data.loadDeformer(absPath):
                logger.info(f"deformers loaded: {path}")

    # TODO: Fix this or delete it.
    def deleteComponents(self, clearList=True):
        """
        Delete all components

        :param bool clearList: clear the builder component list
        """
        mainComponent = None
        for cmpt in self.componentList:
            if cmds.objExists(cmpt.container):
                if cmpt.getComponenetType() == 'main.main':
                    mainComponent = cmpt
                else:
                    cmpt.deleteSetup()
        if mainComponent:
            mainComponent.deleteSetup()
        if clearList:
            self.componentList = list()

    # TODO: Fix this or delete it.
    def buildSingleComponent(self, name, type):
        """
        Build a single component based on the name and component type.
        If a component with the given name and type exists within the self.cmpt_list build that component.

        Warning: Building a single component without nesseary connection nodes in the scene may lead to unpredicable results. ONLY USE THIS FOR RND!

        :param name: name of the component to build
        :param type: type of the component to build
        :return:
        """
        cmpt = self.findComponent(name=name, type=type)

        if cmpt:
            cmpt._intialize_cmpt()
            cmpt._build_cmpt()
            cmpt._connect_cmpt()
            cmpt._finalize_cmpt()

            if cmds.objExists('rig') and cmpt.getComponenetType() != 'main.Main':
                if hasattr(cmpt, "rootHierarchy"):
                    if not cmds.listRelatives(cmpt.rootHierarchy, p=True):
                        cmds.parent(cmpt.rootHierarchy, 'rig')

            logger.info("build: {} -- complete".format(cmpt.name))

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

    def run(self, publish: bool = False, savePublish: bool = True, outputfile: str = None, assetName: str = None,
            suffix: str = None, fileType: str = None, versioning: bool = True, replaceLog: bool = True) -> float:
        """
        Build a rig.

        if Publish is True then it will also run the publish steps. See publish for more information.

        :param publish: if True also run the publish steps
        :param savePublish: if True also save the publish file
        :param outputfile: Path for the output file.
        :param assetName: Asset name used to generate a file name.
        :param suffix: suffix to attatch to the end of the asset name.
        :param fileType: File type of the publish file. valid values are 'mb' or 'ma'.
        :param versioning: Enable versioning. Versioning will create a separate file within the publish directory
                           and store a new version each time the publish file is overwritten.
                           This allows the user to keep a log of files approved to be published.
        :param replaceLog: If True, replace the existing log file. otherwise, append to it.
        """
        if not self.path:
            logger.error('you must provide a build envifornment path. Use Bulder._setRigFile()')
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
        self.initalize()
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
                self.publish(outputfile=outputfile,
                             suffix=suffix,
                             assetName=assetName,
                             fileType=fileType,
                             versioning=versioning
                             )
        endTime = time.time()
        finalTime = endTime - startTime

        logger.info('\nCompleted Rig Build \t -- time elapsed: {0}\n{1}\n'.format(finalTime, '-' * 70))

    # UTILITY FUNCTION TO PUBLISH THE RIG
    def publish(self, outputfile: str = None, suffix: str = None, assetName: str = None, fileType: str = None,
                versioning: bool = True) -> None:
        """
        Publish a rig.

        This will run the whole builder as well as create a publish file.

        :param outputfile: Path for the output file
        :param suffix: the file suffix to add to the rig file
        :param assetName: Asset name used to generate a file name
        :param fileType: File type of the publish file. valid values are 'mb' or 'ma'
        :param versioning: Enable versioning. Versioning will create a separate file within the publish directory
                           and store a new version each time the publish file is overwritten.
                           This allows the user to keep a log of files approved to be published.
        """
        outputfile = outputfile or self.getAbsoultePath(self.getRigData(self.rigFile, constants.OUTPUT_RIG))
        assetName = assetName or self.getAbsoultePath(self.getRigData(self.rigFile, constants.RIG_NAME))
        fileType = fileType or self.getRigData(self.rigFile, constants.OUTPUT_RIG_FILE_TYPE)
        suffix = suffix or self.getRigData(self.rigFile, constants.OUTPUT_FILE_SUFFIX)

        suffix = suffix or str()
        # check if the provided path is a file path.
        # if so use the file naming and extension from the provided path
        if rig_path.isFile(outputfile):
            fileName = outputfile.split(os.sep)[-1]
            dirName = '/'.join(outputfile.split(os.sep)[:-1])

        # if only a directory is provided than generate a filename using the rig name and file extension
        else:
            dirName = outputfile
            if assetName:
                rigName = self.getRigData(self.rigFile, constants.RIG_NAME)
                fileName = "{}{}.{}".format(rigName, suffix, fileType)
            else:
                raise RuntimeError("Must select an output path or character name to publish a rig")

        # if we want to save a version as well
        if versioning:
            # get the version directory, file
            versionDir = os.path.join(dirName, 'versions')
            filebase = ".".join(fileName.split('.')[:-1])
            fileext = fileName.split('.')[-1]

            # format the new file name and file path
            versionFile = "{}_{}.{}".format(filebase, 'v000', fileext)
            versionPath = os.path.join(versionDir, versionFile)

            # get a list of previous publishes to determine the proper version for this file

            if os.path.exists(versionDir):
                versionDirContents = os.listdir(versionDir)
                numberOfPublishes = len([x for x in versionDirContents if x.endswith(".{}".format(fileext))])
            else:
                numberOfPublishes = 0

            topNodes = cmds.ls(assemblies=True)
            topTransformNodes = cmds.ls(topNodes, exactType='transform')
            for node in topTransformNodes:
                # set the version to the number of publishes (plus one) to account for the version we are about to publish
                cmds.addAttr(node, longName="__version__", attributeType='short', dv=numberOfPublishes + 1, k=False)
                cmds.setAttr("{}.__version__".format(node), lock=True)
                cmds.setAttr("{}.__version__".format(node), cb=True)

            # make the output directory and save the file. This will also make the directory for the main publish
            rig_path.mkdir(versionDir)
            versionPath = file.incrimentSave(versionPath, log=False)
            logger.info("out rig versioned: {}   ({})".format(os.path.basename(versionPath), versionPath))

        # create output directory and save
        publishPath = os.path.join(dirName, fileName)
        file.saveAs(publishPath, log=False)
        logger.info("out rig published: {}  ({})".format(fileName, publishPath))

    def updateMaya(self) -> None:
        """ Update maya if in an interactive session"""
        # refresh the viewport after each component is built.
        if not om2.MGlobal.mayaState():
            cmds.refresh(f=True)

    # --------------------------------------------------------------------------------
    # GET
    # --------------------------------------------------------------------------------
    def getRigEnviornment(self) -> str:
        """Get the rig enviornment"""
        return self.path

    def getRigFile(self) -> str:
        """Get the rig file"""
        return self.rigFile

    def getComponentList(self) -> typing.List[Component]:
        """Get a list of all components in the builder"""
        return self.componentList

    def getComponentFromContainer(self, container: str) -> Component:
        """
        Get the component object from a container name
        :param container: name of the container to get the component for
        :return: component object
        """
        name = cmds.getAttr("{}.name".format(container))
        componentType = cmds.getAttr("{}.type".format(container))

        return self.findComponent(name, componentType)

    def findComponent(self, name: str, type: str = None) -> Component:
        """
        Find a component within the self.componentList.
        :param name: name of the component to find
        :param type: type of the component to find
        :return: component object
        """
        for cmpt in self.componentList:
            _name = cmpt.name
            _type = cmpt.componentType
            if name == _name:
                if not type:
                    return cmpt
                elif type == _type:
                    return cmpt
        logger.warning("No component: {} with type: {} found within current build".format(name, type))
        return None

    # --------------------------------------------------------------------------------
    # SET
    # --------------------------------------------------------------------------------
    def setComponents(self, cmpts: typing.List[Component]) -> None:
        """
        Set the self.cmpt_list

        :param cmpts: list of components to set
        """
        cmpts = common.toList(cmpts)
        self.componentList = cmpts

    def appendComponents(self, cmpts: typing.List[Component]) -> None:
        """
        append a component

        :param cmpts: list of components to append
        """
        cmpts = common.toList(cmpts)
        for cmpt in cmpts:
            self.componentList.append(cmpt)

    def setRigFile(self, rigFile: str) -> None:
        """
        Set the rig file.
        This will update the self.rigFile and self.path variables

        :param rigFile: Path of the rig file to set.
        """
        if not os.path.exists(rigFile):
            raise RuntimeError("'{0}' does not exist".format(rigFile))
        self.rigFile = rigFile

        rigData = abstract_data.AbstractData()
        rigData.read(self.rigFile)
        data = rigData.getData()
        if "rig_env" not in data:
            rigEnviornmentPath = '../'
        else:
            rigEnviornmentPath = data["rig_env"]
        self.path = os.path.abspath(os.path.join(self.rigFile, rigEnviornmentPath))

        # also set the rig file and rig enviornment into eniviornment varriables to access in other scripts if needed.
        os.environ['RIGAMJIG_FILE'] = self.rigFile
        os.environ['RIGAMJIG_ENV'] = self.path

        logger.info('\nRig Enviornment path: {0}'.format(self.path))

    def saveRigFile(self, dataDict):
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
        read the data from the self.rig_file. Kept here for compatability of old code. Should probably be deleted!

        :param rigFile: path to thr rig file to get date from
        :param key: name of the dictionary key to get the data from
        :return:
        """
        return core.getRigData(rigFile=rigFile, key=key)
