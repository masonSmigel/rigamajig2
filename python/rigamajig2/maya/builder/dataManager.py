#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: data.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import inspect
import os
import pathlib
import sys
from typing import Type

from rigamajig2.maya.data import abstract_data
from rigamajig2.shared import path as rig_path

_AbstractDataType = Type[abstract_data.AbstractData]


DATA_PATH = os.path.abspath(os.path.join(__file__, "../../data"))
DATA_EXCLUDE_FILES = ["__init__.py"]
DATA_EXCLUDE_FOLDERS = []

# Todo: better implementation
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

# TODO: better implementation
def createDataClassInstance(dataType=None) -> _AbstractDataType:
    """
    Create a new and usable instance of a given data type to be actively used when loading new data
    :param dataType:
    :return:
    """
    dataTypeInfo = getDataModules().get(dataType)
    if not dataTypeInfo:
        raise ValueError(f"Data type {dataType} is not valid. Valid Types are {getDataModules()}")

    modulePath = dataTypeInfo[0]
    className = dataTypeInfo[1]

    moduleObject = __import__(modulePath, globals(), locals(), ["*"], 0)
    classInstance = getattr(moduleObject, className)

    # initialize the class when returning it to return it as a NEW instance.
    return classInstance()
