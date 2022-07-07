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
import rigamajig2.maya.data.psd_data as psd_data
import rigamajig2.maya.data.skin_data as skin_data
import rigamajig2.maya.skinCluster as skinCluster


logger = logging.getLogger(__name__)


# POSE SPACE DEFORMERS
def save_poseReaders(path=None):
    """Save out pose readers"""

    pd = psd_data.PSDData()
    pd.gatherDataIterate(meta.getTagged("poseReader"))
    pd.write(path)


def load_poseReaders(path=None, replace=True):
    """ Load pose readers"""
    if not os.path.exists(path):
        return False

    pd = psd_data.PSDData()
    pd.read(path)
    pd.applyData(nodes=pd.getData().keys(), replace=replace)
    return True


# SKINWEIGHTS
def load_skin_weights(path=None):
    """load all skinweights within the folder"""

    if not os.path.exists(path):
        return

    root, ext = os.path.splitext(path)
    if ext:
        load_single_skin(path)
    else:
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            _, fileext = os.path.splitext(file_path)
            if fileext == '.json':
                load_single_skin(file_path)
        return True


def load_single_skin(path):
    if path:
        sd = skin_data.SkinData()
        sd.read(path)
        sd.applyData(nodes=sd.getData().keys())


def save_skin_weights(path=None):
    if rig_path.isFile(path):
        sd = skin_data.SkinData()
        sd.gatherDataIterate(cmds.ls(sl=True))
        sd.write(path)
        logging.info("skin weights for: {} saved to:{}".format(cmds.ls(sl=True), path))

    else:
        for geo in cmds.ls(sl=True):
            if not skinCluster.getSkinCluster(geo):
                continue
            sd = skin_data.SkinData()
            sd.gatherData(geo)
            sd.write("{}/{}.json".format(path, geo))
            logging.info("skin weights for: {} saved to:{}.json".format(path, geo))