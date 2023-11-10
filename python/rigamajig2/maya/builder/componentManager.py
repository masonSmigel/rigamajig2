#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: componentUtils.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import inspect
import os
import sys
from typing import Type

from rigamajig2.maya.data import abstract_data
from rigamajig2.shared import path as rig_path

CMPT_PATH = os.path.abspath(os.path.join(__file__, "../../components"))
_EXCLUDED_FOLDERS = ["face"]
_EXCLUDED_FILES = ["__init__.py", "base.py"]
CMPT_ROOT_MODULE = "components"

# TODO: better implementation
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
        if item.find(".py") != -1 and item.find(".pyc") == -1 and item not in excludedFiles:
            singleComponentDict = validateComponent(itemPath)
            if singleComponentDict:
                toReturn.update(singleComponentDict)

    return toReturn

# TODO: better implementation
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

    # Todo: better implementation
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

# TODO: better implementation
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


_AbstractDataType = Type[abstract_data.AbstractData]
