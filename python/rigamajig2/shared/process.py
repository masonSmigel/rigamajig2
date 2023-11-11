#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: process.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Union, Any


def importModuleFromPath(absolutePath: Union[Path, str], moduleName: str = None) -> ModuleType:
    """
    Import a Python module from an absolute path.

    :param absolutePath: The absolute path to the Python module file.
    :param moduleName: The name to use for the imported module. If not provided, the module will be named based on the file.
    :returns: The imported module.
    """
    if not isinstance(absolutePath, Path):
        absolutePath = Path(absolutePath)

    if isDottedPath(absolutePath):
        return importlib.import_module(str(absolutePath))

    if not moduleName:
        # get a list of all python paths that are a part of the modulePath
        sysPaths = sys.path
        pythonPathsInModulePath = [sysPath for sysPath in sysPaths if sysPath in str(absolutePath)]
        # Get the longest found python path.
        modulePythonRoot = max(pythonPathsInModulePath, key=len)

        relativePath = absolutePath.relative_to(modulePythonRoot)
        moduleName = asDottedPath(relativePath)

    spec = importlib.util.spec_from_file_location(moduleName, absolutePath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def asDottedPath(filepath: Path) -> str:
    """
    Convert a filepath to a dot-separated name

    :param filepath:
    :return: module name as a dot separated path
    """

    moduleName = os.path.splitext(str(filepath))[0].replace(os.path.sep, ".")
    return moduleName


def isDottedPath(filepath: Union[Path, str]) -> bool:
    """
    Check if a filepath is separated by dots (path.to.python.module)

    :param filepath: filepath to check
    :return: bool
    """

    if isinstance(filepath, Path):
        filepath = str(filepath)

    if os.path.sep in filepath:
        return False
    # check if it's greater than two because one can always be for the extension.
    elif len(filepath.split(".")) > 2:
        return True
    else:
        return False


def getSubclassesFromModule(module: ModuleType, classType: Any):
    """
    Iterates all classes within a module object, returning subclasses of type classType.

    :param module: (module object): The module object to iterate on.
    :param classType: The class object.
    :return: A generator function returning class objects.
    """
    classesInModule = []
    for name in dir(module):
        obj = getattr(module, name, None)
        if isinstance(obj, type) and issubclass(obj, classType) and obj != classType:
            classesInModule.append(obj)
    return classesInModule
