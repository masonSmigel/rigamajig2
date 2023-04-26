#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: quickRename.py
    author: masonsmigel
    date: 04/2023
    discription: 

"""

import sys
import maya.cmds as cmds
from PySide2 import QtWidgets
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance


def mayaMainWindow():
    """ Return the Maya main window widget as a Python object """
    mainWindowPointer = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(mainWindowPointer), QtWidgets.QWidget)
    else:
        return wrapInstance(long(mainWindowPointer), QtWidgets.QWidget)


def quickRename():
    """
    Utility to quickly rename selected objects
    """

    sel = cmds.ls(sl=True)

    if sel:
        initialText = sel[-1]

        text, accept = QtWidgets.QInputDialog.getText(mayaMainWindow(), "Rename", "Enter Name:", text=initialText)

        if accept:
            for s in sel:
                uniqueName = getUniqueName(text)
                cmds.rename(s, uniqueName)


# -------
# function from rigamajig
# ------
DELIMINATOR = '_'


def getUniqueName(name, side=None, indexPosition=-1):
    """
    Generate a unique name for the given string.
    Add an index to the given name. The last interger found in the string will be used as the index.

    :param str name: name to check
    :param side side: side to add to the name
    :param int indexPosition: where to add the index if one is not found. default is -2 (after the suffix)
    :return: returns a new unique name
    """

    if isinstance(name, (list, tuple)):
        name = name[0]

    if side:
        name = "{}_{}".format(name, side)

    # name is already unique
    if not cmds.objExists(name):
        return name

    nameSplit = name.split(DELIMINATOR)
    indexStr = [int(s) for s in nameSplit if s.isdigit()]

    if indexStr:
        # Get the location in the name the index appears.
        # Then incriment the index and replace the original in the nameSplit
        indexPosition = nameSplit.index(str(indexStr[-1]))
        oldIndex = (int(indexStr[-1]) if indexStr else -1)
        newIndex = oldIndex + 1
    else:
        # if the index is '-1' add the new index to the end of the string instead of inserting it.
        newIndex = 1
        if indexPosition == -1:
            nameSplit.append(str(newIndex))
        # if the nameSplit is greater than the index, add the index to the end instead of inserting it.
        elif len(nameSplit) >= abs(indexPosition):
            nameSplit.insert(indexPosition + 1, str(newIndex))
        else:
            nameSplit.append(str(newIndex))
            indexPosition = -1

    # check if an object exists with the name until we find a unique name.
    for i in range(2000):
        nameSplit[indexPosition] = str(newIndex)
        newName = DELIMINATOR.join(nameSplit)
        if cmds.objExists(newName):
            newIndex += 1
        else:
            return newName
