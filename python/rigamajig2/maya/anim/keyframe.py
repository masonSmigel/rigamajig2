#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: keyframe.py
    author: masonsmigel
    date: 03/2023
    description: some utilities for working with keyframes

"""
import logging
from collections import OrderedDict

import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import decorators
from rigamajig2.shared import common

logger = logging.getLogger(__name__)


def wipeKeys(nodes, attributes=None, reset=False):
    """
    Wipe all keys from a node. Optionally we can reset the values to their default values as well.


    :param str list nodes: list of
    :param list attributes: list of attributes to wipe

    :param bool reset:
    :return:
    """
    nodes = common.toList(nodes)

    for node in nodes:
        if not attributes:
            attributes = attr.KEYABLE(node)

        if not cmds.objExists(node):
            raise Exception("The transform '{}' does not exist".format(node))

        for attribute in attributes:
            plug = "{}.{}".format(node, attribute)
            # if the plug doesnt exist we can skip it and give a warning
            if not cmds.objExists(plug):
                logger.warning("The attribute '{}' does not exist. Cannot wipe non-existant attributes".format(plug))
                continue

            # cut the keyframes
            cmds.cutKey(plug, s=True)

            if reset:
                attr.resetDefault(node, attribute)


@decorators.suspendViewport
@decorators.oneUndo
def bake(nodes, start=None, end=None, attributes=None):
    """
    Bake all animation to keyframes

    :param str list nodes: list of nodes to bake keyframes for
    :param int start: start time to bake the simulation for. Default value is start of time slider
    :param int end: end time to bake the simulation for. Default value is end of time slider
    :param list attributes: list of attributes to bake. Default is all keyable.
    :return:
    """

    nodes = common.toList(nodes)

    if not start:
        start = cmds.playbackOptions(animationStartTime=True, query=True)
    if not end:
        end = cmds.playbackOptions(animationEndTime=True, query=True)

    bakeRange = (start, end)

    kwargs = OrderedDict(
        t=bakeRange,
        simulation=True,
        smart=False,
        disableImplicitControl=True,
        preserveOutsideKeys=False,
        sparseAnimCurveBake=False,
        removeBakedAttributeFromLayer=False,
        removeBakedAnimFromLayer=False,
        bakeOnOverrideLayer=False,
        minimizeRotation=True,
        sampleBy=1.0)

    if attributes:
        kwargs['at'] = attributes

    # bake the nodes with the given attribute list
    cmds.bakeResults(nodes, **kwargs)
