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

import maya.cmds as cmds

from rigamajig2.maya.builder import constants
from rigamajig2.maya.data import abstract_data
from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path

logger = logging.getLogger(__name__)

SCRIPT_FOLDER_CONSTANTS = ["pre_scripts", "post_scripts", "pub_scripts"]


def loadRequiredPlugins():
    """
    loadSettings required plugins
    NOTE: There are plugins REQUIRED for rigamajig such as matrix and quat nodes.
          loading other plug-ins needed in production should be added into a pre-script file
    """
    loadedPlugins = cmds.pluginInfo(query=True, listPlugins=True)

    for plugin in common.REQUIRED_PLUGINS:
        if plugin not in loadedPlugins:
            cmds.loadPlugin(plugin)


# Script List Utilities


#
# class GetCompleteScriptList(object):
#     """
#     This class will get a list of all scripts for a given rigfile
#     Including any upstream archetype parents script contents.
#     """
#
#     scriptList = list()
#     scriptDict = dict()
#
#     @classmethod
#     def getScriptList(cls, rigFile, scriptType=None):
#         """
#         This function will get a list of all scripts for a given rigfile including any upstream archetype parents.
#
#         :param rigFile: rig file to get scripts for
#         :param scriptType: key of scripts to get. Typical values are pre_script, post_script or pub_script.
#         :return: list of scripts
#         """
#         cls.scriptList = list()
#
#         cls.findScripts(rigFile=rigFile, scriptType=scriptType)
#
#         # The list is reversed to provide scripts at the lowest level of inheritance first.
#         return list(reversed(cls.scriptList))
#
#     @classmethod
#     def findScripts(cls, rigFile, scriptType=None):
#         """
#         :param rigFile: directories at the current rig file level of the rig
#         :param scriptType: key of scripts to get. Typical values are pre_script, post_script or pub_script.
#         """
#         scriptType = scriptType or constants.PRE_SCRIPT
#
#         localScriptPaths = getRigData(rigFile, scriptType)
#         rigEnviornmentPath = os.path.abspath(os.path.join(rigFile, "../"))
#
#         # for each item in the prescript path append the scripts within that directory
#         for localScriptPath in localScriptPaths:
#             fullScriptPath = os.path.join(rigEnviornmentPath, localScriptPath)
#             builderScripts = validateScriptList(fullScriptPath)
#
#             for script in builderScripts:
#                 if script not in cls.scriptList:
#                     cls.scriptList.insert(0, script)
#
#         baseArchetype = getRigData(rigFile, constants.BASE_ARCHETYPE)
#         archetypeList = common.toList(baseArchetype)
#         for baseArchetype in archetypeList:
#             if baseArchetype and baseArchetype in getAvailableArchetypes():
#                 archetypePath = os.sep.join([common.ARCHETYPES_PATH, baseArchetype])
#                 archetypeRigFile = findRigFile(archetypePath)
#
#                 cls.findScripts(archetypeRigFile, scriptType=scriptType)

# Archetype Utilities


def getAvailableArchetypes():
    """
    get a list of avaible archetypes. Archetypes are defined as a folder containng a .rig file.
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


def newRigEnviornmentFromArchetype(newEnv, archetype, rigName=None):
    """
    Create a new rig envirnment from and archetype
    :param newEnv: target driectory for the new rig enviornment
    :param rigName: name of the new rig enviornment
    :param archetype: archetype to copy
    :return: path to the rig file
    """
    if archetype not in getAvailableArchetypes():
        raise RuntimeError("{} is not a valid archetype".format(archetype))

    archetypePath = os.path.join(common.ARCHETYPES_PATH, archetype)
    rigFile = createRigEnvironment(sourceEnviornment=archetypePath, targetEnviornment=newEnv, rigName=rigName)

    data = abstract_data.AbstractData()
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


def createRigEnvironment(sourceEnviornment, targetEnviornment, rigName):
    """
    create a new rig enviornment from an existing rig enviornment.
    :param sourceEnviornment: source rig enviornment
    :param targetEnviornment: target rig direction
    :param rigName: new name of the rig enviornment and .rig file
    :return: path to the rig file
    """

    tgtEnvPath = os.path.join(targetEnviornment, rigName)
    shutil.copytree(sourceEnviornment, tgtEnvPath)

    srcRigFile = findRigFile(tgtEnvPath)
    rigFile = os.path.join(tgtEnvPath, "{}.rig".format(rigName))

    # rename the .rig file and the rig_name within the .rig file
    os.rename(srcRigFile, rigFile)

    data = abstract_data.AbstractData()
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

    data = abstract_data.AbstractData()
    data.read(rigFile)
    if key in data.getData():
        return data.getData()[key]
    return None
