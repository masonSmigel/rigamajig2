"""
Utility functions
"""
import maya.cmds as cmds
from functools import wraps
import time

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
    Get an MObject for the specifiec object (For maya api 2 )
    :param name: object to get the MObject for
    :return: MObject
    """
    if not cmds.objExists(name):
        cmds.error("Object '{}' does not exist".format(name))
        return

    sel = om2.MGlobal.getSelectionListByName(name)
    return sel.getDependNode(0)


def getDagPath(name):
    """
    Get the DAG path of a node (For maya api 2 )
    :param name: name of the node to get the dag path from
    """
    sel = om2.MGlobal.getSelectionListByName(name)
    return sel.getDagPath(0)


# Decorators
def preserveSelection(func):
    """
    Decorator to preserve the selection before running a function
    :param func: funtion to wrap
    :return:
    """

    @wraps(func)
    def wrap(*args, **kwargs):
        selection = cmds.ls(sl=True)

        try:
            return func(*args, **kwargs)

        except Exception as e:
            raise e

        finally:
            if selection:
                cmds.select(selection)

    return wrap


def oneUndo(func):
    """
    Wrap the function with an open and close undo chunk.
    :param func:
    :return:
    """

    @wraps(func)
    def wrap(*args, **kwargs):
        cmds.undoInfo(openChunk=True, chunkName=func.__name__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=func.__name__)

    return wrap


class Timer(object):
    startTime = 0
    runTime = 0

    @classmethod
    def start(cls):
        cls.startTime = time.time()

    @classmethod
    def stop(cls):
        cls.runTime = time.time() - cls.startTime
        print("Time Elapsed: {}".format(str(cls.runTime)))
