#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json module for maya animation data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""
import sys
from collections import OrderedDict

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

import rigamajig2.maya.data.maya_data as maya_data
import rigamajig2.shared.common as common

if sys.version_info.major >= 3:
    basestring = str


class AnimData(maya_data.MayaData):
    """ This class to save and load  animation data"""

    def __init__(self):
        """
        constructor for the node data class
        """
        super(AnimData, self).__init__()

    # pylint:disable=too-many-locals
    # pylint:disable=too-many-statements
    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        :type node: str
        """
        super(AnimData, self).gatherData(node)

        data = OrderedDict()
        # current input convert to MObject
        objSelection = om.MSelectionList()
        objSelection.add(node)
        objMObject = objSelection.getDependNode(0)

        # Find the attributes of the current object
        mfnDependNode = om.MFnDependencyNode(objMObject)
        attrCount = mfnDependNode.attributeCount()

        for attrIndex in range(attrCount):
            attrMObject = mfnDependNode.attribute(attrIndex)
            mfnAttr = om.MFnAttribute(attrMObject)
            attrName = mfnAttr.name

            # find animataion node connected to the attribute
            currentPlug = mfnDependNode.findPlug(attrName, 1)
            if currentPlug.connectedTo(1, 0):
                connectionList = currentPlug.connectedTo(1, 0)
                connectedNodeMObject = connectionList[0].node()

                # check if the node is an animation node. if not go to the next attribute
                if not connectedNodeMObject.hasFn(om.MFn.kAnimCurve):
                    continue

                mfnAnimCurve = oma.MFnAnimCurve(connectedNodeMObject)
                data[attrName] = OrderedDict()

                data[attrName]['animCurveType'] = mfnAnimCurve.animCurveType
                data[attrName]['preInfinity'] = mfnAnimCurve.preInfinityType
                data[attrName]['postInfinity'] = mfnAnimCurve.postInfinityType
                data[attrName]['weightedTangents'] = mfnAnimCurve.isWeighted

                # find the number of keys in the animation curve
                numKeys = mfnAnimCurve.numKeys

                timeList = list()
                valueList = list()
                lockedTangentsList = list()
                inTangentTypeList = list()
                inTangentAngleList = list()
                inTangentWeightList = list()
                outTangentTypeList = list()
                outTangentAngleList = list()
                outTangentWeightList = list()

                for keyIndex in range(numKeys):
                    # time
                    input = mfnAnimCurve.input(keyIndex)
                    mTime = om.MTime(input)
                    currentTime = mTime.value
                    timeList.append(currentTime)

                    # value
                    value = mfnAnimCurve.value(keyIndex)
                    valueList.append(value)

                    # locked tangents
                    lockedTangents = mfnAnimCurve.tangentsLocked(keyIndex)
                    lockedTangentsList.append(lockedTangents)

                    # in tangent
                    inTangentType = mfnAnimCurve.inTangentType(keyIndex)
                    inTangentTypeList.append(inTangentType)
                    inTangentAngleWeight = mfnAnimCurve.getTangentAngleWeight(keyIndex, 1)
                    inTangentMAngle = om.MAngle(inTangentAngleWeight[0])
                    inTangentAngleValue = inTangentMAngle.value
                    inTangentAngleList.append(inTangentAngleValue)
                    inTangentWeightList.append(inTangentAngleWeight[1])

                    # out Tangent
                    outTangentType = mfnAnimCurve.outTangentType(keyIndex)
                    outTangentTypeList.append(outTangentType)
                    outTangentAngleWeight = mfnAnimCurve.getTangentAngleWeight(keyIndex, 0)
                    outTangentMAngle = om.MAngle(outTangentAngleWeight[0])
                    outTangentAngleValue = outTangentMAngle.value
                    outTangentAngleList.append(outTangentAngleValue)
                    outTangentWeightList.append(outTangentAngleWeight[1])

                data[attrName]['timeList'] = timeList
                data[attrName]['valueList'] = valueList
                data[attrName]['inTangentTypeList'] = inTangentTypeList
                data[attrName]['inTangentAngleList'] = inTangentAngleList
                data[attrName]['inTangentWeightList'] = inTangentWeightList
                data[attrName]['outTangentTypeList'] = outTangentTypeList
                data[attrName]['outTangentAngleList'] = outTangentAngleList
                data[attrName]['outTangentWeightList'] = outTangentWeightList
                data[attrName]['lockedTangents'] = lockedTangentsList

        self._data[node].update(data)

    def applyData(self, nodes, retargetNodes=None, attributes=None):
        """
        Applies animation data to the given nodes
        :param nodes: Array of nodes to apply the data to
        :param retargetNodes: Array of nodes to retarget the data to. matched in order to the nodes
        :param attributes: Array of attributes you want to apply the data to
        :return:
        """
        nodes = common.toList(nodes)
        if not retargetNodes:
            retargetNodes = nodes
        else:
            retargetNodes = common.toList(retargetNodes)

        gatherAttrsFromFile = False
        for node, retargetNode in zip(nodes, retargetNodes):
            if node not in self._data:
                continue
            if not attributes:
                gatherAttrsFromFile = True
                attributes = self._data[node].keys()

            # apply the data
            for attribute in attributes:
                if attribute == 'dagPath':
                    continue

                # get an MPlug for the current plug
                mSelectionList = om.MSelectionList()
                mSelectionList.add("{}.{}".format(retargetNode, attribute))
                currentMPlug = mSelectionList.getPlug(0)

                connectedList = currentMPlug.connectedTo(1, 0)
                newAnimCurve = True

                if connectedList:
                    connecetedNode = connectedList[0].node()
                    if connecetedNode.hasFn(om.MFn.kAnimCurve):
                        mfnAnimCurve = oma.MFnAnimCurve(connecetedNode)
                        newAnimCurve = False

                if newAnimCurve:
                    mfnAnimCurve = oma.MFnAnimCurve()
                    mfnAnimCurve.create(currentMPlug, self._data[node][attribute]['animCurveType'])

                mfnAnimCurve.setPreInfinityType(self._data[node][attribute]['preInfinity'])
                mfnAnimCurve.setPostInfinityType(self._data[node][attribute]['postInfinity'])
                mfnAnimCurve.setIsWeighted(self._data[node][attribute]['weightedTangents'])

                mTimeList = om.MTimeArray()
                mDoubleValueList = om.MDoubleArray()

                for keyIndex in range(len(self._data[node][attribute]['timeList'])):
                    mTimeList.append(om.MTime(self._data[node][attribute]['timeList'][keyIndex], om.MTime.uiUnit()))
                    mDoubleValueList.append(self._data[node][attribute]['valueList'][keyIndex])

                mfnAnimCurve.addKeys(mTimeList, mDoubleValueList, 0, 0, 1)

                for keyIndex in range(len(self._data[node][attribute]['timeList'])):
                    mfnAnimCurve.setInTangentType(keyIndex, self._data[node][attribute]['inTangentTypeList'][keyIndex])
                    mfnAnimCurve.setOutTangentType(keyIndex,
                                                   self._data[node][attribute]['outTangentTypeList'][keyIndex])

                    mfnAnimCurve.setTangentsLocked(keyIndex, self._data[node][attribute]['lockedTangents'][keyIndex])

                    inTangentAngle = om.MAngle(self._data[node][attribute]['inTangentAngleList'][keyIndex])
                    outTangentAngle = om.MAngle(self._data[node][attribute]['outTangentAngleList'][keyIndex])

                    mfnAnimCurve.setAngle(keyIndex, inTangentAngle, 1)
                    mfnAnimCurve.setAngle(keyIndex, outTangentAngle, 0)

                    mfnAnimCurve.setWeight(keyIndex, self._data[node][attribute]['inTangentWeightList'][keyIndex], 1)
                    mfnAnimCurve.setWeight(keyIndex, self._data[node][attribute]['outTangentWeightList'][keyIndex], 0)

                # clear out attributes if getting from file
                if gatherAttrsFromFile:
                    attributes = None

            print("anim loaded '{}' to '{}".format(node, retargetNode))
