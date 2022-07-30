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

# RIGAMAJIG
import rigamajig2.shared.path as rig_path
from rigamajig2.maya import meta
from rigamajig2.maya.data import psd_data
from rigamajig2.maya.data import skin_data
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
    if not os.path.exists(path):
        return False

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
        dataObj.applyData(nodes=dataObj.getData().keys())


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