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
import maya.api.OpenMayaAnim as oma
import maya.api.OpenMaya as om

# RIGAMAJIG
import rigamajig2.maya.shape
import rigamajig2.maya.openMayaUtils as omu
from rigamajig2.shared import common
from rigamajig2.maya import deformer


def isBlendshape(blendshape):
    """
    check if the blendshape is a valid belndshape

    :param blendshape: name of deformer to check
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    blendshape = common.getFirstIndex(blendshape)
    if not cmds.objExists(blendshape) or not cmds.nodeType(blendshape) == 'blendShape': return False
    return True


def create(base, targets=None, origin='local', deformOrder=None, name=None):
    """
    Create a blendshape deformer on the specified geometry

    :param str base: base shape of the blendshape
    :param str list targets: target shapes to add
    :param str origin: Optional - create the blendshape with a local or world origin
    :param str deformOrder: set the deformation oder
    :param str name: Optional - specify a name
    :return: name fo the blendshape node created
    :rtype: str
    """
    targets = targets or list()
    targets = common.toList(targets)

    if not cmds.objExists(base):
        raise Exception("base mesh {} does not exist".format(base))

    name = name or base
    if not name.endswith("_bshp"):
        blendshapeName = "{}_bshp".format(name)
    else:
        blendshapeName = name

    data = dict()
    if deformOrder == 'after':
        data['after'] = True
    elif deformOrder == 'before':
        data['before'] = True
    elif deformOrder == 'parallel':
        data['parallel'] = True
    elif deformOrder == 'split':
        data['split'] = True
    elif deformOrder == 'foc':
        data['foc'] = True

    blendshapeNode = cmds.blendShape(base, name=blendshapeName, origin=origin, **data)[0]

    # add the blendshape targets
    for target in targets:
        addTarget(blendshape=blendshapeNode, target=target, base=base)

    return blendshapeNode


def addTarget(blendshape, target, base=None, targetIndex=-1, targetWeight=0.0, topologyCheck=False):
    """
    Add a new blendshape target to an existing blendshape node

    :param str blendshape: name of the blendshape nnode
    :param str  target: name of the target geometry to add
    :param str base: base geometry of the blendshape. If Ommited use the first connected base
    :param int targetIndex: specified target index of the blendshape
    :param int float targetWeight: set the target weight
    :param  bool topologyCheck: check the topology of the model before adding the blendshape
    :return: plug of the new target added
    :rtype: str
    """

    if not isBlendshape(blendshape):
        raise Exception("{} is not a blendshape".format(blendshape))

    if not cmds.objExists(target):
        raise Exception("The target geometry {} doesnt exist".format(target))

    if not base:
        base = getBaseGeometry(blendshape)

    if targetIndex < 0:
        targetIndex = getNextTargetIndex(blendshape)

    cmds.blendShape(blendshape, e=True, t=(base, targetIndex, target, 1.0), topologyCheck=topologyCheck)

    targetName = getTargetName(blendshape, target)

    if targetWeight:
        cmds.setAttr("{}.{}".format(blendshape, targetName), targetWeight)

    return "{}.{}".format(blendshape, targetName)


def addInbetween(blendshape, targetGeo, targetName, base=None, targetWeight=0.5):
    """
    Add a new target inbetween to the specified blendShape target

    :param str blendshape: Name of the blendshape node
    :param targetGeo: New target geo to add as an ibetween target
    :param targetName: Name of the blendshape target to add the inbetween to
    :param str base: base geometry of the blendshape. If Ommited use the first connected base
    :param float targetWeight: Set the weight of the target inbetween shape
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a blendshape".format(blendshape))

    if not cmds.objExists(targetGeo):
        raise Exception("The target geometry {} doesnt exist".format(target))

    if base and not mc.objExists(base):
        raise Exception('Base geometry "{}" does not exist!'.format(base))

    if not base:
        base = getBaseGeometry(blendshape)

    targetIndex = getTargetIndex(blendshape, targetName)

    # add the blendshape target
    cmds.blendShape(blendshape, e=True, t=(base, targetIndex, targetGeo, targetWeight))

    return "{}.{}".format(blendshape, targetName)


def getBaseGeometry(blendshape):
    """
    Get a list of blendshape geometry

    :param str blendshape: blendshape name to get the base geometry from
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a blendshape".format(blendshape))

    deformerObj = omu.getMObject(blendshape)
    deformFn = oma.MFnGeometryFilter(deformerObj)

    baseObject = deformFn.getOutputGeometry()
    outputNode = om.MFnDagNode(baseObject[0])

    return outputNode.partialPathName()


def getBlendshapeNodes(geometry):
    """
    Get the blendshape nodes
    :param geometry:
    :return: blendshape node attatched to the geometry
    :rtype: str
    """
    history = cmds.listHistory(geometry)
    blendshapeNodes = cmds.ls(history, type='blendShape')
    return blendshapeNodes


def getTargetList(blendshape):
    """
    Get the list of connected targets
    :param str blendshape: Blendshape node to get the target list geometry from
    :return: list of targe indicies
    :rtype: list
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape node".format(blendshape))

    targetList = cmds.listAttr(blendshape + ".w", m=True) or []
    return common.toList(targetList)


def hasTargetGeo(blendShape, target, base=None):
    """
    Check if the specified blendShape target has live target geometry.

    :param blendShape: Name of blendShape to query
    :param str target: BlendShape target to query
    :param str base: The base geometry index to check for live target geometry.
    """
    # Check blendShape
    if not isBlendshape(blendShape):
        raise Exception('Object "' + blendShape + '" is not a valid blendShape node!')

    # Check target
    if not target in getTargetList(blendShape):
        raise Exception('BlendShape "' + blendShape + '" has no target "' + target + '"!')

    # Check Target Geometry
    targetGeo = getTargetGeo(blendShape, target, base=base)

    # Return Result
    return bool(targetGeo)


def getTargetGeo(blendShape, target, base=None):
    """
    Get the connected target geometry given a blendShape and specified target.

    :param str blendShape: BlendShape node to get target geometry from
    :param str target: BlendShape target to get source geometry from
    :param str base: The base geometry of the blendshape to get the target geometry for. If empty, use base geometry at geomIndex 0.
    """
    # Get Target Index
    targetIndex = getTargetIndex(blendShape, target)

    # Get Geometry Index
    geomIndex = 0
    if base: geomIndex = deformer.getGeoIndex(baseGeo, blendShape)

    # Get Weight Index
    # !!! Hardcoded to check "inputTargetItem" index 6000. This could be more robust by check all existing multi indexes.
    wtIndex = 6000

    # Get Connected Target Geometry
    targetGeoAttr = blendShape + '.inputTarget[' + str(geomIndex) + '].inputTargetGroup[' + str(
        targetIndex) + '].inputTargetItem[' + str(wtIndex) + '].inputGeomTarget'
    targetGeoConn = cmds.listConnections(targetGeoAttr, s=True, d=False)

    # Check Target Geometry
    if not targetGeoConn: targetGeoConn = ['']

    # Return Result
    return targetGeoConn[0]


def getTargetIndex(blendshape, target):
    """
    Get the index of a blendshape target

    :param str blendshape: blendshape
    :param target: target name to find an index of
    :return: index
    :rtype: int
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


def getTargetName(blendshape, targetGeometry):
    """
    Get the target alias for the specified target geometry
    :param blendshape: blendshape node to get the target name from
    :param targetGeometry: blendshape target to get the alais name for
    :return: name of the blendshape target
    :rtype: str
    """

    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape node".format(blendshape))

    targetShape = rigamajig2.maya.shape.getShapes(targetGeometry)
    if not targetShape:
        raise Exception("invalid shape on target geometry {}".format(targetGeometry))

    targetConnections = cmds.listConnections(targetShape, sh=True, d=True, s=False, p=False, c=True)

    if not targetConnections.count(blendshape):
        raise Exception("Target geometry {} is not connected to blnedshape {}".format(targetShape, blendshape))

    targetConnectionIndex = targetConnections.index(blendshape)
    targetConnectionAttr = targetConnections[targetConnectionIndex - 1]
    targetConnectionPlug = cmds.listConnections(targetConnectionAttr, sh=True, p=True, d=True, s=False, t='blendShape')[0]

    targetIndex = int(targetConnectionPlug.split(".")[2].split("[")[1].split("]")[0])
    targetAlias = cmds.aliasAttr("{}.weight[{}]".format(blendshape, targetIndex), q=True)

    return targetAlias


def getNextTargetIndex(blendshape):
    """
    Get the next available index for a blendshape

    :param str blendshape: name of the blendshape to get the next available target for
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape node".format(blendshape))

    targetList = getTargetList(blendshape)
    if not targetList:
        return 0

    lastIndex = getTargetIndex(blendshape, targetList[-1])
    nextIndex = lastIndex + 1

    return nextIndex


def getWeights(blendshape, targets=None, geometry=None):
    """
    Get blendshape target weights as well as the baseWeights.
    If no target or geometry are provided all targets are gathered, and the first geometry.

    :param str blendshape: blendshape node to get
    :param str list targets: list of targets to get the blendshape weifs from
    :param str geometry: Optional name of the geometry to get the targets from.
                         By default it will find the first geometry attatched to the node.
    :return: dictionary of blendshape weights {"baseweights":[], "target":[]}
    :rtype: dict
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

    :param str blendshape: blendshape node to get
    :param str weights: dictionary of weights
    :param str targets: Optional - influences to set. If None all are set from the weight. optionally use "baseWeights" to set the base
    :param str geometry: Optional - Name of geometry to set weights on
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape target".format(blendshape))

    if not targets: targets = getTargetList(blendshape) + ['baseWeights']
    if not geometry: geometry = cmds.blendShape(blendshape, q=True, g=True)[0]

    pointCount = rigamajig2.maya.shape.getPointCount(geometry) - 1

    for target in targets:
        if target == 'baseWeights':
            attr = '{}.inputTarget[0].baseWeights[0:{}]'.format(blendshape, pointCount)
            cmds.setAttr(attr, *weights[target])
        else:
            targetIndex = getTargetIndex(blendshape, target)
            attr = '{}.inputTarget[0].itg[{}].tw[0:{}]'.format(blendshape, targetIndex, pointCount)
            cmds.setAttr(attr, *weights[target])
