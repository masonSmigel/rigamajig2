#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: setup_rig_callbacks.py.py
    author: masonsmigel
    date: 08/2023
    discription: This script will setup any callbacks needed for the rig to work as well as save them into a script
                node to install the callback on startup for other files

"""
import maya.cmds as cmds
from rigamajig2.maya import meta
from rigamajig2.maya import scriptNode
from rigamajig2.maya.rig import rigcallbacks

# check if we need to install a selectionOverride callback:
nodesForSelectionOverride = cmds.ls(f"*.{rigcallbacks.SELECTION_OVERRIDE}")
if len(nodesForSelectionOverride) > 0:
    # first setup the callback in the current scene
    rigcallbacks.setupSelectionOverrideCallback()

    # then create a script job to set it up as well.
    callback = scriptNode.create("rigamajig2_selectionOverride",
                                 scriptType="Open/Close",
                                 beforeScript=rigcallbacks.setupSelectionOverrideCallback,
                                 extraImports="import maya.api.OpenMaya as om2")

    print("Created selection Override callback and scriptnode")
