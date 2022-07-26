#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json module for guide data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""
from collections import OrderedDict
import rigamajig2.maya.data.node_data as node_data
import maya.cmds as cmds
import rigamajig2.maya.attr
import sys

if sys.version_info.major >= 3:
    basestring = str


class GuideData(node_data.NodeData):
    """ This class to save and load curve data"""

    def __init__(self):
        """
        constructor for the node data class
        """
        super(GuideData, self).__init__()

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        """
        super(GuideData, self).gatherData(node)

        data = OrderedDict()
        attrs = cmds.listAttr(node, ud=True)
        for attr in attrs:
            if attr.startswith("__"):
                continue
            data[attr] = rigamajig2.maya.attr .getPlugValue("{}.{}".format(node, attr))

        self._data[node].update(data)
