#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: componentUtils.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import logging
import os
import pathlib
from types import ModuleType
from typing import Type, Dict

from rigamajig2.maya.components import base
from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path
from rigamajig2.shared import process

COMPONENTS_PATH = os.path.abspath(os.path.join(__file__, "../../components"))
EXCLUDED_FOLDERS = []
EXCLUDED_FILES = ["__init__.py", "base.py"]

logger = logging.getLogger(__name__)

ComponentType = Type[base.BaseComponent]


def findComponents(path: str = COMPONENTS_PATH) -> Dict[str, ModuleType]:
    """
    Find all valid components within a folder
    :param path: path to search for components
    :return: dictionary of component type and full python dot separated path.
    """

    path = rig_path.cleanPath(path)
    pathContents = os.listdir(path)

    componentLookup = dict()
    for filePathItem in pathContents:
        filePath = pathlib.Path(path) / filePathItem

        if str(filePath.name) not in EXCLUDED_FOLDERS and filePath.is_dir():
            componentLookup.update(findComponents(str(filePath)))

        if filePath.suffix == ".py" and filePath.name not in EXCLUDED_FILES:
            module = process.importModuleFromPath(filePath)
            components = process.getSubclassesFromModule(module=module, classType=base.BaseComponent)

            logger.debug(f"Module:{module}: components: {components}")

            if components:
                if len(components) > 1:
                    logger.warning(f"Component modules should only contain one Component class. {module.__name__}")

                componentType = formatComponentTypeFromModule(modulePath=module.__name__)
                componentLookup[componentType] = module
    return componentLookup


def formatComponentTypeFromModule(modulePath: str) -> str:
    """
    Format the module path into a component type string.

    :param modulePath: module path. Should be a dot separated string `(path.to.component)`
    :return: component name `(component.name)`
    """
    componentTypeSplit = modulePath.split(".")[-2:]
    componentType = ".".join(componentTypeSplit)
    return componentType


def createComponentClassInstance(componentType: str) -> ComponentType:
    """
    Get an instance of the component object based on the componentType
    :param componentType: type of the component to get the class instance from. (limb.limb)
    :return: instance to the component.
    """
    componentLookup = findComponents(COMPONENTS_PATH)

    componentKey = getComponentLookupKey(componentType, componentLookup)
    moduleObject = componentLookup.get(componentKey)

    if not moduleObject:
        raise ValueError(f"Component type {componentType} is not valid. Valid Types are {componentLookup.keys()}")

    componentInstances = process.getSubclassesFromModule(moduleObject, classType=base.BaseComponent)
    return common.getFirst(componentInstances)


def getComponentLookupKey(componentType: str, componentLookup: Dict[str, ModuleType]) -> str:
    """
    Format the component type into a lookup key to use to retrieve the proper module.
    This is a bit of a hack to ensure we are always getting a lookup key that is up-to-date with the
    internal structure of the components

    :param componentType: type of the component to get the class instance from. (limb.limb)
    :param componentLookup: Dictonary of components to query for the componentKey
    :return: lookup key to get the proper component path from the dictionary
    """
    if componentType not in componentLookup:
        componentModule, componentName = componentType.split(".")
        newComponentName = componentName[0].lower() + componentName[1:]
        tempModuleName = f"{componentModule}.{newComponentName}"
        if tempModuleName in componentLookup:
            componentType = tempModuleName

    return componentType
