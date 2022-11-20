#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: blendshape_data.py
    author: masonsmigel
    date: 09/2022
    discription: This is the json module for saving maya blendshape data


"""
from collections import OrderedDict
import rigamajig2.maya.data.maya_data as maya_data
import maya.cmds as cmds

from rigamajig2.shared import common
from rigamajig2.maya import blendshape


class BlendshapeData(maya_data.MayaData):
    """ Class to store  maya data"""

    def gatherData(self, node, asDelta=False):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute

        :param str node: Node to gather data from
        :param bool asDelta: if True gether data will gather blendshape data as a delta.
                             Otherwise it will gather the targets name and assume it exists in the scene when applying data
        """
        if not blendshape.isBlendshape(node):
            node = blendshape.getBlendshapeNodes(node)[0]

        super(BlendshapeData, self).gatherData(node)

        data = OrderedDict()

        data['geometry'] = blendshape.getBaseGeometry(node)
        targets = blendshape.getTargetList(node)

        data['targets'] = targets
        targetWeightList = list()
        targetGeometryList = list()
        for target in targets:
            if blendshape.hasTargetGeo(node, target):
                targetMesh = blendshape.getTargetGeo(node, target)
            else:
                targetMesh = None
            targetGeometryList.append(targetMesh)
            targetWeightList.append(cmds.getAttr("{}.{}".format(node, target)))
        data['targetGeometry'] = targetGeometryList
        data['targetWeights'] = targetWeightList

        # TODO: implement blendshapes as deltas.
        data['weights'] = blendshape.getWeights(node, targets=None)

        self._data[node].update(data)

    def applyData(self, nodes, attributes=None):
        """
        Apply deformation layer data back to the models.
        """

        nodes = common.toList(nodes)
        for node in nodes:
            if not cmds.objExists(node):
                geometry = self._data[node]['geometry']
                blendshape.create(geometry, name=node)

            for i,target in enumerate(self._data[node]['targets']):
                if target not in blendshape.getTargetList(node):
                    if self._data[node]['targetGeometry'][i]:
                        blendshape.addTarget(node, target=self._data[node]['targetGeometry'][i])
                        cmds.setAttr("{}.{}".format(node, target), self._data[node]['targetWeights'][i])

            blendshape.setWeights(node, weights=self._data[node]['weights'])



