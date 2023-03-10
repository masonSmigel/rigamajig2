#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: decorators.py
    author: masonsmigel
    date: 07/2022

"""
import time
from functools import wraps

from maya import cmds as cmds


def preserveSelection(func):
    """
    Decorator to preserve the selection before running a function

    :param func: funtion to wrap
    """

    # pylint:disable=missing-docstring
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
    """

    # pylint:disable=missing-docstring
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Open the undo chunk
        cmds.undoInfo(openChunk=True)

        # Call the original function
        result = func(*args, **kwargs)

        # Close the undo chunk
        cmds.undoInfo(closeChunk=True)

        return result

    return wrapper


def suspendViewport(func):
    """
    Wrap the function to suspend the viewport

    :param func:
    """

    # pylint:disable=missing-docstring
    @wraps(func)
    def wrap(*args, **kwargs):
        cmds.refresh(suspend=True)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            cmds.refresh(suspend=False)

    return wrap


def timeFunction(func):
    """
    Wrap the function to suspend the viewport

    :param func:
    """

    # pylint:disable=missing-docstring
    @wraps(func)
    def wrap(*args, **kwargs):
        startTime = time.time()

        try:
            return func(*args, **kwargs)

        except Exception as e:
            raise e

        finally:
            endTime = time.time()
            finalTime = endTime - startTime

            print "Function {} completed in {}".format(func, finalTime)

    return wrap
