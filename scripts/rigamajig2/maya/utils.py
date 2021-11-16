"""
Utility functions
"""
import maya.cmds as cmds
from functools import wraps
import time


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
