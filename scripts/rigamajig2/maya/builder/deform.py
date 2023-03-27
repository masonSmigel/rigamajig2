#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: deform.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
import os
import logging

# MAYA
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om2

# RIGAMAJIG
import rigamajig2.shared.path as rig_path
from rigamajig2.maya import meta
from rigamajig2.maya.data import psd_data
from rigamajig2.maya.data import skin_data
from rigamajig2.maya.data import deformLayer_data
from rigamajig2.maya.data import SHAPES_data
from rigamajig2.maya import skinCluster

logger = logging.getLogger(__name__)


# POSE SPACE DEFORMERS
def savePoseReaders(path=None):
    """
    Save out pose readers
    :param path: path to the pose reader file
    """

    dataObj = psd_data.PSDData()
    dataObj.gatherDataIterate(meta.getTagged("poseReader"))
    dataObj.write(path)


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
            dataObj.applyData(nodes=dataObj.getData().keys())
        except:
            fileName = os.path.basename(path)
            om2.MGlobal.displayWarning("Failed to load skin weights for {}".format(fileName))


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
        logging.info("skin weights for: {} saved to:{}".format(cmds.ls(sl=True), path))

    else:
        for geo in cmds.ls(sl=True):
            if not skinCluster.getSkinCluster(geo):
                continue
            dataObj = skin_data.SkinData()
            dataObj.gatherData(geo)
            dataObj.write("{}/{}.json".format(path, geo))
            logging.info("skin weights for: {} saved to:{}.json".format(path, geo))


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


    # if rig_path.isFile(path):
    #     # mel wont source the file if the slashes match windows slashes
    #     # so we need to search for them and replace them with mel freindly slashes
    #     melFormmatedPath = path.replace("\\", "/")
    #     mel.eval('source "{path}";'.format(path=melFormmatedPath))
    #     return True
    # if rig_path.isDir(path):
    #     for f in os.listdir(path):
    #         name, ext = os.path.splitext(f)
    #         if ext == '.mel':
    #             fullPath = os.path.join(path, f)
    #             melFormmatedPath = fullPath.replace("\\", "/")
    #             mel.eval('source "{path}";'.format(path=melFormmatedPath))
    #     return True


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
        dataObj.applyData(nodes=dataObj.getData().keys())
        return True
