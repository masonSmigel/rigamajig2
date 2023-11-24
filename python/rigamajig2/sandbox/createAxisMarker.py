#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: createAxisMarker.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import os

from maya import cmds as cmds

from rigamajig2.maya import transform as rig_transform


def createAxisMarker(nodes=None):
    """
    Create an axis marker geometry on the given nodes.

    This can be helpful over LRA's since the geometry will show scale as well as orientation

    :param list nodes: nodes to add markers to
    """
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    # if we dont have any nodes. use the selection
    if not nodes:
        nodes = cmds.ls(sl=True)

    asset = os.path.abspath(os.path.join(os.path.dirname(__file__), "../axis_marker.ma"))

    if not cmds.objExists("axisMarker_hrc"):
        cmds.createNode("transform", name="axisMarker_hrc")

    for node in nodes:
        if not cmds.objExists(node):
            continue
        marker = '{}_marker'.format(node)
        if cmds.objExists(marker):
            raise RuntimeError("A marker already exists with the name '{}'".format(marker))

        markerNode = cmds.ls(cmds.file(asset, i=True, returnNewNodes=True, ns='marker'), type='transform')
        cmds.rename(markerNode,marker)
        cmds.parent(marker, "axisMarker_hrc")

        rig_transform.matchTransform(node, marker)
        rig_transform.connectOffsetParentMatrix(node, marker)
