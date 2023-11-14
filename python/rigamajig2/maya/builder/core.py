#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: scripts.py
    author: masonsmigel
    date: 07/2022
    description: This module contains utilities for the builder

"""
import glob
import logging
import os
import shutil

from rigamajig2.maya.builder import constants
from rigamajig2.maya.data import abstractData
from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path

logger = logging.getLogger(__name__)

SCRIPT_FOLDER_CONSTANTS = ["pre_scripts", "post_scripts", "pub_scripts"]


def getAvailableArchetypes():
    """
    get a list of available archetypes. Archetypes are defined as a folder containing a .rig file.
    :return: list of archetypes
    """
    archetypeList = list()

    pathContents = os.listdir(common.ARCHETYPES_PATH)
    for archetype in pathContents:
        archetypePath = os.path.join(common.ARCHETYPES_PATH, archetype)
        if archetype.startswith("."):
            continue
        if findRigFile(archetypePath):
            archetypeList.append(archetype)
    return archetypeList


def findRigFile(path):
    """find a rig file within the path"""
    if rig_path.isFile(path):
        return False

    pathContents = os.listdir(path)
    for f in pathContents:
        if f.startswith("."):
            continue
        if not rig_path.isDir(path):
            continue
        fileName, fileExt = os.path.splitext(os.path.join(path, f))
        if fileExt != ".rig":
            continue
        return os.path.join(path, f)
    return False


def newRigEnvironmentFromArchetype(newEnv, archetype, rigName=None):
    """
    Create a new rig environment from and archetype
    :param newEnv: target directory for the new rig environment
    :param rigName: name of the new rig environment
    :param archetype: archetype to copy
    :return: path to the rig file
    """
    if archetype not in getAvailableArchetypes():
        raise RuntimeError("{} is not a valid archetype".format(archetype))

    archetypePath = os.path.join(common.ARCHETYPES_PATH, archetype)
    rigFile = createRigEnvironment(sourceEnvironment=archetypePath, targetEnvironment=newEnv, rigName=rigName)

    data = abstractData.AbstractData()
    data.read(rigFile)

    newData = data.getData()
    newData[constants.BASE_ARCHETYPE] = archetype
    newData[constants.PRE_SCRIPT] = list()
    newData[constants.POST_SCRIPT] = list()
    newData[constants.PUB_SCRIPT] = list()
    data.setData(newData)
    data.write(rigFile)

    # delete the contents of the scripts folders as they should be constructed from
    # previous inheritance. Keeping them here will duplicate the execution.
    for scriptType in SCRIPT_FOLDER_CONSTANTS:
        path = os.sep.join([newEnv, rigName, scriptType])
        files = glob.glob("{}/*".format(path))
        for f in files:
            os.remove(f)

    return rigFile


def createRigEnvironment(sourceEnvironment, targetEnvironment, rigName):
    """
    create a new rig environment from an existing rig enviornment.
    :param sourceEnvironment: source rig environment
    :param targetEnvironment: target rig direction
    :param rigName: new name of the rig environment and .rig file
    :return: path to the rig file
    """

    tgtEnvPath = os.path.join(targetEnvironment, rigName)
    shutil.copytree(sourceEnvironment, tgtEnvPath)

    srcRigFile = findRigFile(tgtEnvPath)
    rigFile = os.path.join(tgtEnvPath, "{}.rig".format(rigName))

    os.rename(srcRigFile, rigFile)

    data = abstractData.AbstractData()
    data.read(rigFile)

    newData = data.getData()
    newData[constants.RIG_NAME] = rigName
    data.setData(newData)
    data.write(rigFile)

    logger.info("New rig environment created: {}".format(tgtEnvPath))
    return os.path.join(tgtEnvPath, rigFile)


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
        raise RuntimeError("rig file at {} does not exist".format(rigFile))

    data = abstractData.AbstractData()
    data.read(rigFile)
    if key in data.getData():
        return data.getData()[key]
    return None
