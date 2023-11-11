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
from types import ModuleType
from typing import Type, Dict

from rigamajig2.maya.components import base
from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path
from rigamajig2.shared import process

COMPONENTS_PATH = os.path.abspath(os.path.join(__file__, f"../../components"))
EXCLUDED_FOLDERS = []
EXCLUDED_FILES = ["__init__.py", "base.py"]

logger = logging.getLogger(__name__)

ComponentType = Type[base.Base]


def findComponents(path: str = COMPONENTS_PATH) -> Dict[str, ModuleType]:
    """
    Find all valid components within a folder
    :param path: path to search for components
    :return: dictionary of component type and full python dot separated path.
    """

    path = rig_path.cleanPath(path)
    items = os.listdir(path)

    componentLookup = dict()
    for item in items:
        itemPath = os.path.join(path, item)

        # ensure the item should not be excluded
        if item not in EXCLUDED_FOLDERS and os.path.isdir(itemPath):
            res = findComponents(itemPath)
            componentLookup.update(res)

        # check if the item is a python file
        if item.find(".py") != -1 and item.find(".pyc") == -1 and item not in EXCLUDED_FILES:
            module = process.importModuleFromPath(itemPath)
            components = process.getSubclassesFromModule(module=module, classType=base.Base)

            logger.debug(f"Module:{module}: components: {components}")

            if components:
                if len(components) > 1:
                    logger.warning(f"Component modules should only contain one Component class. {module.__name__}")

                componentTypeSplit = module.__name__.split(".")[-2:]
                componentType = ".".join(componentTypeSplit)
                componentLookup[componentType] = module
    return componentLookup


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

    componentInstances = process.getSubclassesFromModule(moduleObject, classType=base.Base)
    return common.getFirstIndex(componentInstances)


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
