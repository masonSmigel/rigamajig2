#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: channelBox.py
    author: masonsmigel
    date: 01/2021
    discription: channel Box utilities
"""

import maya.cmds as cmds


def getSelectedShapAttrs():
    """get the selected shape"""
    return cmds.channelBox('mainChannelBox', q=True, ssa=True)


def getSelectedInputAttrs():
    """get the selected inputs"""
    return cmds.channelBox('mainChannelBox', q=True, sha=True)


def getSelectedChannels():
    """get the selected channel"""
    return cmds.channelBox('mainChannelBox', q=True, sma=True)


def getFocusNode(input=False, shape=False, output=False):
    """
    Get the name of the node with focus in the channel box.
    You can either specify a section of the channelbox or not.
     If none is specifed look for an input, then an outout and finally a shape
    :param input: get only nodes with focus in the inputs section
    :param shape: get only nodes with focus in the shapes section
    :param output: get only nodes with focus in the output section
    :return:
    """
    selectedInput = cmds.channelBox('mainChannelBox', q=True, hol=True)
    selectedOutput = cmds.channelBox('mainChannelBox', q=True, ool=True)
    selectedShape = cmds.channelBox('mainChannelBox', q=True, sol=True)

    if input: return selectedInput
    if shape: return selectedShape
    if output: return selectedOutput

    if not input and not shape and not output:
        if selectedInput:
            return selectedInput
        elif selectedOutput:
            return selectedOutput
        elif selectedShape:
            return selectedShape
        else:
            return None
