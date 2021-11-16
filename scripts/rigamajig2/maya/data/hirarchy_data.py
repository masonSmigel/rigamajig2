"""
This is the json module
"""

import getpass
import json
from collections import OrderedDict
import maya.cmds as cmds
from rigamajig2 import Logger
import rigamajig2.shared.common as common
import rigamajig2.maya.data.maya_data as maya_data
import rigamajig2.maya.hierarchy as dag


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

        def getChildren(n):
            children = cmds.listRelatives(n, c=True, pa=True, type='transform')
            if children:
                data[n] = children
                for child in children:
                    getChildren(child)

        getChildren(node)

        self._data[node].update(data)

    def applyData(self, nodes, create=True):

        nodes = common.toList(nodes)

        for node in nodes:
            for parent, children in self._data[node].iteritems():
                if parent == "dagPath":
                    continue

                if not cmds.objExists(parent):
                    cmds.error('Hirarchy Root {} does not exist'.format(parent))
                    return

                for child in children:
                    shortName = child.split('|')[-1]
                    if not cmds.objExists(child) and create:
                        cmds.createNode('transform', n=shortName)
                    if cmds.objExists(child):
                        try:
                            cmds.parent(child, parent)
                        except:
                            pass
                    else:
                        cmds.parent("|{}".format(shortName), parent)