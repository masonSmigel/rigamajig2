#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: blendshape_data.py
    author: masonsmigel
    date: 09/2022
    description: This is the json module for saving maya blendshape data


"""
import logging
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.data.maya_data as maya_data
from rigamajig2.maya import blendshape
from rigamajig2.shared import common

logger = logging.getLogger(__name__)


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
            nodes = blendshape.getBlendshapeNodes(node)
        else:
            nodes = common.toList(node)

        for node in nodes:
            super(BlendshapeData, self).gatherData(node)

            data = OrderedDict()

            data['geometry'] = blendshape.getBaseGeometry(node)
            targets = blendshape.getTargetList(node)

            data['targets'] = dict()
            targetWeightList = list()
            targetGeometryList = list()
            for target in targets:

                targetDict = OrderedDict()
                # get the blendshape delta and any inbetweens deltas
                for iti in blendshape.getInputTargetItemList(node, target):
                    itiDict = OrderedDict(deltas=None, targetGeo=None)
                    wt = blendshape.itiToInbetween(iti)
                    deltas = blendshape.getDelta(node, target, inbetween=wt)
                    itiDict['deltas'] = deltas

                    if blendshape.hasTargetGeo(node, target, inbetween=wt):
                        targetGeo = blendshape.getTargetGeo(node, target, inbetween=wt, plugs=True)
                        itiDict['targetGeo'] = targetGeo

                    targetDict[str(iti)] = itiDict

                data['targets'][target] = targetDict

                targetWeightList.append(cmds.getAttr("{}.{}".format(node, target)))
            data['targetGeometry'] = targetGeometryList
            data['targetWeights'] = targetWeightList

            data['weights'] = blendshape.getWeights(node, targets=None)

            self._data[node].update(data)

    def applyData(self, nodes, attributes=None, loadWeights=False):
        """
        Apply deformation layer data back to the models.
        """

        nodes = common.toList(nodes)
        for node in nodes:
            if not cmds.objExists(node):
                geometry = self._data[node]['geometry']
                blendshapeNode = blendshape.create(geometry, name=node, deformOrder="foc")
            else: blendshapeNode = node

            # get the base
            base = blendshape.getBaseGeometry(blendshapeNode)
            baseIndex = blendshape.getBaseIndex(blendshapeNode, base)

            addedTargets = 0
            for i, target in enumerate(self._data[node]['targets']):
                # rebuild the targets
                if target not in blendshape.getTargetList(blendshapeNode):
                    # first we need to recreate the main target. This is available at the index 6000.
                    deltaDict = self._data[node]['targets'][target]['6000']['deltas']
                    blendshape.addEmptyTarget(blendshapeNode, target=target, )
                    blendshape.setDelta(blendshapeNode, target, deltaDict=deltaDict)

                    addedTargets += 1

                    # now we can do the same for all the inbetweens
                    for iti in list(self._data[node]['targets'][target].keys()):
                        if iti == "6000":
                            continue

                        # recaulcuate the weight of the inbetween
                        # using the same formula used to set the inputTargetIndex
                        wt = blendshape.itiToInbetween(iti)
                        deltaDict = self._data[node]['targets'][target][iti]['deltas']
                        blendshape.addEmptyTarget(blendshapeNode, target, inbetween=wt)
                        blendshape.setDelta(blendshapeNode, target, deltaDict=deltaDict, inbetween=wt)

                    # for each target we need to check if the shape exisits
                    for iti in list(self._data[node]['targets'][target].keys()):
                        # check if the live shape exists. if it does then reconnect it
                        geoShape = self._data[node]['targets'][target][iti]['targetGeo']
                        targetIndex = blendshape.getTargetIndex(blendshapeNode, target)
                        if geoShape and cmds.objExists(geoShape):
                            inputTargetItemPlug = '{}.it[{}].itg[{}].iti[{}]'.format(node, baseIndex, targetIndex, iti)
                            geoTargetPlug = "{}.igt".format(inputTargetItemPlug)
                            # reconnect the target plugs
                            cmds.connectAttr(geoShape, geoTargetPlug)

                    # finally we can set the target weights
                    if loadWeights:
                        cmds.setAttr("{}.{}".format(blendshapeNode, target), self._data[node]['targetWeights'][i])

            blendshape.setWeights(blendshapeNode, weights=self._data[node]['weights'])

            logger.info(f"Blendshape data loaded: '{node}' with {addedTargets} targets")
