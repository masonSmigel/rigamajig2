#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: rigcallbacks.py
    author: masonsmigel
    date: 08/2023
    description: 

"""
import json
import logging
import os

import maya.api.OpenMaya as om2
import maya.cmds as cmds

logger = logging.getLogger(__name__)

SELECTION_OVERRIDE = "selectionOverride"

MAYA_ENV_CALLBACKS_ARRAY = "RIGAMAJIG_CALLBACKS_ARRAY"


def addCallbackToEnviornmentVar(callbackID):
    """
    Add the callback to an enviornment variable. This way we can access the variables within a maya session so long
    as the enviornment is not reset.

    :param callbackID: callback Id to append to the enviornment variable list
    :return:
    """
    if MAYA_ENV_CALLBACKS_ARRAY not in os.environ:
        os.environ[MAYA_ENV_CALLBACKS_ARRAY] = json.dumps([])

    currentList = json.loads(os.environ[MAYA_ENV_CALLBACKS_ARRAY])
    currentList.append(callbackID)
    updatedList = currentList.copy()
    os.environ[MAYA_ENV_CALLBACKS_ARRAY] = json.dumps(updatedList)


def clearRigamajigCallbacks():
    """
    Clear all callbacks created by rigamajig2.
    :return:
    """

    if MAYA_ENV_CALLBACKS_ARRAY not in os.environ:
        logger.warning("No Rigamajig Callbacks exist in the scene")
        return

    callbackIdList = json.loads(os.environ[MAYA_ENV_CALLBACKS_ARRAY])
    MCallbackIdArray = om2.MCallbackIdArray(callbackIdList)

    for callbackID in MCallbackIdArray:
        # TODO: add multiple removals for different callback types
        om2.MEventMessage.removeCallback(callbackID)
        print(f"Callback Removed: {callbackID}")

    # once callbacks are deleted we can just delete the enviornment variable
    del os.environ[MAYA_ENV_CALLBACKS_ARRAY]


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

            itemToSelect = cmds.listConnections(
                f"{s}.selectionOverride", destination=True
            )
            if not itemToSelect:
                continue

            if isinstance(itemToSelect, (list, tuple)):
                itemToSelect = itemToSelect[0]

            cmds.select(s, deselect=True)
            cmds.select(itemToSelect, add=True)

    callbackID = om2.MEventMessage.addEventCallback(
        "SelectionChanged", selectionOverrideCallback, None
    )
    addCallbackToEnviornmentVar(callbackID=callbackID)
