"""
This is the json module
"""

import getpass
import json
from collections import OrderedDict
import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.data.maya_data as maya_data
import rigamajig2.maya.hierarchy as hierarchy


class HirachyData(maya_data.MayaData):
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
        data['hierarchy'] = hierarchy.DictHierarchy.getHirarchy(node)

        self._data[node].update(data)

    def applyData(self, nodes):

        nodes = common.toList(nodes)

        for node in nodes:
            if not self._data.has_key(node):
                continue
            hi = hierarchy.DictHierarchy(hierarchy=self._data[node]['hierarchy'])
            hi.create()
