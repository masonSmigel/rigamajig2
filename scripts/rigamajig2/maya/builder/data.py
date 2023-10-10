#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: data.py
    author: masonsmigel
    date: 08/2023
    discription: 

"""
import os

from maya import cmds as cmds

from rigamajig2.maya import psd, skinCluster, meta as meta, joint as joint
from rigamajig2.maya.builder import core
from rigamajig2.maya.builder.constants import DEFORMER_DATA_TYPES
from rigamajig2.maya.data import psd_data, skin_data, SHAPES_data, deformLayer_data, joint_data, curve_data, guide_data, abstract_data
from rigamajig2.shared import path as rig_path, common as common
from . import Builder_Logger


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
            geo = dataObj.getKeys()[0]
            Builder_Logger.info(f"Loaded Skin Weights for: {geo[0] if len(geo)<1 else geo}")
        except:
            fileName = os.path.basename(path)
            Builder_Logger.WARNING("Failed to load skin weights for {}".format(fileName))


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
        Builder_Logger.info("skin weights for: {} saved to:{}".format(cmds.ls(sl=True), path))

    else:
        for geo in cmds.ls(sl=True):
            if not skinCluster.getSkinCluster(geo):
                continue
            dataObj = skin_data.SkinData()
            dataObj.gatherData(geo)
            dataObj.write("{}/{}.json".format(path, geo))
            Builder_Logger.info("skin weights for: {} saved to:{}.json".format(path, geo))


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
