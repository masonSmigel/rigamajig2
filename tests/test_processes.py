#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_processes.py.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import logging
from pathlib import Path

from rigamajig2.shared import process
from rigamajig2.shared.common import ROOT_PATH, PYTHON_PATH

FILEPATHS = ["path/to/your/test/file.txt", "path/to/your/test/file.py", "path/to/a/directory"]

DOTPATHS = [
    "path.to.your.test.file.txt",
    "path.to.your.test.file.py",
    "path.to.a.directory",
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def test_isDottedPath():
    """Test if a path is a dotted path"""

    for testPath in DOTPATHS:
        assert process.isDottedPath(testPath)


def testIsNotDottedPath():
    """Ensure filepaths return False"""
    for testPath in FILEPATHS:
        assert process.isDottedPath(testPath) == False


def testConvertToDotPath():
    for i, filepath in enumerate(FILEPATHS):
        dotPath = Path(DOTPATHS[i])
        if dotPath.suffix in [".py", ".txt"]:
            dotPath = dotPath.stem

        assert process.asDottedPath(filepath) == str(dotPath)


def testImportModule():
    """Try to import a python module"""

    logger.debug(f"rootpath: {ROOT_PATH}")
    mayaModuleRoot = Path(ROOT_PATH) / "python/rigamajig2/maya"
    testModules = ["curve.py", "mesh.py", "naming.py", "skinCluster.py"]

    for testModule in testModules:
        modulePath = mayaModuleRoot / testModule
        logger.debug(f"Module Path: {modulePath}")

        module = process.importModuleFromPath(modulePath.resolve())

        relativeModulePath = modulePath.resolve().relative_to(PYTHON_PATH)
        logger.debug(f"RelativePath : {relativeModulePath}")
        assert module.__name__ == process.asDottedPath(relativeModulePath)


def testListSubclasses():
    """Try to import a python module"""

    from rigamajig2.maya.components import base

    logger.debug(f"rootpath: {ROOT_PATH}")
    mayaModuleRoot = Path(ROOT_PATH) / "python/rigamajig2/maya/components"
    testModules = ["arm/arm.py", "cog/cog.py", "lookAt/eyeballs.py"]

    for testModule in testModules:
        modulePath = mayaModuleRoot / testModule
        logger.debug(f"Module Path: {modulePath}")
        module = process.importModuleFromPath(modulePath.resolve())

        subclasses = process.getSubclassesFromModule(module, classType=base.BaseComponent)
        assert len(subclasses) > 0


def testListSubclassesIgnoreBase():
    """Ensure that listing subclasses will not list the base class type"""
    from rigamajig2.maya.data import abstractData

    logger.debug(f"rootpath: {ROOT_PATH}")
    mayaModuleRoot = Path(ROOT_PATH) / "python/rigamajig2/maya/data/"

    modulePath = mayaModuleRoot / "abstractData.py"
    logger.debug(f"Module Path: {modulePath}")
    module = process.importModuleFromPath(modulePath.resolve())

    subclasses = process.getSubclassesFromModule(module, classType=abstractData.AbstractData)
    assert len(subclasses) == 0
