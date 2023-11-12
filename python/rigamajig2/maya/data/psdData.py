#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json module for rigamajig psd data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.data.mayaData as maya_data
import rigamajig2.maya.meta as meta
import rigamajig2.maya.rig.psd as psd


class PSDData(maya_data.MayaData):
    """ This class to save and load pose space deformer reader data"""

    def __init__(self):
        super(PSDData, self).__init__()

    def gatherData(self, node):
        """gather data from node"""

        node = psd.getAssociateJoint(node)

        super(PSDData, self).gatherData(node)

        outputNode = meta.getMessageConnection("{}.poseReaderOut".format(node))

        # gather important info to build the pose reader
        data = OrderedDict()

        outputAttrs = cmds.listAttr(outputNode, ud=True)
        data['useTwist'] = True if True in [True if 'twist' in x else False for x in outputAttrs] else False
        data['useSwing'] = True if True in [True if 'swing' in x else False for x in outputAttrs] else False

        overwriteParent = None
        if cmds.objExists("{}.{}".format(outputNode, "overwriteParentJoint")):
            overwriteParent = str(cmds.getAttr("{}.{}".format(outputNode, "overwriteParentJoint")))
        data['overwriteParent'] = overwriteParent

        self._data[node].update(data)

    def applyData(self, nodes, replace=False):
        """
        Apply settings from the pose reader if one exists in the file
        :param nodes:
        :param replace: delete all existing pose readers before creating new ones
        """
        if replace:
            readers = psd.getAllPoseReaders()
            psd.deletePsdReader(readers)

        for node in nodes:
            if node not in list(self._data.keys()):
                continue
            if not cmds.objExists(node):
                continue

            psd.createPsdReader(node,
                                twist=self._data[node]['useTwist'],
                                swing=self._data[node]['useSwing'],
                                overwriteParent=self._data[node].get("overwriteParent"))

            # TODO: This might need more complexity later... we'll see!
