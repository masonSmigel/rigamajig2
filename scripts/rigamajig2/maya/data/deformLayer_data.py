#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: deformLayer_data.py
    author: masonsmigel
    date: 09/2022
    discription: This is the json module for saving maya deformation data


"""
from collections import OrderedDict
import rigamajig2.maya.data.maya_data as maya_data
import maya.cmds as cmds

from rigamajig2.shared import common
from rigamajig2.maya.rig import deformLayer


class DeformLayerData(maya_data.MayaData):
    """ Class to store  maya data"""

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        :type node: str
        """
        super(DeformLayerData, self).gatherData(node)

        data = OrderedDict()

        deformLayerObj = deformLayer.DeformLayer(node)

        layers = deformLayerObj.getDeformationLayers()

        for layer in layers:
            data[layer] = OrderedDict()
            data[layer]['suffix'] = cmds.getAttr("{}.suffix".format(layer))
            connectionMethodIndex = cmds.getAttr("{}.connectionMethod".format(layer))
            data[layer]['connectionMethod'] = deformLayer.CONNECTION_METHOD_LIST[connectionMethodIndex]

        self._data[node].update(data)

    def applyData(self, nodes, attributes=None):
        """
        Apply deformation layer data back to the models.
        """

        nodes = common.toList(nodes)
        for node in nodes:
            deformLayerObj = deformLayer.DeformLayer(node)

            for layer in list(self._data[node].keys()):
                if layer == 'dagPath':
                    continue

                deformLayerObj.createDeformLayer(
                    suffix=self._data[node][layer]['suffix'],
                    connectionMethod=self._data[node][layer]["connectionMethod"]
                    )
