#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: blendshape.py
    author: masonsmigel
    date: 01/2021
    discription: blendshape functions and helpers.
"""

# MAYA
import maya.cmds as cmds

# RIGAMAJIG
import rigamajig2.shared.common as common
import rigamajig2.maya.shape


def isBlendshape(blendshape):
    """
    check if the blendshape is a valid belndshape
    :param blendshape: name of deformer to check
    :return: True if Valid. False is invalid.
    """
    blendshape = common.getFirstIndex(blendshape)
    if not cmds.objExists(blendshape) or not cmds.nodeType(blendshape) == 'blendShape': return False
    return True


def create(base, targets=None, origin='local', prefix=None):
    """
    Create a blendshape deformer on the specified geometry
    :param base: base shape of the blendshape
    :param targets: target shapes to add
    :param origin: Optional - create the blendshape with a local or world origin
    :param prefix:
    :return:
    """


def getTargetList(blendshape):
    """
    Get the list of connected targets
    :param blendshape: Blendshape node to get the target list geometry from
    :return: list of targe indicies
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape node".format(blendshape))

    targetList = cmds.listAttr(blendshape + ".w", m=True) or []
    return targetList


def getTargetIndex(blendshape, target):
    """
    Get the index of a blendshape target
    :param blendshape: blendshape
    :param target: target name to find an index of
    :return: index
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape node".format(blendshape))

    if isinstance(target, (int, long)):
        return target

    targetCount = cmds.blendShape(blendshape, q=True, target=True, wc=True)
    n = i = 0
    while n < targetCount:
        alias = cmds.aliasAttr(blendshape + '.w[{}]'.format(i), q=True)
        if alias == target:
            return i
        if alias:
            n += 1
        i += 1
    return -1


def getWeights(blendshape, targets=None, geometry=None):
    """
    Get blendshape target weights as well as the baseWeights.
    If no target or geometry are provided all targets are gathered, and the first geometry.
    :param blendshape: blendshape node to get
    :param targets:
    :param geometry:
    :return:
    """
    weightList = dict()
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape target".format(blendshape))

    if not targets: targets = getTargetList(blendshape)
    if not geometry: geometry = cmds.blendShape(blendshape, q=True, g=True)[0]

    pointCount = rigamajig2.maya.shape.getPointCount(geometry) - 1

    # Get the target weights
    for target in targets:
        targetIndex = getTargetIndex(blendshape, target)

        attr = '{}.it[0].itg[{}].tw[0:{}]'.format(blendshape, targetIndex, pointCount)
        attrDefaultTest = '{}.it[0].itg[{}].tw[*]'.format(blendshape, targetIndex)
        if not cmds.objExists(attrDefaultTest):
            values = [1 for _ in range(pointCount + 1)]
        else:
            values = cmds.getAttr(attr)
            values = [round(v, 5) for v in values]
        weightList[target] = values

    # get the base weights
    attr = '{}.it[0].baseWeights[0:{}]'.format(blendshape, pointCount)
    attrDefaultTest = '{}.it[0].baseWeights[*]'.format(blendshape)
    if not cmds.objExists(attrDefaultTest):
        values = [1 for _ in range(pointCount + 1)]
    else:
        values = cmds.getAttr(attr)
        values = [round(v, 5) for v in values]
    weightList['baseWeights'] = values

    return weightList


def setWeights(blendshape, weights, targets=None, geometry=None):
    """
    Set blendshape target weights as well as the baseWeights.
    If no target or geometry are provided all targets are gathered, and the first geometry.
    :param blendshape: blendshape node to get
    :param weights: dictionary of weights
    :param targets: Optional - influences to set. If None all are set from the weight.
    :param geometry: Optional - Name of geometry to set weights on
    :return:
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape target".format(blendshape))

    if not targets: targets = getTargetList(blendshape) + ['baseWeights']
    if not geometry: geometry = cmds.blendShape(blendshape, q=True, g=True)[0]

    pointCount = rigamajig2.maya.shape.getPointCount(geometry) - 1

    for target in targets:
        if target == 'baseWeights':
            attr = '{}.it[0].baseWeights[0:{}]'.format(blendshape, pointCount)
            cmds.setAttr(attr, *weights[target])
        else:
            targetIndex = getTargetIndex(blendshape, target)
            attr = '{}.it[0].itg[{}].tw[0:{}]'.format(blendshape, targetIndex, pointCount)
            cmds.setAttr(attr, *weights[target])
