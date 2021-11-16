"""
This module contains skin cluster data
"""

from collections import OrderedDict
import rigamajig2.maya.data.maya_data as maya_data
import rigamajig2.maya.skinCluster as skinCluster


class SkinData(maya_data.MayaData):
    def __init__(self):
        super(SkinData, self).__init__()


    def gatherData(self, node):

        if cmds.nodeType(node) in {'nurbsCurve', 'nurbsSurface', 'mesh'}:
            node = common.getFirstIndex(cmds.listRelatives(node, p=True))
        if cmds.nodeType(node) == 'transform':
            node = skinCluster.getSkinCluster(node)

        super(CurveData, self).gatherData(node)

