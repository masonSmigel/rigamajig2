"""
Utility functions
"""
from typing import Union

import maya.cmds as cmds
from maya.api import OpenMaya as om

_MObject = Union[str, om.MObject]


def getMObject(node: _MObject) -> om.MObject:
    """
    Get an MObject for the specific object (For maya api 2)

    :param node: object to get the MObject for
    :return: MObject
    """
    if isinstance(node, om.MObject):
        return node

    if not cmds.objExists(node):
        logger.error("Object '{}' does not exist".format(node))
        return None

    selectionList = om.MSelectionList()
    selectionList.add(node)
    return selectionList.getDependNode(0)


def getMfnDependNode(node: _MObject) -> om.MFnDependencyNode:
    """
    Get a MfnDependencyNode from the node

    :param node: node name or MObject
    :return: MfnDag node for the given node
    """
    mobject = getMObject(node)
    mfnDependNode = om.MFnDependencyNode(mobject)
    return mfnDependNode


def getMfnDagNode(node: _MObject) -> om.MFnDagNode:
    """
    Get a mfnDagNode from the given node

    :param node: node name or MObject
    :return: MfnDag node for the given node
    """
    mobject = getMObject(node)
    mfnDagNode = om.MFnDagNode(mobject)
    return mfnDagNode


def getDagPath(node: _MObject) -> om.MDagPath:
    """
    Get the DAG path of a node

    :param node: name of the node to get the dag path from
    :return: MDagPath
    """
    selectionList = om.MSelectionList()
    selectionList.add(node)
    return selectionList.getDagPath(0)
