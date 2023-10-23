#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: data.py
    author: masonsmigel
    date: 08/2023
    description: 

"""
import logging
import os
import typing

from maya import cmds as cmds

from rigamajig2.maya import skinCluster, meta as meta, joint as joint
from rigamajig2.maya.builder import core
from rigamajig2.maya.builder.constants import DEFORMER_DATA_TYPES
from rigamajig2.maya.data import psd_data, skin_data, SHAPES_data, deformLayer_data, joint_data, curve_data, guide_data, \
    abstract_data
from rigamajig2.maya.rig import psd
from rigamajig2.shared import path as rig_path, common as common
from rigamajig2.ui.widgets import mayaMessageBox

logger = logging.getLogger(__name__)


CHANGED = "changed"
ADDED = "added"
REMOVED = "removed"

DATA_MERGE_METHODS = ['new', 'merge', 'overwrite']

LayeredDataInfoDict = typing.Dict[str, typing.Dict[str, typing.List]]


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

    # since we want to replace values from the bottom of the stack first we need to reverse our filestack
    searchFileStack = filteredFileStack.copy()
    searchFileStack.reverse()

    # work on saving the node data of nodes that have been saved first. build a source dictionary to save this data to
    saveDataDict = dict()
    for dataFile in filteredFileStack:
        saveDataDict[dataFile] = {CHANGED: [], ADDED: [], REMOVED: []}

    # we also need to build a list of nodes that we have already saved.
    previouslySavedNodes = list()

    for dataFile in searchFileStack:
        nodesPreviouslyInFile = sourceNodesDict[dataFile]
        for node in nodesPreviouslyInFile:
            if node in dataToSave:
                # if we have already saved the node we can skip it!
                if node in previouslySavedNodes:
                    continue
                # append the node to the list
                saveDataDict[dataFile][CHANGED].append(node)
                previouslySavedNodes.append(node)
            else:
                saveDataDict[dataFile][REMOVED].append(node)

    # get the difference of lists for the unsaved nodes and deleted nodes
    unsavedNodes = set(dataToSave) - set(previouslySavedNodes)

    # now we need to do something with the new nodes!
    if method == 'merge':
        saveDataDict[searchFileStack[0]][ADDED] += unsavedNodes

    if method == 'new':
        if not fileName:
            raise Exception("Please provide a file path to save data to a new file")

        saveDataDict[fileName][ADDED] += unsavedNodes

    if method == 'overwrite':
        # get a filename to save the data to if one isn't provided
        if not fileName:
            if searchFileStack:
                startDir = os.path.dirname(searchFileStack[0])
            else:
                startDir = cmds.workspace(q=True, active=True)

            fileName = cmds.fileDialog2(
                ds=2,
                cap="Override: Select a file to save the data to",
                ff="Json Files (*.json)",
                okc="Select",
                fileMode=0,
                dir=startDir)

            fileName = fileName[0] if fileName else None

        # save the data to the new filename
        if not fileName:
            raise UserWarning("Must specify an override file if one is not proved.")

        # next we need to clear out the added or changed data.
        # keep anything added to removed because we cant delete data later.
        for key in saveDataDict:
            saveDataDict[key][CHANGED] = []
            saveDataDict[key][ADDED] = []

        # add all data to a new key.
        saveDataDict[fileName] = {CHANGED: [], ADDED: dataToSave, REMOVED: []}

    return saveDataDict

def validateLayeredSaveData(saveDataDict: LayeredDataInfoDict) -> bool:
    """
    Validate that the dictionary provided is prepared to be saved as a layeredDataDict
    :param saveDataDict: dictonary of layered data info to process the files with. generated using gatherLayeredSaveData
    :return:
    """
    if not saveDataDict:
        return False

    resultsList = list()
    for file in saveDataDict:
        resultsList.append(all(key in saveDataDict[file] for key in [CHANGED,ADDED, REMOVED]))

    return all(resultsList)


def layeredSavePrompt(saveDataDict: LayeredDataInfoDict, dataType: str) -> bool:
    """
    Bring up the prompt with info about the layered save.

    :param saveDataDict: dictonary of layered data info to process the files with. generated using gatherLayeredSaveData
    :param dataType: Datatype to save.
    :return: result of the popup dialog
    """
    tab = "    "
    message = str()

    totalNodesToSave = 0

    if not validateLayeredSaveData(saveDataDict=saveDataDict):
        raise TypeError("Dictionary provided is not a valid layeredSaveInfo")

    for dataFile in saveDataDict.keys():
        numberChangedNodes = len(saveDataDict[dataFile][CHANGED])
        numberAddedNodes = len(saveDataDict[dataFile][ADDED])
        numberRemovedNodes = len(saveDataDict[dataFile][REMOVED])

        message += f"\n{os.path.basename(dataFile)}: {numberChangedNodes + numberAddedNodes} nodes"

        if numberAddedNodes:
            message += f"\n{tab}New Nodes: {numberAddedNodes}"
        if numberRemovedNodes:
            message += f"\n{tab}Deleted Nodes: {numberRemovedNodes}"

        totalNodesToSave += numberChangedNodes
        totalNodesToSave += numberAddedNodes

    mainMessage = f"Save {totalNodesToSave} nodes to {len(saveDataDict.keys())} files\n" + message
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
    if not validateLayeredSaveData(saveDataDict=saveDataDict):
        raise TypeError("Dictionary provided is not a valid layeredSaveInfo")

    if prompt:
        if not layeredSavePrompt(saveDataDict=saveDataDict, dataType=dataType):
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
        logger.info(f"{dataType} saved to {dataFile}")

    # Get a list of all the files saved.
    filesSaved = list(saveDataDict.keys())
    return filesSaved


# Joints
def loadJoints(path=None):
    """
    Load all joints for the builder
    :param path: path to joint file
    :return:
    """
    if not path:
        return

    if not os.path.exists(path):
        return

    dataObj = joint_data.JointData()
    dataObj.read(path)
    dataObj.applyData(dataObj.getKeys())

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


def saveJoints(path=None):
    """
    save the joints
    :param path: path to save joints
    """

    # find all skeleton roots and get the positions of their children
    skeletonRoots = common.toList(meta.getTagged('skeleton_root'))

    if not skeletonRoots:
        skeletonRoots = cmds.ls(sl=True)

    if skeletonRoots:
        dataObj = joint_data.JointData()
        for root in skeletonRoots:
            dataObj.gatherData(root)
            childJoints = cmds.listRelatives(root, allDescendents=True, type='joint') or list()
            dataObj.gatherDataIterate(childJoints)
        dataObj.write(path)
    else:
        raise RuntimeError(
            "the rootHierarchy joint {} does not exists. Please select some joints.".format(skeletonRoots))


def gatherJoints():
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


# Guides
def loadGuideData(path=None):
    """
    Load guide data
    :param path: path to guide data to save
    :return:
    """
    if not path:
        return

    if path and not os.path.exists(path):
        return

    try:
        dataObj = guide_data.GuideData()
        dataObj.read(path)
        dataObj.applyData(nodes=dataObj.getKeys())
        return True
    except Exception as e:
        raise e
        # return False


def saveGuideData(path=None):
    """
    Save guides data
    :param path: path to guide data to save
    :return:
    """
    dataObj = guide_data.GuideData()
    dataObj.gatherDataIterate(meta.getTagged("guide"))
    dataObj.write(path)


def gatherGuides():
    """
    Gather all guides in the scene
    :return: a list of all guides in the scene
    """
    return meta.getTagged("guide")


# CONTROL SHAPES
def loadControlShapes(path=None, applyColor=True):
    """
    Load the control shapes
    :param path: path to control shape
    :param applyColor: Apply the control colors.
    :return:
    """
    if not path:
        return

    if not os.path.exists(path):
        raise Exception("Path does no exist {}".format(path))

    curveDataObj = curve_data.CurveData()
    curveDataObj.read(path)

    controls = [ctl for ctl in curveDataObj.getKeys() if cmds.objExists(ctl)]
    curveDataObj.applyData(controls, create=True, applyColor=applyColor)


def saveControlShapes(path=None):
    """save the control shapes"""
    curveDataObj = curve_data.CurveData()
    curveDataObj.gatherDataIterate(meta.getTagged("control"))
    curveDataObj.write(path)


def gatherControlShapes():
    """gather controls from the scene"""
    return meta.getTagged("control")


# POSE SPACE DEFORMERS
def savePoseReaders(path=None):
    """
    Save out pose readers
    :param path: path to the pose reader file
    """

    dataObj = psd_data.PSDData()
    dataObj.gatherDataIterate(meta.getTagged("poseReader"))
    dataObj.write(path)


def gatherPoseReaders():
    """
    gather Pose readers from the scene
    :return:
    """
    return [psd.getAssociateJoint(p) for p in meta.getTagged("poseReader")]


def loadPoseReaders(path=None, replace=True):
    """
    Load pose readers
    :param path: path to the pose reader file
    :param replace: If true replace existing pose readers.
    """
    if not path:
        return
    if not os.path.exists(path):
        return
    if path:
        dataObj = psd_data.PSDData()
        dataObj.read(path)
        dataObj.applyData(nodes=dataObj.getData().keys(), replace=replace)
        return True


# SKINWEIGHTS
def loadSkinWeights(path=None):
    """
    Load all skinweights within the folder
    :param path: path to skin weights directory
    """
    if not path:
        return

    if not os.path.exists(path):
        return

    root, ext = os.path.splitext(path)
    if ext:
        loadSingleSkin(path)
    else:
        files = os.listdir(path)
        for f in files:
            filePath = os.path.join(path, f)
            _, fileext = os.path.splitext(filePath)
            if fileext == '.json':
                loadSingleSkin(filePath)
        return True


def loadSingleSkin(path):
    """
    load a single skin weight file
    :param path: path to skin weight file
    :return:
    """
    if path:
        dataObj = skin_data.SkinData()
        dataObj.read(path)
        try:
            dataObj.applyData(nodes=dataObj.getKeys())
        except:
            fileName = os.path.basename(path)
            logger.error("Failed to load skin weights for {}".format(fileName))


def saveSkinWeights(path=None):
    """
    Save skin weights for selected object
    :param path: path to skin weights directory
    :return:
    """
    if rig_path.isFile(path):
        dataObj = skin_data.SkinData()
        dataObj.gatherDataIterate(cmds.ls(sl=True))
        dataObj.write(path)

    else:
        for geo in cmds.ls(sl=True):
            if not skinCluster.getSkinCluster(geo):
                continue
            dataObj = skin_data.SkinData()
            dataObj.gatherData(geo)
            dataObj.write("{}/{}.json".format(path, geo))


def saveSHAPESData(path=None):
    """
    Save both a shapes setup mel file and a json file of the deltas to apply back.
    We can also localize the mel files we create

    :param path:
    :return:
    """
    dataObj = SHAPES_data.SHAPESData()
    if os.path.exists(path):
        dataObj.read(path)

    dataObj.gatherDataIterate(cmds.ls(sl=True))
    dataObj.write(path)


def loadSHAPESData(path=None):
    """
    Import blendshape and connection data from the SHAPES plugin.
    The super cool thing about importing the shapes data is that we dont need to load the plugin!
    The data is applied by sourcing a mel file
    """

    if not path:
        return
    if not os.path.exists(path):
        return

    if path and rig_path.isFile(path):
        dataObj = SHAPES_data.SHAPESData()
        dataObj.read(path)
        dataObj.applyData(nodes=dataObj.getKeys())
        return True


def saveDeformLayers(path=None):
    """
    Save the deformation layers
    :param path: path to the deformation layers file
    :return:
    """
    dataObj = deformLayer_data.DeformLayerData()
    if os.path.exists(path):
        dataObj.read(path)

    dataObj.gatherDataIterate(cmds.ls(sl=True))
    dataObj.write(path)


def loadDeformLayers(path=None):
    """
    Load the deformation layers
    :param path: path to the deformation layers file
    :return:
    """
    if not path:
        return
    if not os.path.exists(path):
        return
    if path:
        dataObj = deformLayer_data.DeformLayerData()
        dataObj.read(path)
        dataObj.applyData(nodes=dataObj.getKeys())
        return True


def loadDeformer(path=None):
    """
    Loads all additional deformation data for the rig.
    :param path:
    :return:
    """
    if not path:
        return
    if not os.path.exists(path):
        return

    if path and rig_path.isFile(path):
        dataType = abstract_data.AbstractData().getDataType(path)
        if dataType not in DEFORMER_DATA_TYPES:
            raise ValueError(f"{os.path.basename(path)} is not a type of deformer data")

        dataObj = core.createDataClassInstance(dataType)
        dataObj.read(path)
        dataObj.applyData(nodes=dataObj.getKeys())
        return True
