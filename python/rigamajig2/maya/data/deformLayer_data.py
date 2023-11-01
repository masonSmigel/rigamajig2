#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: deformLayer_data.py
    author: masonsmigel
    date: 09/2022
    description: This is the json module for saving maya deformation data


"""
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.data.maya_data as maya_data
from rigamajig2.maya import meta
from rigamajig2.maya.rig import deformLayer
from rigamajig2.shared import common


class DeformLayerData(maya_data.MayaData):
    """ Class to store  maya data"""

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        :type node: str
        """
        # make sure we have the render mesh to gather the data from
        if cmds.objExists(f"{node}.{deformLayer.LAYER_ATTR}"):
            node = meta.getMessageConnection(f"{node}.{deformLayer.LAYER_ATTR}")

        super(DeformLayerData, self).gatherData(node)

        data = OrderedDict()
        if cmds.objExists("{}.deformLayerGroup".format(node)):
            data["deformLayerGroup"] = cmds.getAttr("{}.deformLayerGroup".format(node))
        else:
            data["deformLayerGroup"] = None

        deformLayerObj = deformLayer.DeformLayer(node)
        layers = deformLayerObj.getDeformationLayers()

        if layers:
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

            # we need to ensure the key for this exisits since it may not in some old files!
            layerGroup = None
            if "deformLayerGroup" in self._data[node]:
                layerGroup = self._data[node]["deformLayerGroup"]
            deformLayerObj = deformLayer.DeformLayer(node, layerGroup=layerGroup)

            for layer in list(self._data[node].keys()):
                if layer == 'dagPath' or layer == "deformLayerGroup":
                    continue

                deformLayerObj.createDeformLayer(
                    suffix=self._data[node][layer]['suffix'],
                    connectionMethod=self._data[node][layer]["connectionMethod"]
                    )
