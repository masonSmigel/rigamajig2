#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: data.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import os
import pathlib
from types import ModuleType
from typing import Type, Dict

from rigamajig2.maya.data import abstract_data
from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path
from rigamajig2.shared import process

AbstractDataType = Type[abstract_data.AbstractData]


DATA_PATH = os.path.abspath(os.path.join(__file__, "../../data"))
DATA_EXCLUDE_FILES = ["__init__.py"]
DATA_EXCLUDE_FOLDERS = []


def getDataModules(path: str = None) -> Dict[str, ModuleType]:
    """
    get a dictionary of data type and data module.
    This can be used to create instances of each data module to use in data loading.
    :return:
    """
    if not path:
        path = DATA_PATH
    path = rig_path.cleanPath(path)

    pathObj = pathlib.Path(path)

    files = [f for f in pathObj.iterdir() if f.is_file()]

    dataTypeLookup = dict()
    for file in files:
        filePath = pathlib.Path(os.path.join(path, file.name))

        # check the extension of the files.
        if filePath.suffix == ".py" and filePath.name not in DATA_EXCLUDE_FILES:

            moduleObject = process.importModuleFromPath(str(filePath.resolve()))
            dataClasses = process.getSubclassesFromModule(moduleObject, abstract_data.AbstractData)

            if dataClasses:
                dataClass = dataClasses[0]
                dataTypeLookup[dataClass.__name__] = moduleObject

    return dataTypeLookup


def createDataClassInstance(dataType=None) -> AbstractDataType:
    """
    Create a new and usable instance of a given data type to be actively used when loading new data
    :param dataType: name of the dataType to create an instance of.
    :return: return an instance to the data class object
    """
    moduleObject = getDataModules().get(dataType)
    if not moduleObject:
        raise ValueError(f"Data type {dataType} is not valid. Valid Types are {getDataModules()}")

    dataTypeInstance = process.getSubclassesFromModule(moduleObject, classType=abstract_data.AbstractData)
    return common.getFirstIndex(dataTypeInstance)()
