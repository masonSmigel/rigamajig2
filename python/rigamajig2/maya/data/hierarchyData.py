#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json module for heirarchy data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""
from collections import OrderedDict

import rigamajig2.maya.data.mayaData as maya_data
import rigamajig2.maya.hierarchy as hierarchy
import rigamajig2.shared.common as common


class HirachyData(maya_data.MayaData):
    """This class to save and load maya DAG heirarchy data"""

    def __init__(self):
        """
        constructor for the joint data class
        """
        super(HirachyData, self).__init__()

    def gatherData(self, node):
        """
        Save the hirarchy below the node passed
        :param node: node to get hirarchy below
        :return:
        """
        super(HirachyData, self).gatherData(node)
        data = OrderedDict()
        data["hierarchy"] = hierarchy.DictHierarchy.getHirarchy(node)

        self._data[node].update(data)

    def applyData(self, nodes):
        """Apply the hierarchy data"""
        nodes = common.toList(nodes)

        for node in nodes:
            if node not in self._data:
                continue
            nodeHierarchy = hierarchy.DictHierarchy(
                hierarchy=self._data[node]["hierarchy"]
            )
            nodeHierarchy.create()
