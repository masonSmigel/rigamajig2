"""
Utility functions
"""
import maya.cmds as cmds

from maya import OpenMaya as om
from maya.api import OpenMaya as om2


# Open maya utilities
def getOldMObject(name):
    """
    Get an MObject for the specifiec object (using api1)

    :param name: object to get the MObject for
    :return: MObject
    """
    selList = om.MSelectionList()
    selList.add(name)
    mObject = om.MObject()
    selList.getDependNode(0, mObject)
    return mObject


def getMObject(name):
    """
    Get an MObject for the specifiec object (For maya api 2)

    :param name: object to get the MObject for
    :return: MObject
    """
    if not cmds.objExists(name):
        logger.error("Object '{}' does not exist".format(name))
        return

    sel = om2.MGlobal.getSelectionListByName(name)
    return sel.getDependNode(0)


def getDagPath(name):
    """
    Get the DAG path of a node (For maya api 2 )

    :param name: name of the node to get the dag path from
    :return: MDagPath
    """
    sel = om2.MGlobal.getSelectionListByName(name)
    return sel.getDagPath(0)