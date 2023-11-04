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
import inspect
import logging
import os
import pathlib
import shutil
import sys

import maya.cmds as cmds

from rigamajig2.maya.builder import constants
from rigamajig2.maya.data import abstract_data
from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path
from rigamajig2.shared import runScript

logger = logging.getLogger(__name__)

CMPT_PATH = os.path.abspath(os.path.join(__file__, "../../components"))
_EXCLUDED_FOLDERS = ["face"]
_EXCLUDED_FILES = ["__init__.py", "base.py"]
CMPT_ROOT_MODULE = "components"

SCRIPT_FOLDER_CONSTANTS = ["pre_scripts", "post_scripts", "pub_scripts"]

DATA_PATH = os.path.abspath(os.path.join(__file__, "../../data"))
DATA_EXCLUDE_FILES = ["__init__.py"]
DATA_EXCLUDE_FOLDERS = []


# Component Utilities
def findComponents(path=CMPT_PATH, excludedFolders=None, excludedFiles=None):
    """
    Find all valid components within a folder
    :param path: path to search for components
    :param excludedFolders: names of folders to exclude from the search
    :param excludedFiles: names of files to exclude from the search
    :return:
    """
    excludedFiles = excludedFiles or _EXCLUDED_FILES
    excludedFolders = excludedFolders or _EXCLUDED_FOLDERS
    path = rig_path.cleanPath(path)
    items = os.listdir(path)

    toReturn = dict()
    for item in items:
        itemPath = os.path.join(path, item)

        # ensure the item should not be excluded
        if item not in excludedFolders and os.path.isdir(itemPath):
            res = findComponents(itemPath, excludedFolders, excludedFiles)
            toReturn.update(res)

        # check if the item is a python file
        if (
            item.find(".py") != -1
            and item.find(".pyc") == -1
            and item not in excludedFiles
        ):
            singleComponentDict = validateComponent(itemPath)
            if singleComponentDict:
                toReturn.update(singleComponentDict)

    return toReturn


def validateComponent(filePath):
    """
    Check if a file is a valid rigamajig component
    :param filePath: file path to check
    :return tuple: component class name, instance of the class
    """
    # first check to make sure the filepath exists
    if not os.path.exists(filePath):
        return False

    if not rig_path.isFile(filePath):
        return False

    # add the path to sys.path
    pathName = os.path.dirname(filePath)
    fileName = os.path.basename(filePath)

    # find the system path that is imported into python
    pythonPaths = list()
    for sysPath in sys.path:
        if sysPath in pathName:
            pythonPaths.append(sysPath)

    # Get the longest found python path.
    # We should never add a path closer than the python root, so it should always be the longest in the file.
    pythonPath = max(pythonPaths, key=len)

    # convert the path into a python module path (separated by ".")
    # ie: path/to/module --> path.to.module
    pythonPathName = pathName.replace(pythonPath, "")
    pythonModulesSplit = pythonPathName.split(os.path.sep)

    moduleName = fileName.split(".")[0]
    modulePath = ".".join(pythonModulesSplit[1:])

    fullModulename = ".".join([modulePath, moduleName])

    # import the module object to verify it is a component.
    moduleObject = __import__(fullModulename, globals(), locals(), ["*"], 0)
    classesInModule = inspect.getmembers(moduleObject, inspect.isclass)

    for cls in classesInModule:
        # component name must be a PascalCase version of the modulename.
        predictedName = moduleName[0].upper() + moduleName[1:]
        componentClassName = cls[0]
        if componentClassName == predictedName:
            resultDict = dict()
            componentName = ".".join([modulePath.rsplit(".")[-1], moduleName])
            resultDict[componentName] = [fullModulename, componentClassName]
            return resultDict

    return False


def createComponentClassInstance(componentType):
    """
    Get an instance of the component object based on the componentType
    :param componentType: type of the component to get the class instance from.
    :return:
    """
    componentLookupDict = findComponents(CMPT_PATH, _EXCLUDED_FOLDERS, _EXCLUDED_FILES)

    if componentType not in list(componentLookupDict.keys()):
        # HACK: this is a work around to account for the fact that some old .rig files use the cammel cased components
        module, cls = componentType.split(".")
        newClass = cls[0].lower() + cls[1:]
        tempModuleName = module + "." + newClass
        if tempModuleName in list(componentLookupDict.keys()):
            componentType = tempModuleName

    modulePath = componentLookupDict[componentType][0]
    className = componentLookupDict[componentType][1]
    moduleObject = __import__(modulePath, globals(), locals(), ["*"], 0)
    classInstance = getattr(moduleObject, className)

    return classInstance


# Data Type Utilities


def getDataModules(path=None):
    """
    get a dictionary of data type and data module.
    This can be used to create instances of each data module to use in data loading.
    :return:
    """
    if not path:
        path = DATA_PATH
    path = rig_path.cleanPath(path)

    pathObj = pathlib.Path(path)

    # here we can find a python root to use later when creating python paths to load the modules
    pythonPaths = [p for p in sys.path if p in path]
    rigamajigRootPyPath = max(pythonPaths, key=len)

    # Using path lib we can list all files and directories than filter out only the files
    files = [f for f in pathObj.iterdir() if f.is_file()]

    toReturn = dict()
    for file in files:
        filePath = pathlib.Path(os.path.join(path, file.name))

        # check the extension of the files.
        if filePath.suffix == ".py" and filePath.name not in DATA_EXCLUDE_FILES:
            # get the path local to the python path
            relPath = pathlib.Path(filePath.relative_to(rigamajigRootPyPath))

            # convert the path into a python module path (separated by ".")
            # ie: path/to/module --> path.to.module

            # split the file name into parts.
            # then join them back together minus the suffix
            pathSplit = relPath.parts
            pythonModulePath = ".".join([p.removesuffix(".py") for p in pathSplit])

            # next lets import the module to get an instance of it
            moduleObject = __import__(pythonModulePath, globals(), locals(), ["*"], 0)
            classesInModule = inspect.getmembers(moduleObject, inspect.isclass)

            # now we can look through each class and find the subclasses of the abstract Data Class
            for className, classObj in classesInModule:
                if issubclass(classObj, abstract_data.AbstractData):
                    classDict = dict()
                    classDict[className] = [pythonModulePath, className]
                    toReturn.update(classDict)

    return toReturn


def createDataClassInstance(dataType=None):
    """
    Create a new and usable instance of a given data type to be actively used when loading new data
    :param dataType:
    :return:
    """
    dataTypeInfo = getDataModules().get(dataType)
    if not dataTypeInfo:
        raise ValueError(
            f"Data type {dataType} is not valid. Valid Types are {getDataModules()}"
        )

    modulePath = dataTypeInfo[0]
    className = dataTypeInfo[1]

    moduleObject = __import__(modulePath, globals(), locals(), ["*"], 0)
    classInstance = getattr(moduleObject, className)

    # initialize the class when returning it to return it as a NEW instance.
    return classInstance()


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


def validateScriptList(scriptsList=None):
    """
    Validate the script list.
    This will filter all the items in the script into a script type.
    If the item is a directory then get scripts within the directory.

    :param scriptsList: list of directories and/or scripts to check and add to the list
    :return:
    """
    resultList = list()

    scriptsList = common.toList(scriptsList)

    # add all scripts and directories in the script list to the builder
    for item in scriptsList:
        if not item:
            continue

        if rig_path.isFile(item):
            resultList.insert(0, item)

        if rig_path.isDir(item):
            for script in runScript.findScripts(item):
                resultList.insert(0, script)

    return resultList


def runAllScripts(scripts=None):
    """
    Run pre scripts. You can add scripts by path, but the main use is through the PRE SCRIPT path
    :param scripts: path to scripts to run
    """
    if scripts is None:
        scripts = list()

    fileScripts = validateScriptList(scripts)

    fileScripts.reverse()
    for script in fileScripts:
        runScript.runScript(script)


class GetCompleteScriptList(object):
    """
    This class will get a list of all scripts for a given rig file and return them in a dictionary
    """

    scriptDict = dict()
    scriptList = list()
    fileRecursionDict = dict()

    @classmethod
    def getScriptList(cls, rigFile, scriptType=None):
        """
        This function will get a list of all scripts for a given rigfile including any upstream archetype parents.

        :param rigFile: rig file to get scripts for
        :param scriptType: key of scripts to get. Typical values are pre_script, post_script or pub_script.
        :return: list of scripts
        """
        cls.scriptDict = dict()
        cls.scriptList = list()

        cls.findScripts(rigFile=rigFile, scriptType=scriptType)

        return cls.scriptDict

    @classmethod
    def findScripts(cls, rigFile, scriptType, recursionLevel=0):
        """
        :param rigFile: directories at the current rig file level of the rig
        :param scriptType: key of scripts to get. Typical values are pre_script, post_script or pub_script.
        :param recursionLevel: the recursion level of the script to store as the dictionary key.
        """
        scriptType = scriptType or constants.PRE_SCRIPT
        localScriptPaths = getRigData(rigFile, scriptType)
        rigEnvironmentPath = os.path.abspath(os.path.join(rigFile, "../"))

        if recursionLevel not in cls.scriptDict:
            cls.scriptDict[recursionLevel] = []

        # for each item in the script path append the scripts
        for localScriptPath in localScriptPaths:
            fullScriptPath = os.path.join(rigEnvironmentPath, localScriptPath)
            builderScripts = validateScriptList(fullScriptPath)

            # make a temp script list
            _scriptList = list()

            for script in builderScripts:
                if script not in cls.scriptList:
                    _scriptList.insert(0, script)
                    cls.scriptList.insert(0, script)

            cls.scriptDict[recursionLevel].extend(_scriptList)

        # now we can look at the parent archetypes and iterate through them too.
        baseArchetype = getRigData(rigFile, constants.BASE_ARCHETYPE)
        archetypeList = common.toList(baseArchetype)
        for baseArchetype in archetypeList:
            if baseArchetype and baseArchetype in getAvailableArchetypes():
                archetypePath = os.sep.join([common.ARCHETYPES_PATH, baseArchetype])
                archetypeRigFile = findRigFile(archetypePath)

                cls.findScripts(
                    archetypeRigFile,
                    scriptType=scriptType,
                    recursionLevel=recursionLevel + 1,
                )


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
    rigFile = createRigEnvironment(
        sourceEnviornment=archetypePath, targetEnviornment=newEnv, rigName=rigName
    )

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


# Rig File Utilities


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
