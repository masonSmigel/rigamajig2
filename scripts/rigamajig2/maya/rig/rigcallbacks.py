#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: rigcallbacks.py
    author: masonsmigel
    date: 08/2023
    discription: 

"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2

SELECTION_OVERRIDE = "selectionOverride"


def setupSelectionOverrideCallback():
    """
    Setup a callback for the selection override.

    This checks on nodes if they have a "SelectionOverride" message attribute. If it does when that node is selected
    it switches to select the selection override instead.
    :return:
    """

    def selectionOverrideCallback(*clientData):
        """
        Stuff to do when the selection changes
        """
        selection = cmds.ls(sl=True, type="transform")

        if not selection:
            return

        for s in selection:
            if not cmds.objExists(f"{s}.selectionOverride"):
                continue

            itemToSelect = cmds.listConnections(f"{s}.selectionOverride", destination=True)
            if not itemToSelect:
                continue

            if isinstance(itemToSelect, (list, tuple)):
                itemToSelect = itemToSelect[0]

            cmds.select(s, deselect=True)
            cmds.select(itemToSelect, add=True)

    callBackArray = om2.MCallbackIdArray()
    callBackArray.append(om2.MEventMessage.addEventCallback("SelectionChanged", selectionOverrideCallback, None))
