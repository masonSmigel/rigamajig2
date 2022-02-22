"""
This is the json module for rigamajig psd data
"""
import maya.cmds as cmds

from collections import OrderedDict
import rigamajig2.maya.data.maya_data as maya_data
import rigamajig2.shared.common as common


class PSDData(maya_data.MayaData):
    def __init__(self):
        super(PSDData, self).__init__()

    def gatherData(self, node):
        pass

    def applyData(self, nodes):
        pass
