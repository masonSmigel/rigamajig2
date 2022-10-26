#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json module for rigamajig joint data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""

from collections import OrderedDict
import rigamajig2.maya.data.node_data as node_data
import maya.cmds as cmds


class JointData(node_data.NodeData):
    """Subclass for joint Data"""

    def __init__(self):
        """
        constructor for the joint data class
        """
        super(JointData, self).__init__()

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        :type node: str
        """
        super(JointData, self).gatherData(node)

        data = OrderedDict()
        parent = cmds.listRelatives(node, parent=True)

        data['parent'] = parent[0] if parent else None
        data['jointOrient'] = [round(value, 4) for value in cmds.getAttr("{0}.jo".format(node))[0]]
        data['preferredAngle'] = [round(value, 4) for value in cmds.getAttr("{0}.preferredAngle".format(node))[0]]
        data['drawStyle'] = cmds.getAttr("{0}.drawStyle".format(node))
        data['radius'] = cmds.getAttr("{0}.radius".format(node))

        self._data[node].update(data)

    def applyData(self, nodes):
        """

        :param nodes:
        :return:
        """
        for node in nodes:
            if not cmds.objExists(node):
                cmds.createNode("joint", name=node)

        for node in nodes:
            if "parent" in self._data[node]:
                if self._data[node]["parent"] and cmds.objExists(self._data[node]["parent"]):
                    # check to make sure the node isnt already parented to the parent
                    parents = cmds.listRelatives(node, p=True)  or []
                    if self._data[node]["parent"] not in parents:
                        cmds.parent(node, self._data[node]["parent"])

        super(JointData, self).applyData(nodes)
