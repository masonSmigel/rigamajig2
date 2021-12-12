"""
Open maya utilities
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.OpenMaya as om


def getMObject(name):
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


def getMObject2(name):
    """
    Get an MObject for the specifiec object (For maya api 2 )
    :param name: object to get the MObject for
    :return: MObject
    """
    if not cmds.objExists(name):
        cmds.error("Object '{}' does not exist".format(name))
        return

    selectionList = om2.MSelectionList()
    selectionList.add(name)
    return selectionList.getDependNode(0)


def getDagPath2(name):
    """
    Get the DAG path of a node (For maya api 2 )
    :param name: name of the node to get the dag path from
    """
    sel = om2.MGlobal.getSelectionListByName(name)
    return sel.getDagPath(0)

