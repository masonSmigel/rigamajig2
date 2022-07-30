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

# PYTHON
import os
import time
import inspect
import logging
from collections import OrderedDict

# MAYA
import maya.cmds as cmds
import maya.api.OpenMaya as om2

# RIGAMAJIG
import rigamajig2.shared.common as common
import rigamajig2.shared.path as rig_path
import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.file as file
import rigamajig2.maya.meta as meta

# BUILDER
import rigamajig2.maya.rig_builder.model as model
import rigamajig2.maya.rig_builder.guides as guides
import rigamajig2.maya.rig_builder.controlShapes as controlShapes
import rigamajig2.maya.rig_builder.deform as deform
import rigamajig2.maya.rig_builder.builderUtils as builderUtils

logger = logging.getLogger(__name__)

CMPT_PATH = os.path.abspath(os.path.join(__file__, '../../cmpts'))

_EXCLUDED_FOLDERS = ['face']
_EXCLUDED_FILES = ['__init__.py', 'base.py']

# BUILD ENVIORNMENT GLOBLALS
PRE_SCRIPT = 'pre_script'
POST_SCRIPT = 'post_script'
PUB_SCRIPT = 'pub_script'

# RIG FILE KEYS
RIG_NAME = 'rig_name'
MODEL_FILE = "model_file"
SKELETON_FILE = "skeleton_file"
SKELETON_POS = "skeleton_pos"
CONTROL_SHAPES = "control_shapes"
GUIDES = "guides"
COMPONENTS = "components"
SKINS = 'skins'
PSD = 'psd'
OUTPUT_RIG = 'output_file'
OUTPUT_RIG_FILE_TYPE = 'output_file_type'


# pylint:disable=too-many-public-methods
class Builder(object):
    """
    The builder is the foundational class used to construct rigs with Rigamajig2.
    """
    def __init__(self, rigFile=None):
        """
        Initalize the builder
        :param rigFile: path to the rig file
        """
        self.path = None
        self.setRigFile(rigFile)
        self.componentList = list()

        self._availableComponents = builderUtils._lookForComponents(CMPT_PATH, _EXCLUDED_FOLDERS, _EXCLUDED_FILES)
        # self.__lookForComponents(CMPT_PATH)

        # varibles we need
        self.topSkeletonNodes = list()
        self.loadComponentsFromFile = False

    def getAvailableComponents(self):
        """ Get all available components"""
        return self._availableComponents

    def getComponentRefDict(self):
        """
        Get the component reference dictionary
        :return:
        """
        return builderUtils._lookForComponents(CMPT_PATH, _EXCLUDED_FOLDERS, _EXCLUDED_FILES)

    def getAbsoultePath(self, path):
        """
        Get the absoulte path of the given path relative to the rigEnviornment
        :param path:
        :return:
        """
        if path:
            path = common.getFirstIndex(path)
            return os.path.realpath(os.path.join(self.path, path))

    # --------------------------------------------------------------------------------
    # RIG BUILD STEPS
    # --------------------------------------------------------------------------------
    def importModel(self, path=None):
        """
        Import the model file
        :param path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, MODEL_FILE))
        model.importModel(path)
        logger.info("Model loaded")

    def loadJoints(self, path=None):
        """
         Load the joint Data to a json file
        :param path: Path to the json file. if none is provided use the data from the rigFile
        :return:
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, SKELETON_POS))
        guides.loadJoints(path)
        logger.info("Joints loaded")

    def saveJoints(self, path=None):
        """
        Save the joint Data to a json file
        :param path: Path to the json file. if none is provided use the data from the rigFile
        :return:
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, SKELETON_POS))
        guides.saveJoints(path)
        logger.info("Joint positions saved to: {}".format(path))

    def initalize(self):
        """Initalize rig (this is where the user can make changes)"""
        if not cmds.objExists("guides"):
            cmds.createNode("transform", name="guides")

        for cmpt in self.componentList:
            logger.info('Initalizing: {}'.format(cmpt.name))
            cmpt._initalizeComponent()
            if hasattr(cmpt, "guidesHierarchy") and cmpt.guidesHierarchy:
                parent = cmds.listRelatives(cmpt.guidesHierarchy, p=True)
                if parent and parent[0] == 'guides':
                    break
                cmds.parent(cmpt.guidesHierarchy, "guides")
            self.updateMaya()

        self.loadGuideData()
        logger.info("initalize -- complete")

    def build(self):
        """build rig"""
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
            if not cmds.listRelatives(topSkeletonNodes, p=True):
                cmds.parent(topSkeletonNodes, 'bind')

        # if the model group exists. parent the model
        if cmds.objExists('model'):
            topModelNodes = meta.getTagged('model_root')
            if not cmds.listRelatives(topModelNodes, p=True):
                cmds.parent(topModelNodes, 'model')

        logger.info("build -- complete")

    def connect(self):
        """connect rig"""
        for cmpt in self.componentList:
            logger.info('Connecting: {}'.format(cmpt.name))
            cmpt._connectComponent()
            self.updateMaya()
        logger.info("connect -- complete")

    def finalize(self):
        """finalize rig"""
        for cmpt in self.componentList:
            logger.info('Finalizing: {}'.format(cmpt.name))
            cmpt._finalizeComponent()
            self.updateMaya()

        # delete the guide group
        cmds.delete("guides")

        logger.info("finalize -- complete")

    def optimize(self):
        """optimize rig"""
        for cmpt in self.componentList:
            logger.info('Optimizing {}'.format(cmpt.name))
            cmpt._optimizeComponent()
            self.updateMaya()
        logger.info("optimize -- complete")

    def saveComponents(self, path=None):
        """
        Save out components to a file.
        This only saves compoonent settings such as name, inputs, spaces and names.
        :param path: path to the component data file
        :return:
        """
        if not path:
            path = self.getAbsoultePath(self.getRigData(self.rigFile, COMPONENTS))

        componentData = OrderedDict()
        componentDataObj = abstract_data.AbstractData()
        for cmpt in self.componentList:
            componentData[cmpt.name] = cmpt.getComponentData()

        componentDataObj.setData(componentData)
        componentDataObj.write(path)
        logger.info("Components saved to: {}".format(path))

    def loadComponents(self, path=None):
        """
        Load components from a json file. This will only load the component settings and objects.
        :param path: Path to the json file. if none is provided use the data from the rigFile
        :return:
        """
        if not path:
            path = self.getAbsoultePath(self.getRigData(self.rigFile, COMPONENTS))
        componentDataObje = abstract_data.AbstractData()
        componentDataObje.read(path)
        componentData = componentDataObje.getData()

        self.setComponents(list())
        for cmpt in list(componentData.keys()):

            # dynamically load component module into python
            moduleName = componentData[cmpt]['type']

            cmptDict = self.getComponentRefDict()
            if moduleName not in list(cmptDict.keys()):
                # This is a work around to account for the fact that some old .rig files use the cammel cased components
                module, cls = moduleName.split('.')
                newClass = cls[0].lower() + cls[1:]
                tempModuleName = module + "." + newClass
                if tempModuleName in list(cmptDict.keys()):
                    moduleName = tempModuleName

            modulePath = cmptDict[moduleName][0]
            className = cmptDict[moduleName][1]
            moduleObject = __import__(modulePath, globals(), locals(), ["*"], 0)

            componentClass = getattr(moduleObject, className)
            instance = componentClass(componentData[cmpt]['name'], componentData[cmpt]['input'])
            self.appendComponents(instance)
            self.loadComponentsFromFile = True

        logger.info("components loaded -- complete")

    def loadComponentSettings(self, path=None):
        """
        loadSettings component settings from the rig builder
        :param path: Path to the json file. if none is provided use the data from the rigFile
        :return:
        """
        if not path:
            path = self.getAbsoultePath(self.getRigData(self.rigFile, COMPONENTS))

        if self.loadComponentsFromFile:
            componentDataObj = abstract_data.AbstractData()
            componentDataObj.read(path)
            componentData = componentDataObj.getData()
            for cmpt in self.componentList:
                cmpt.loadSettings(componentData[cmpt.name])

    def loadMetadataToComponentSettings(self):
        """
        Load the metadata stored on the container attributes to the component objects.
        :return:
        """
        for cmpt in self.componentList:
            cmpt._loadComponentParametersToClass()

    def loadControlShapes(self, path=None, applyColor=True):
        """
        Load the control shapes
        :param path: Path to the json file. if none is provided use the data from the rigFile
        :param applyColor: Apply the control colors.
        :return:
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, CONTROL_SHAPES))
        controlShapes.loadControlShapes(path, applyColor=applyColor)
        logger.info("control shapes -- complete")

    def saveControlShapes(self, path=None):
        """
        Save the control shapes
        :param path: Path to the json file. if none is provided use the data from the rigFile
        :return:
"""
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, CONTROL_SHAPES))
        controlShapes.saveControlShapes(path)
        logger.info("control shapes saved to: {}".format(path))

    def loadGuideData(self, path=None):
        """
        Load guide data
        :return:
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, GUIDES))
        if guides.loadGuideData(path):
            logger.info("guides loaded")

    def saveGuideData(self, path=None):
        """
        Save guides data
        :param path: Path to the json file. if none is provided use the data from the rigFile
        :return:
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, GUIDES))
        guides.saveGuideData(path)
        logger.info("guides saved to: {}".format(path))

    def loadPoseReaders(self, path=None, replace=True):
        """
        Load pose readers
        :param path: Path to the json file. if none is provided use the data from the rigFile
        :param replace: Replace existing pose readers.
        """

        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, PSD)) or ''
        if deform.loadPoseReaders(path, replace=replace):
            logger.info("pose readers loaded")

    def savePoseReaders(self, path=None):
        """
        Save out pose readers
        :param path: Path to the json file. if none is provided use the data from the rigFile.
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, PSD))
        deform.savePoseReaders(path)
        logger.info("pose readers saved to: {}".format(path))

    def loadDeformationData(self):
        """
        Load other data, this is stuff like skinweights, blendshapes, clusters etc.
        :return:
        """
        self.loadSkinWeights()
        logger.info("data loading -- complete")

    def loadSkinWeights(self, path=None):
        """
        Load the skin weights
        :param path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, SKINS)) or ''
        if deform.loadSkinWeights(path):
            logger.info("skin weights loaded")

    def saveSkinWeights(self, path=None):
        """
        Save the skin weights
        :param path: Path to the json file. if none is provided use the data from the rigFile
        """
        path = path or self.getAbsoultePath(self.getRigData(self.rigFile, SKINS)) or ''
        deform.saveSkinWeights(path)

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

    def buildSingleComponent(self, name, type):
        """
        Build a single component based on the name and component type.
        If a component with the given name and type exists within the self.cmpt_list build that component.

        Warning: Building a single component without nesseary connection nodes in the scene may lead to
                 unpredicable results. ONLY USE THIS FOR RND!
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
    def preScript(self):
        """ Run pre scripts. use  through the PRE SCRIPT path"""
        builderUtils.runAllScripts(self.getAbsoultePath(self.getRigData(self.rigFile, PRE_SCRIPT)))
        logger.info("pre scripts -- complete")

    def postScript(self):
        """ Run pre scripts. use  through the POST SCRIPT path"""
        builderUtils.runAllScripts(self.getAbsoultePath(self.getRigData(self.rigFile, POST_SCRIPT)))
        logger.info("post scripts -- complete")

    def publishScript(self):
        """ Run pre scripts. use  through the PUB SCRIPT path"""
        builderUtils.runAllScripts(self.getAbsoultePath(self.getRigData(self.rigFile, PUB_SCRIPT)))
        logger.info("publish scripts -- complete")

    # ULITITY FUNCTION TO BUILD THE ENTIRE RIG
    def run(self, publish=False, outputfile=None, assetName=None, fileType=None, versioning=True):
        """
        Build a rig.

        if Publish is True then it will also run the publish steps. See publish for more information.

        :param publish: if True also publish the rig.
        :param outputfile: Path for the output file.
        :param assetName: Asset name used to generate a file name.
        :param fileType: File type of the publish file. valid values are 'mb' or 'ma'.
        :param versioning: Enable versioning. Versioning will create a separate file within the publish directory
                           and store a new version each time the publish file is overwritten.
                           This allows the user to keep a log of files approved to be published.
        :return:
        """
        if not self.path:
            logger.error('you must provide a build enviornment path. Use Bulder.setRigFile()')
            return

        startTime = time.time()
        print('\nBegin Rig Build\n{0}\nbuild env: {1}\n'.format('-' * 70, self.path))
        builderUtils.loadRequiredPlugins()
        self.preScript()
        self.importModel()
        self.loadJoints()
        self.loadComponents()
        self.initalize()
        self.loadComponentSettings()
        self.build()
        self.connect()
        self.finalize()
        self.loadPoseReaders()
        self.postScript()
        self.loadControlShapes()
        self.loadDeformationData()
        if publish:
            self.publishScript()
            self.publish(outputfile=outputfile, assetName=assetName, fileType=fileType, versioning=versioning)
        endTime = time.time()
        finalTime = endTime - startTime

        print('\nCompleted Rig Build \t -- time elapsed: {0}\n{1}\n'.format(finalTime, '-' * 70))

    # UTILITY FUNCTION TO PUBLISH THE RIG
    def publish(self, outputfile=None, assetName=None, fileType=None, versioning=True):
        """
        Publish a rig.

        This will run the whole builder as well as create a publish file.

        :param outputfile: Path for the output file
        :param assetName: Asset name used to generate a file name
        :param fileType: File type of the publish file. valid values are 'mb' or 'ma'
        :param versioning: Enable versioning. Versioning will create a separate file within the publish directory
                           and store a new version each time the publish file is overwritten.
                           This allows the user to keep a log of files approved to be published.
        :return:
        """

        outputfile = outputfile or self.getAbsoultePath(self.getRigData(self.rigFile, OUTPUT_RIG))
        assetName = assetName or self.getAbsoultePath(self.getRigData(self.rigFile, RIG_NAME))
        fileType = fileType or self.getAbsoultePath(self.getRigData(self.rigFile, OUTPUT_RIG_FILE_TYPE))

        # check if the provided path is a file path.
        # if so use the file naming and extension from the provided path
        if rig_path.isFile(outputfile):
            fileName = outputfile.split(os.sep)[-1]
            dirName = '/'.join(outputfile.split(os.sep)[:-1])

        # if only a directory is provided than generate a filename using the rig name and file extension
        else:
            dirName = outputfile
            if assetName:
                rigName = self.getRigData(self.rigFile, RIG_NAME)
                fileName = "{}_{}.{}".format(rigName, 'rig', fileType)
            else:
                raise RuntimeError("Must select an output path or character name to publish a rig")

        # create output directory and save
        rig_path.mkdir(dirName)
        publishPath = os.path.join(dirName, fileName)
        file.saveAs(publishPath, log=False)
        logger.info("out rig published: {}".format(publishPath))

        # if we want to save a version as well
        if versioning:
            # get the version directory, file
            versionDir = os.path.join(dirName, 'versions')
            filebase = ".".join(fileName.split('.')[:-1])
            fileext = fileName.split('.')[-1]

            # format the new file name and file path
            versionFile = "{}_{}.{}".format(filebase, 'v000', fileext)
            versionPath = os.path.join(versionDir, versionFile)

            # make the output directory and save the file
            rig_path.mkdir(versionDir)
            versionPath = file.incrimentSave(versionPath, log=False)
            logger.info("out rig archived: {}".format(versionPath))

    def updateMaya(self):
        """ Update maya if in an interactive session"""
        # refresh the viewport after each component is built.
        if not om2.MGlobal.mayaState():
            cmds.refresh(f=True)

    # --------------------------------------------------------------------------------
    # GET
    # --------------------------------------------------------------------------------
    def getRigEnviornment(self):
        """Get the rig enviornment"""
        return self.path

    def getRigFile(self):
        """Get the rig file"""
        return self.rigFile

    def getComponentList(self):
        """Get a list of all components in the builder"""
        return self.componentList

    def getComponentFromContainer(self, container):
        """
        Get the component object from a container name
        :param container: name of the container to get the component for
        :return: component object
        """
        name = cmds.getAttr("{}.name".format(container))
        componentType = cmds.getAttr("{}.type".format(container))

        return self.findComponent(name, componentType)

    def findComponent(self, name, type):
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
                if type == _type:
                    return cmpt
        logger.warning("No component: {} with type: {} found within current build".format(name, cmpt_type))
        return None

    # --------------------------------------------------------------------------------
    # SET
    # --------------------------------------------------------------------------------
    def setComponents(self, cmpts):
        """
        Set the self.cmpt_list
        :param cmpts: list of components to set
        """
        cmpts = common.toList(cmpts)
        self.componentList = cmpts

    def appendComponents(self, cmpts):
        """
        append a component
        :param cmpts: list of components to append
        :return:
        """
        cmpts = common.toList(cmpts)
        for cmpt in cmpts:
            self.componentList.append(cmpt)

    def setRigFile(self, rigFile):
        """
        Set the rig file.
        This will update the self.rigFile and self.path variables
        :param rigFile: Path of the rig file to set.
        :return:
        """
        if not rigFile:
            self.rigFile = None
            return

        if not os.path.exists(rigFile):
            # TODO: give the user the option to create a rig file somewhere
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
        logger.info('\n\nRig Enviornment path: {0}'.format(self.path))

    @staticmethod
    def getRigData(rigFile, key):
        """
        read the data from the self.rig_file
        :param rigFile:
        :param key:
        :return:
        """
        if not rigFile:
            return None

        if not os.path.exists(rigFile):
            raise RuntimeError('rig file at {} does not exist'.format(rigFile))

        data = abstract_data.AbstractData()
        data.read(rigFile)
        if key in data.getData():
            return data.getData()[key]
        return None
