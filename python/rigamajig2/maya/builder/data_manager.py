#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: data_manager.py
    author: masonsmigel
    date: 08/2023
    description: 

"""
import logging
import os
import typing

from maya import cmds as cmds

from rigamajig2.maya import joint
from rigamajig2.maya import meta
from rigamajig2.maya import skinCluster
from rigamajig2.maya.builder import core
from rigamajig2.maya.builder.constants import DEFORMER_DATA_TYPES
from rigamajig2.maya.data import (psd_data,
                                  skin_data,
                                  deformLayer_data,
                                  joint_data,
                                  curve_data,
                                  guide_data,
                                  abstract_data,
                                  component_data
                                  )
from rigamajig2.maya.rig import psd
from rigamajig2.shared import common
from rigamajig2.shared import path
from rigamajig2.ui.widgets import mayaMessageBox

logger = logging.getLogger(__name__)

CHANGED = "changed"
ADDED = "added"
REMOVED = "removed"

DATA_MERGE_METHODS = ['new', 'merge', 'overwrite']

LayeredDataInfoDict = typing.Dict[str, typing.Dict[str, typing.List]]

_StringList = typing.List[str]
_Builder = typing.Type["Builder"]


def gatherLayeredSaveData(dataToSave, fileStack, dataType, method="merge", fileName=None) -> LayeredDataInfoDict:
    """
    gather data for a layered data save. This can be used on nearly any node data class to save a list of data into the
    source files where they originally came from. If the node data appears in multiple files it will be saved in the
    lowest file to preserve inheritance.

    There are several methods to append new node data that has been added since the previous save.

    new - new data is added to a new file at the bottom of the file stack
    merge - new data is merged onto the file at the bottom of the file stack
    overwrite - all data is saved into a new file at the bottom of the file stack

    :param dataToSave: List of nodes to save data from
    :param fileStack: list of file from which we're currently reading data from
    :param dataType: Datatype to save.
    :param method: method to append new data. Available options are [new, merge, overwrite]
    :param fileName: if using new file method provide a file to save new data to
    :return: dictonary containing info about all nodes added, changed and removed from each file.
    """

    dataModules = list(core.getDataModules(core.DATA_PATH).keys())
    if dataType not in dataModules:
        raise ValueError(f"Data type {dataType} is not valid. Valid Types are {dataModules}")

    if method not in ['new', 'merge', 'overwrite']:
        raise ValueError(f"Merge method '{method}' is not valid. Use {DATA_MERGE_METHODS}")

    fileStack = common.toList(fileStack)

    # sometimes we may want to save other data types into a different data loader.
    # Here we need to filter only files of the data type we want
    filteredFileStack = []
    for dataFile in fileStack:
        dataFileType = abstract_data.AbstractData.getDataType(dataFile)
        if dataFileType == dataType or dataFileType == "AbstractData":
            filteredFileStack.append(dataFile)

    # first lets get a list of all the nodes that has been previously saved
    # we can save that into a dictionary with the file they came from and a list to compare to the new data.
    # (check for deleted/missing nodes)
    sourceNodesDict = dict()
    sourceNodesList = set()
    for dataFile in filteredFileStack:
        dataClass = core.createDataClassInstance(dataType=dataType)
        dataClass.read(dataFile)
        nodes = dataClass.getKeys()
        sourceNodesDict[dataFile] = nodes

        sourceNodesList.update(nodes)

    # since we want to replace values from the bottom of the stack first we need to reverse our file-stack
    searchFileStack = filteredFileStack.copy()
    searchFileStack.reverse()

    # work on saving the node data of nodes that have been saved first. build a source dictionary to save this data to
    layeredDataInfo = dict()
    for dataFile in filteredFileStack:
        layeredDataInfo[dataFile] = {CHANGED: [], ADDED: [], REMOVED: []}

    # we also need to build a list of nodes that we have already saved.
    previouslySavedNodes = list()

    for dataFile in searchFileStack:
        nodesPreviouslyInFile = sourceNodesDict[dataFile]
        for node in nodesPreviouslyInFile:
            if node in dataToSave:
                # if we have already saved the node we can skip it!
                if node in previouslySavedNodes:
                    continue
                layeredDataInfo[dataFile][CHANGED].append(node)
                previouslySavedNodes.append(node)
            else:
                layeredDataInfo[dataFile][REMOVED].append(node)

    # get the difference of lists for the unsaved nodes and deleted nodes
    unsavedNodes = set(dataToSave) - set(previouslySavedNodes)

    # now we need to do something with the new nodes!
    if method == 'merge':
        layeredDataInfo[searchFileStack[0]][ADDED] += unsavedNodes

    if method == 'new':
        if not fileName:
            raise Exception("Please provide a file path to save data to a new file")

        layeredDataInfo[fileName][ADDED] += unsavedNodes

    if method == 'overwrite':
        # save the data to the new filename
        if not fileName:
            raise UserWarning("Must specify an override file if one is not proved.")

        # next we need to clear out the added or changed data.
        # keep anything added to removed because we cant delete data later.
        for key in layeredDataInfo:
            layeredDataInfo[key][CHANGED] = []
            layeredDataInfo[key][ADDED] = []

        # add all data to a new key.
        layeredDataInfo[fileName] = {CHANGED: [], ADDED: dataToSave, REMOVED: []}

    return layeredDataInfo


def validateLayeredSaveData(layeredDataInfo: LayeredDataInfoDict) -> bool:
    """
    Validate that the dictionary provided is prepared to be saved as a layeredDataDict
    :param layeredDataInfo: dictonary of layered data info to process the files with. generated using gatherLayeredSaveData
    :return:
    """
    if not layeredDataInfo:
        return False

    resultsList = list()
    for file in layeredDataInfo:
        resultsList.append(all(key in layeredDataInfo[file] for key in [CHANGED, ADDED, REMOVED]))

    return all(resultsList)


def layeredSavePrompt(layeredDataInfo: LayeredDataInfoDict, dataType: str) -> bool:
    """
    Bring up the prompt with info about the layered save.

    :param layeredDataInfo: dictonary of layered data info to process the files with. generated using gatherLayeredSaveData
    :param dataType: Datatype to save.
    :return: result of the popup dialog
    """
    tab = "    "
    message = str()

    totalNodesToSave = 0

    if not validateLayeredSaveData(layeredDataInfo=layeredDataInfo):
        raise TypeError("Dictionary provided is not a valid layeredSaveInfo")

    for dataFile in layeredDataInfo.keys():
        numberChangedNodes = len(layeredDataInfo[dataFile][CHANGED])
        numberAddedNodes = len(layeredDataInfo[dataFile][ADDED])
        numberRemovedNodes = len(layeredDataInfo[dataFile][REMOVED])

        message += f"\n{os.path.basename(dataFile)}: {numberChangedNodes + numberAddedNodes} nodes"

        if numberAddedNodes:
            message += f"\n{tab}New Nodes: {numberAddedNodes}"
        if numberRemovedNodes:
            message += f"\n{tab}Deleted Nodes: {numberRemovedNodes}"

        totalNodesToSave += numberChangedNodes
        totalNodesToSave += numberAddedNodes

    mainMessage = f"Save {totalNodesToSave} nodes to {len(layeredDataInfo.keys())} files\n" + message
    popupConfirm = mayaMessageBox.MayaMessageBox(title=f"Save {dataType}", message=mainMessage, icon="info")
    popupConfirm.setButtonsSaveDiscardCancel()

    return popupConfirm.getResult()


def performLayeredSave(saveDataDict, dataType="AbstractData", prompt=True) -> typing.List[str] or None:
    """
    Perform a layered data save.
    Takes a dictonary of filepaths that contain a dictonary of nodes added, changed and removed.
    This should be generated by the `gatherLayeredSaveData` function.

    :param saveDataDict: dictonary of layered data info to process the files with. generated using gatherLayeredSaveData
    :param dataType: Datatype to save.
    :param prompt: opens a UI prompt if maya is running with a UI
    :return: list of all files edited.
    """
    if not validateLayeredSaveData(layeredDataInfo=saveDataDict):
        raise TypeError("Dictionary provided is not a valid layeredSaveInfo")

    if prompt:
        if not layeredSavePrompt(layeredDataInfo=saveDataDict, dataType=dataType):
            return None

    for dataFile in saveDataDict:

        # read all the old data. Anything that is NOT updated it will stay the same as the previous file.
        oldDataObj = core.createDataClassInstance(dataType=dataType)
        if os.path.exists(dataFile):
            oldDataObj.read(dataFile)

        # create a dictionary with data that is updated from our scene
        newDataObj = core.createDataClassInstance(dataType=dataType)
        changedNodes = saveDataDict[dataFile][CHANGED]
        addedNodes = saveDataDict[dataFile][ADDED]
        removedNodes = saveDataDict[dataFile][REMOVED]

        newDataObj.gatherDataIterate(changedNodes)
        newDataObj.gatherDataIterate(addedNodes)

        # remove deleted nodes from the old dictionary
        oldData = oldDataObj.getData()
        for key in removedNodes:
            oldData.pop(key)
        oldDataObj.setData(oldData)

        # add the two data objects.
        mergedDataObj = oldDataObj + newDataObj

        # write out the file
        mergedDataObj.write(dataFile)

    # Get a list of all the files saved.
    filesSaved = list(saveDataDict.keys())
    return filesSaved


# Joints
def loadJointData(filepath: str = None) -> bool:
    """
    Load all joints for the builder

    :param filepath: path to joint file
    :return: True if the data was loaded. False if no data was loaded
    """
    if not path.validatePathExists(filepath):
        logger.error(f"path does not exist: {filepath}")
        return False
    if not path.isFile(filepath):
        logger.error(f"filepath {filepath} is not a file")
        return False

    dataObj = joint_data.JointData()
    dataObj.read(filepath)
    dataObj.applyAllData()

    # tag all bind joints
    for jnt in cmds.ls(f"*_{common.BINDTAG}", type='joint'):
        meta.tag(jnt, common.BINDTAG)

    dataObj.getData().keys()
    for node in cmds.ls(dataObj.getKeys(), l=True):
        # add the joint orient to all joints in the file.
        joint.addJointOrientToChannelBox(node)

        # find joints without a parent and make them a root
        if not len(node.split('|')) > 2:
            meta.tag(node, 'skeleton_root')
    return True


def saveJoints(fileStack: _StringList = None, method="merge", fileName=None) -> _StringList:
    """
    Save the joint Data to a json file

    :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
    :param str method: method of data merging to apply. Default is "merge"
    :param str fileName: path to the override file.

    :return: list of files saved
    """
    fileStack = common.toList(fileStack)
    dataToSave = gatherJoints()

    layeredSaveInfo = gatherLayeredSaveData(
        dataToSave=dataToSave,
        fileStack=fileStack,
        dataType="JointData",
        method=method,
        fileName=fileName)

    savedFiles = performLayeredSave(layeredSaveInfo, dataType="JointData", prompt=True)

    return savedFiles


def gatherJoints() -> _StringList:
    """
    gather all joints in the scene to save.
    :return: list of all joints in the scene that should be saved.
    """

    # find all skeleton roots and get the positions of their children
    skeletonRoots = common.toList(meta.getTagged('skeleton_root'))

    if not skeletonRoots:
        skeletonRoots = cmds.ls(sl=True)

    allJoints = list()
    if skeletonRoots:
        for root in skeletonRoots:
            childJoints = cmds.listRelatives(root, allDescendents=True, type='joint') or list()
            allJoints.append(root)
            for eachJoint in childJoints:
                allJoints.append(eachJoint)
    else:
        raise RuntimeError(
            "the rootHierarchy joint {} does not exists. Please select some joints.".format(skeletonRoots))

    return allJoints


# Components
def saveComponents(builder: _Builder, fileStack: _StringList = None, method: str = "merge") -> _StringList or None:
    """
    Save out components to a file.
    This only saves component settings such as name, inputs, spaces and names.

    :param builder: instance of a builder object.
    :param str fileStack: path to the component data file
    :param str method: method of data merging to apply. Default is "merge"
    """
    # because component data is gathered from the class but saved with the name as a key
    # this needs to be done in steps. First we can define our save dictionaries using the layered save...
    componentNameList = [c.name for c in builder.componentList]
    saveDict = gatherLayeredSaveData(
        dataToSave=componentNameList,
        fileStack=fileStack,
        dataType="ComponentData",
        method=method)

    # if we escape from the save then we can return
    if not layeredSavePrompt(layeredDataInfo=saveDict, dataType="ComponentData"):
        return

    # ... next loop through the save dict and gather component data based on the component name.
    for dataFile in saveDict:
        componentDataObj = component_data.ComponentData()

        # loop through the list of component names
        for componentName in saveDict[dataFile][CHANGED] + saveDict[dataFile][ADDED]:
            component = builder.findComponent(name=componentName)
            componentDataObj.gatherData(component)
        componentDataObj.write(dataFile)

    return [filepath for filepath in saveDict.keys()]


def loadComponentData(builder: _Builder, filepath: str = None) -> None:
    """
    Load components from a json file. This will only load the component settings and objects.

    :param builder: instance of the builder to store the component list on
    :param filepath: path to component data file
    """

    if not path.isFile(filepath):
        logger.error(f"filepath {filepath} is not a file")
        return

    componentDataObj = component_data.ComponentData()
    componentDataObj.read(filepath)

    # look through each component and add it to the builder list
    # check before adding it so only one instance of each exists in the list
    for component in componentDataObj.getKeys():
        instance = common.getFirstIndex(componentDataObj.applyData(component))

        componentNameList = [component.name for component in builder.componentList]
        if instance.name not in componentNameList:
            builder.componentList.append(instance)


# Guides
def loadGuideData(filepath=None) -> bool:
    """
    Load guide data
    
    :param filepath: path to guide data to save
    :return: True if the data was loaded. False if no data was loaded
    """
    if not path.validatePathExists(filepath):
        return False
    if not path.isFile(filepath):
        logger.error(f"filepath {filepath} is not a file")
        return False

    dataObj = guide_data.GuideData()
    dataObj.read(filepath)
    dataObj.applyAllData()
    return True


def saveGuides(fileStack: _StringList = None, method: str = "merge", fileName: str = None) -> _StringList:
    """
    Save guides data

    :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
    :param str method: method of data merging to apply. Default is "merge"
    :param str fileName: path to the override file.
    """
    # path = path or rigFileData
    fileStack = common.toList(fileStack)
    layeredSaveInfo = gatherLayeredSaveData(
        dataToSave=gatherGuides(),
        fileStack=fileStack,
        dataType="GuideData",
        method=method,
        fileName=fileName
    )
    savedFiles = performLayeredSave(saveDataDict=layeredSaveInfo, dataType="GuideData", prompt=True)

    return savedFiles


def gatherGuides() -> _StringList:
    """
    Gather all guides in the scene
    :return: a list of all guides in the scene
    """
    return meta.getTagged("guide")


def loadControlShapeData(filepath: str = None, applyColor: bool = True) -> bool:
    """
    Load the control shapes

    :param filepath: path to control shape
    :param applyColor: Apply the control colors.
    :return: True if the data was loaded. False if no data was loaded
    """
    if not path.validatePathExists(filepath):
        return False
    if not path.isFile(filepath):
        logger.error(f"filepath {filepath} is not a file")
        return False

    curveDataObj = curve_data.CurveData()
    curveDataObj.read(filepath)

    controls = [ctl for ctl in curveDataObj.getKeys() if cmds.objExists(ctl)]
    curveDataObj.applyData(controls, create=True, applyColor=applyColor)
    return True


def saveControlShapes(fileStack: _StringList = None, method: str = 'merge', fileName: str = None) -> _StringList:
    """
    Save the control shapes

    :param str fileStack: Path to the json file. if none is provided use the data from the rigFile
    :param str method: method of data merging to apply. Default is "merge"
    :param str fileName: path to the override file.

    :return: list of files saved
    """
    layeredSaveInfo = gatherLayeredSaveData(
        dataToSave=gatherControlShapes(),
        fileStack=fileStack,
        dataType="CurveData",
        method=method,
        fileName=fileName
    )

    savedFiles = performLayeredSave(layeredSaveInfo, dataType="CurveData", prompt=True)

    return savedFiles


def gatherControlShapes() -> _StringList:
    """
    gather controls from the scene

    :return: list of all control shapes
    """
    return meta.getTagged("control")


# POSE SPACE DEFORMERS
def savePoseReaders(fileStack: _StringList = None) -> _StringList:
    """
    Save out pose readers

    :param str fileStack: Path to the json file. if none is provided use the data from the rigFile.
    """
    allPoseReaders = gatherPoseReaders()

    layeredSaveInfo = gatherLayeredSaveData(
        dataToSave=allPoseReaders,
        fileStack=fileStack,
        dataType="PSDData",
        method="merge")

    savedFiles = performLayeredSave(layeredSaveInfo, dataType="PSDData", prompt=True)

    # deform._onSavePoseReaders(path)
    return savedFiles


def gatherPoseReaders() -> _StringList:
    """
    gather Pose readers from the scene

    :return: list of all pose reader joints to save
    """
    return [psd.getAssociateJoint(p) for p in meta.getTagged("poseReader")]


def loadPoseReaderData(filepath: str = None, replace: bool = True) -> bool:
    """
    Load pose readers

    :param filepath: path to the pose reader file
    :param replace: If true replace existing pose readers.
    :return: True if the data was loaded. False if no data was loaded
    """
    if not path.validatePathExists(filepath):
        return False
    if not path.isFile(filepath):
        logger.error(f"filepath {filepath} is not a file")
        return False

    dataObj = psd_data.PSDData()
    dataObj.read(filepath)
    dataObj.applyData(nodes=dataObj.getData().keys(), replace=replace)
    return True


# SKIN WEIGHTS
def loadSkinWeightData(filepath=None) -> bool:
    """
    Load all skinweights within the folder
    :param filepath: path to skin weights directory
    :return: True if the data was loaded. False if no data was loaded

    """
    if not path.validatePathExists(filepath):
        return False

    root, ext = os.path.splitext(filepath)
    if ext:
        loadSingleSkin(filepath)
    else:
        files = os.listdir(filepath)
        for f in files:
            eachFile = os.path.join(filepath, f)
            _, fileExtension = os.path.splitext(eachFile)
            if fileExtension == '.json':
                loadSingleSkin(eachFile)
    return True


def loadSingleSkin(filepath) -> bool:
    """
    load a single skin weight file
    :param filepath: path to skin weight file
    :return:
    """
    if not path.isFile(filepath):
        logger.error(f"filepath {filepath} is not a file")
        return False

    if filepath:
        dataObj = skin_data.SkinData()
        dataObj.read(filepath)
        dataObj.applyAllData()
    return True


def saveSkinWeights(filepath: str = None) -> None:
    """
    Save skin weights for selected object

    :param filepath: path to skin weights directory
    """
    if path.isFile(filepath):
        dataObj = skin_data.SkinData()
        dataObj.gatherDataIterate(cmds.ls(sl=True))
        dataObj.write(filepath)

    else:
        for geo in cmds.ls(sl=True):
            if not skinCluster.getSkinCluster(geo):
                continue
            dataObj = skin_data.SkinData()
            dataObj.gatherData(geo)
            dataObj.write("{}/{}.json".format(filepath, geo))


def saveDeformationLayers(filepath: str = None) -> None:
    """
    Save the deformation layers

    :param filepath: path to the deformation layers file
    """
    dataObj = deformLayer_data.DeformLayerData()
    if os.path.exists(filepath):
        dataObj.read(filepath)

    dataObj.gatherDataIterate(cmds.ls(sl=True))
    dataObj.write(filepath)


def loadDeformationLayerData(filepath: str = None) -> bool:
    """
    Load the deformation layers

    :param filepath: path to the deformation layers file
    :return: True if the data was loaded. False if no data was loaded
    """
    if not path.validatePathExists(filepath):
        return False
    if not path.isFile(filepath):
        logger.error(f"filepath {filepath} is not a file")
        return False

    dataObj = deformLayer_data.DeformLayerData()
    dataObj.read(filepath)
    dataObj.applyAllData()
    return True


def loadDeformer(filepath: str = None) -> bool:
    """
    Loads all additional deformation data for the rig.

    :param filepath: path to the data to load
    :return: True if the data was loaded. False if no data was loaded
    """
    if not path.validatePathExists(filepath):
        return False
    if not path.isFile(filepath):
        logger.error(f"filepath {filepath} is not a file")
        return False

    dataType = abstract_data.AbstractData().getDataType(filepath)
    if dataType not in DEFORMER_DATA_TYPES:
        raise ValueError(f"{os.path.basename(filepath)} is not a type of deformer data")

    dataObj = core.createDataClassInstance(dataType)
    dataObj.read(filepath)
    dataObj.applyAllData()
    return True
