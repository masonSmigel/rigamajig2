#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: decorators.py
    author: masonsmigel
    date: 07/2022

"""
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
    def wrap(*args, **kwargs):
        cmds.undoInfo(openChunk=True, chunkName=func.__name__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=func.__name__)

    return wrap