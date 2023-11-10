#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: blendshape.py
    author: masonsmigel
    date: 01/2021
    description: blendshape functions and helpers.
"""

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
# MAYA
import maya.cmds as cmds

import rigamajig2.maya.openMayaUtils as omu
# RIGAMAJIG
import rigamajig2.maya.shape
from rigamajig2.maya import connection
from rigamajig2.maya import deformer
from rigamajig2.maya import mesh
from rigamajig2.shared import common


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


def addTarget(blendshape, target, targetAlias=None, base=None, targetIndex=-1, targetWeight=0.0, topologyCheck=False):
    """
    Add a new blendshape target from an existing geometry to an existing blendshape node

    :param str blendshape: name of the blendshape nnode
    :param str  target: name of the target geometry to add
    :param str targetAlias: give the newly created target a different alias
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

    if targetAlias:
        renameTarget(blendshape, target, newName=targetAlias)

    return "{}.{}".format(blendshape, targetName)


def addEmptyTarget(blendshape, target, base=None, targetIndex=-1, targetWeight=0.0, inbetween=None,
                   topologyCheck=False):
    """
    Add an empty blendshape target from an existing blendshape node

    :param str blendshape: name of the blendshape nnode
    :param str  target: name of the target geometry to add. This will be a blank shape that doesnt exisit in the scene.
    :param str base: base geometry of the blendshape. If Ommited use the first connected base
    :param int targetIndex: specified target index of the blendshape
    :param float inbetween:
    :param int float targetWeight: set the target weight
    :param  bool topologyCheck: check the topology of the model before adding the blendshape
    :return: plug of the new target added
    :rtype: str
    """
    # if cmds.objExists(target):
    #     raise Exception("The target geometry {} exists. Please use addTarget instead".format(target))

    if not base:
        base = getBaseGeometry(blendshape)
    blankTarget = deformer.createCleanGeo(base, name=f"tmp_{blendshape}_blendshapeNode")

    if inbetween:
        plug = addInbetween(blendshape,
                            targetGeo=blankTarget,
                            targetName=target,
                            base=base,
                            weight=inbetween)
    else:

        plug = addTarget(blendshape,
                         target=blankTarget,
                         base=base,
                         targetIndex=targetIndex,
                         targetWeight=targetWeight,
                         targetAlias=target,
                         topologyCheck=topologyCheck)

    # delete the blank target geo
    cmds.delete(blankTarget)

    return plug


def addInbetween(blendshape, targetGeo, targetName, base=None, weight=0.5, absolute=True):
    """
    Add a new target inbetween to the specified blendShape target

    :param str blendshape: Name of the blendshape node
    :param targetGeo: New target geo to add as an ibetween target
    :param targetName: Name of the blendshape target to add the inbetween to
    :param str base: base geometry of the blendshape. If Ommited use the first connected base
    :param float weight: Set the weight of the target inbetween shape
    :param bool absolute: Add the inbtween as an absoutle target

    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a blendshape".format(blendshape))

    if not cmds.objExists(targetGeo):
        raise Exception("The target geometry {} doesnt exist".format(target))

    if base and not cmds.objExists(base):
        raise Exception('Base geometry "{}" does not exist!'.format(base))

    if not base:
        base = getBaseGeometry(blendshape)

    targetIndex = getTargetIndex(blendshape, targetName)

    # add the blendshape target
    inbetweenType = 'absolute' if absolute else 'relative'
    cmds.blendShape(blendshape, e=True, t=(base, targetIndex, targetGeo, weight), ib=True, ibt=inbetweenType)

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


def getBaseIndex(blendshape, base):
    """
    Get the index for a given base geometry

    :param blendshape: blendshape node
    :param base: base node
    :return:
    """
    # get the blendshape as a geometry filter
    deformerObj = omu.getMObject(blendshape)
    deformFn = oma.MFnGeometryFilter(deformerObj)

    # get the deforming shape and an mObject for it.
    deformingShape = deformer.getDeformShape(base)
    deformingShapeMObj = omu.getMObject(deformingShape)

    return deformFn.indexForOutputShape(deformingShapeMObj)


def getBlendshapeNodes(geometry):
    """
    Get the blendshape nodes
    :param geometry:
    :return: blendshape node attatched to the geometry
    :rtype: str
    """
    deformers = deformer.getDeformerStack(geometry)
    blendshapeNodes = cmds.ls(deformers, type='blendShape')
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


def hasTargetGeo(blendShape, target, base=None, inbetween=None):
    """
    Check if the specified blendShape target has live target geometry.

    :param blendShape: Name of blendShape to query
    :param str target: BlendShape target to query
    :param str base: The base geometry index to check for live target geometry.
    :param float inbetween: Optional get the input target geo for an inbetween
    """
    # Check blendShape
    if not isBlendshape(blendShape):
        raise Exception('Object "' + blendShape + '" is not a valid blendShape node!')

    # Check target
    if not target in getTargetList(blendShape):
        raise Exception('BlendShape "' + blendShape + '" has no target "' + target + '"!')

    # Check Target Geometry
    targetGeo = getTargetGeo(blendShape, target, base=base, inbetween=inbetween)

    # Return Result
    return bool(targetGeo)


def getTargetGeo(blendShape, target, base=None, inbetween=None, plugs=False):
    """
    Get the connected target geometry given a blendShape and specified target.

    :param str blendShape: BlendShape node to get target geometry from
    :param str target: BlendShape target to get source geometry from
    :param str base: The base geometry of the blendshape to get the target geometry for.
                      If empty, use base geometry at geomIndex 0.
    :param inbetween: Optional get the input target geo for an inbetween
    """
    # Get Target Index
    targetIndex = getTargetIndex(blendShape, target)

    # Get Geometry Index
    geomIndex = 0
    if base: geomIndex = deformer.getGeoIndex(baseGeo, blendShape)

    # Get Weight Index
    wtIndex = 6000 if not inbetween else inbetweenToIti(inbetween)

    # Get Connected Target Geometry
    targetGeoAttr = blendShape + '.inputTarget[' + str(geomIndex) + '].inputTargetGroup[' + str(
        targetIndex) + '].inputTargetItem[' + str(wtIndex) + '].inputGeomTarget'
    targetGeoConn = cmds.listConnections(targetGeoAttr, s=True, d=False, plugs=plugs)

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

    if isinstance(target, int):
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


def renameTarget(blendshape, target, newName):
    """
    Rename a given blendshape target to a new name. This is accomplished by using the blendshape attribute alias

    :param blendshape:
    :param target:
    :param newName:
    :return:
    """

    allAliases = cmds.aliasAttr(blendshape, q=True)
    if not target in allAliases:
        raise ValueError("BlendShape node '{}' doesn't have an alias '{}'".format(blendshape, target))
    oldAliasIndex = allAliases.index(target) + 1
    oldAliasAttr = allAliases[oldAliasIndex]
    cmds.aliasAttr(newName, '{}.{}'.format(blendshape, oldAliasAttr))


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
    targetConnectionPlug = cmds.listConnections(targetConnectionAttr, sh=True, p=True, d=True, s=False, t='blendShape')[
        0]

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

        targetAttr = '{}.it[0].itg[{}].tw[0:{}]'.format(blendshape, targetIndex, pointCount)
        attrDefaultTest = '{}.it[0].itg[{}].tw[*]'.format(blendshape, targetIndex)
        if not cmds.objExists(attrDefaultTest):
            values = [1 for _ in range(pointCount + 1)]
        else:
            values = cmds.getAttr(targetAttr)
            values = [round(v, 5) for v in values]

        # optimize the value list
        opimizedDict = dict()
        for i, v in enumerate(values):
            # if the weights are almost equal to zero skip adding them.
            if not abs(v - 1.0) <= 0.0001:
                opimizedDict[i] = v

        weightList[target] = opimizedDict

    # get the base weights
    targetAttr = '{}.it[0].baseWeights[0:{}]'.format(blendshape, pointCount)
    attrDefaultTest = '{}.it[0].baseWeights[*]'.format(blendshape)
    if not cmds.objExists(attrDefaultTest):
        values = [1 for _ in range(pointCount + 1)]
    else:
        values = cmds.getAttr(targetAttr)
        values = [round(v, 5) for v in values]

    # optimize the value list
    opimizedDict = dict()
    for i, v in enumerate(values):
        # if the weights are almost equal to skip adding them.
        if not abs(v - 1.0) <= 0.0001:
            opimizedDict[i] = v

    weightList['baseWeights'] = opimizedDict

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
        raise Exception("{} is not a valid blendshape".format(blendshape))

    if not targets: targets = getTargetList(blendshape) + ['baseWeights']
    if not geometry: geometry = cmds.blendShape(blendshape, q=True, g=True)[0]

    targets = common.toList(targets)

    pointCount = rigamajig2.maya.shape.getPointCount(geometry) - 1

    for target in targets:
        if not target:
            continue

        if target == 'baseWeights':
            tmpWeights = list()
            for i in range(pointCount + 1):
                # we need to check if there are weights in the dictionary. We can use get to check and return -1 if
                # there is not a key for the specified weight. After that we can check if the weight == None. If we does
                # we replace it with 1.0 since we stripped out any values at 1.0 when we gathered the weights
                if weights[target].get(i) is not None:
                    tmpWeight = weights[target].get(i)
                elif weights[target].get(str(i)) is not None:
                    tmpWeight = weights[target].get(str(i))
                else:
                    tmpWeight = 1.0
                # finally append the weight to the list
                tmpWeights.append(tmpWeight)

            targetAttr = '{}.inputTarget[0].baseWeights[0:{}]'.format(blendshape, pointCount)
            cmds.setAttr(targetAttr, *tmpWeights)
        else:
            tmpWeights = list()
            for i in range(pointCount + 1):
                # we need to check if there are weights in the dictionary. We can use get to check and return -1 if
                # there is not a key for the specified weight. After that we can check if the weight == None. If we does
                # we replace it with 1.0 since we stripped out any values at 1.0 when we gathered the weights

                if weights[target].get(i) is not None:
                    tmpWeight = weights[target].get(i)
                elif weights[target].get(str(i)) is not None:
                    tmpWeight = weights[target].get(str(i))
                else:
                    tmpWeight = 1.0

                # finally append the weight to the list
                tmpWeights.append(tmpWeight)

            targetIndex = getTargetIndex(blendshape, target)
            targetAttr = '{}.inputTarget[0].itg[{}].tw[0:{}]'.format(blendshape, targetIndex, pointCount)
            cmds.setAttr(targetAttr, *tmpWeights)


def getInputTargetItemList(blendshape, target, base=None):
    """
    Get the input targetItem attribute from a blendshape node and a target.
    This is handy if we want to rebuild the targets from deltas or just check if nodes are connected to the targets already

    :param blendshape: name of the blendshape node to get the target item plug
    :param target: name of the blendshape target to check
    :param base: Optional pass in a specific base to query from.
    :return:
    """

    targetIndex = getTargetIndex(blendshape, target=target)

    if not base: base = getBaseGeometry(blendshape)
    # get the base index
    baseIndex = getBaseIndex(blendshape, base)

    # we need to list all the available inputTargetItems added to the blendshape
    # The attribute can be a bit awkward to manage so set it up here.
    # (inputTarget[0].inputTargetGroup[0].inputTargetItem).
    targetItemAttr = "{}.it[{}].itg[{}].iti ".format(blendshape, baseIndex, targetIndex)

    # return a list of all indecies gathered.
    indices = cmds.getAttr(targetItemAttr, mi=True)
    return indices


def itiToInbetween(iti):
    """Convert the inputTargetItem index into float representing the inbetween value"""
    return float((int(iti) - 5000) / 1000)


def inbetweenToIti(inbetween):
    """Convert the inbtween float an inputTargetItem index"""
    return int((float(inbetween) * 1000) + 5000)


def getDelta(blendshape, target, inbetween=None, prune=5):
    """
    Gather
    :param blendshape: name of the blendshape to gather blendshape data from.
    :param target: name of the target to gather the delta information for
    :param inbetween: value of the ibetween to gather the delta from. If not set get the base blendshape delta.
    :param prune: amount of decimal places to prune from delta
    :return: delta data dictionary of deltas for vertex IDs
    """
    if not isBlendshape(blendshape):
        raise Exception("'{}' is not a valid blendshape".format(blendshape))

    targetIndex = getTargetIndex(blendshape, target)

    base = getBaseGeometry(blendshape)
    baseIndex = getBaseIndex(blendshape, base)

    inputTargetItem = 6000 if not inbetween else inbetweenToIti(inbetween)

    # Theese attributes can get rather unweidly. so we'll do it once here to reuse later.
    # this attribute accesses the input target item for a given index.
    inputTargetItemPlug = '{}.it[{}].itg[{}].iti[{}]'.format(blendshape, baseIndex, targetIndex, inputTargetItem)
    geoTargetPlug = "{}.igt".format(inputTargetItemPlug)

    # define the delta point list to store the delta into.
    deltaPointList = dict()

    # first lets check to see if its connected to any input geometry.
    if len(cmds.listConnections(geoTargetPlug, s=True, d=False) or list()) > 0:
        inputShape = cmds.listConnections(geoTargetPlug, s=True, d=False, plugs=True)
        # get the shape node of the input shape conenction
        inputShape = inputShape[0].split(".")[0]

        # get the point positions for the target shape
        targetPoints = mesh.getVertPositions(inputShape, world=False)

        # get the point positions for the orig shape
        origShape = deformer.getOrigShape(base)
        origPoints = mesh.getVertPositions(origShape, world=False)

        deltaPointList = dict()
        for i in range(len(targetPoints)):

            # get the difference of the base geo and deformed geo
            offset = om.MVector(targetPoints[i]) - om.MVector(origPoints[i])

            # check if the magnitude is within a very small vector before adding it.
            # This will help us cut down on file sizes.
            if offset.length() >= 0.0001:
                deltaPointList[str(i)] = round(offset.x, prune), round(offset.y, prune), round(offset.z, prune)

    # if we dont have any input geo then we need to gather the target points
    else:
        # the input points target list stores a list of offsets from the orignial shape of the vertex to the blendshape
        pointsTarget = cmds.getAttr("{}.ipt".format(inputTargetItemPlug))
        # the components target stores a list of components that have been modified.
        # The order matches that of the pointsTarget list.
        componentsTarget = common.flattenList(cmds.getAttr("{}.ict".format(inputTargetItemPlug)))

        # now we need to compose thos into a delta point dictionary
        for point, componentTarget in zip(pointsTarget, componentsTarget):
            vertexId = componentTarget.split('[')[-1].split(']')[0]

            # add the item to the delta list
            prunedPoint = round(point[0], prune), round(point[1], prune), round(point[2], prune)
            deltaPointList[vertexId] = prunedPoint

    return deltaPointList


def setDelta(blendshape, target, deltaDict, inbetween=None):
    """
    Set the delta values on a given blendshape target.
    By setting the inputPointsTarget  and inputComponentsTarget attributes of a given inputTargetItem Idex attributes
    we can effectivly add a new blendshape target without requiring a target to be rebuilt.

    :param blendshape: Name of the blendshape node
    :param target: name of the target to set the delta on
    :param deltaDict: delta data dictionary of deltas for vertex IDs. Gathered from getDeltas
    :param inbetween: Specify an inbetween to set the delta for the given target. Otherwise replace
                      inputTargetItem index 6000.
    """
    if not isBlendshape(blendshape):
        raise Exception("'{}' is not a valid blendshape".format(blendshape))

    targetIndex = getTargetIndex(blendshape, target)

    base = getBaseGeometry(blendshape)
    baseIndex = getBaseIndex(blendshape, base)

    inputTargetItem = 6000 if not inbetween else inbetweenToIti(inbetween)

    # Theese attributes can get rather unweidly. so we'll do it once here to reuse later.
    # this attribute accesses the input target item for a given index.
    inputTargetItemPlug = '{}.it[{}].itg[{}].iti[{}]'.format(blendshape, baseIndex, targetIndex, inputTargetItem)
    geoTargetPlug = "{}.igt".format(inputTargetItemPlug)

    # first lets check to see if its connected to any input geometry.
    if len(cmds.listConnections(geoTargetPlug, s=True, d=False) or list()) > 0:
        raise Warning("{}.{} has a live blendshape connection".format(blendshape, target))

    else:
        pointsList = [deltaDict[p] for p in list(deltaDict.keys())]
        componentsList = ["vtx[{}]".format(p) for p in list(deltaDict.keys())]

        # set the inputPointsTarget and inputComponentsTarget
        cmds.setAttr("{}.ipt".format(inputTargetItemPlug), len(pointsList), *pointsList, type="pointArray")
        cmds.setAttr("{}.ict".format(inputTargetItemPlug), len(componentsList), *componentsList, type="componentList")


def reconstructTargetFromDelta(blendshape, deltaDict, name=None):
    """
    Reconstruct a blendshape target from a given delta dictionary.
    The deltaDict contains a vertexid and a delta position per item.
    If no delta exists for the given vertexid default to the position from the orig shape

    :param blendshape: blendshape node to reconstruct the delta for. This is used for gathering the orig shape.
    :param deltaDict: delta data dictionary of deltas for vertex IDs
    :param name: name the newly created target
    :return: New blendshape target mesh from delta
    """
    if not isBlendshape(blendshape):
        raise Exception("'{}' is not a valid blendshape".format(blendshape))

    base = getBaseGeometry(blendshape)
    origShape = deformer.getOrigShape(base)
    origShapePoints = mesh.getVertPositions(origShape, world=False)

    targetGeo = deformer.createCleanGeo(base, name=name)

    for vtxid in list(deltaDict.keys()):
        # calculate the absoute point of the vertex given the orig and delta
        origPoint = om.MPoint(origShapePoints[int(vtxid)])
        delta = om.MVector(deltaDict[vtxid])

        absPoint = origPoint + delta
        absPoint = [absPoint.x, absPoint.y, absPoint.z]

        # now we need to set the vertex to that position
        cmds.xform("{}.vtx[{}]".format(targetGeo, vtxid), objectSpace=True, translation=absPoint)

    return targetGeo


def regenerateTarget(blendshape, target, inbetween=None, connect=True):
    """
    regenerate a live target mesh for a given target.

    :param blendshape: blendshape node
    :param target: name of the target to regenerate
    :param inbetween: value of the inbetween to get
    :return: newly created duplicate
    """

    if not isBlendshape(blendshape):
        raise Exception("'{}' is not a valid blendshape".format(blendshape))

    # get the target index
    targetIndex = getTargetIndex(blendshape, target)

    base = getBaseGeometry(blendshape)
    baseIndex = getBaseIndex(blendshape, base)

    # get the input target item index
    inputTargetItem = 6000 if not inbetween else inbetweenToIti(inbetween)

    inputTargetItemPlug = '{}.it[{}].itg[{}].iti[{}]'.format(blendshape, baseIndex, targetIndex, inputTargetItem)

    # check if an inputTargetItem exisits for the given inbetween
    if inputTargetItem not in getInputTargetItemList(blendshape, target):
        raise ValueError("No inbetween exists for '{}.{}' at the inbetween {}".format(blendshape, target, inbetween))

    # check if the plug is already connected to geometry
    if cmds.listConnections("{}.igt".format(inputTargetItemPlug), s=True, d=False, plugs=True):
        print("{}.{} is already connected to input geometry".format(blendshape, target))
        return

    # if its not we can reconstruct the delta then connect it to the inputGeometryTarget plug.
    else:
        ibName = "{}_ib{}".format(target, str(inbetween).replace(".", "_").replace("-", "neg"))
        targetGeoName = target if not inbetween else ibName
        deltaDict = getDelta(blendshape, target, inbetween=inbetween)
        targetGeo = reconstructTargetFromDelta(blendshape, deltaDict=deltaDict, name=targetGeoName)

        targetGeoShape = cmds.listRelatives(targetGeo, s=True)[0]
        if connect:
            cmds.connectAttr("{}.worldMesh[0]".format(targetGeoShape), "{}.igt".format(inputTargetItemPlug), f=True)

        return targetGeo


def transferBlendshape(blendshape, targetMesh, blendshapeName=None, copyConnections=True, deformOrder="foc"):
    """
    Transfer a blendshape from one node to another.

    :param blendshape: Blendshape to copy to another mesh
    :param targetMesh: mesh to transfer the blendshape to
    :param blendshapeName: name of the new blendshape
    :param copyConnections: copy input and output connections
    :param deformOrder: Override the deform order of the blendshape. default is "FrontOfChain"
    :return:
    """

    if not isBlendshape(blendshape):
        raise Exception("'{}' is not a valid blendshape".format(blendshape))

    # get the base mesh
    base = getBaseGeometry(blendshape)

    blendshapeName = blendshapeName or "transfer__" + blendshape

    # create the new blendshape
    targetBlendshape = create(targetMesh, name=blendshapeName, deformOrder=deformOrder)

    # transfer the targets
    targetList = getTargetList(blendshape)
    for target in targetList:

        # get the base delta
        baseDelta = getDelta(blendshape=blendshape, target=target)

        # create a new base target with the same name
        addEmptyTarget(blendshape=targetBlendshape, target=target)
        # set the base delta
        setDelta(blendshape=targetBlendshape, target=target, deltaDict=baseDelta)

        # transfer each inbetween
        for iti in getInputTargetItemList(blendshape=blendshape, target=target, base=base):
            # if the index is the base (6000) we can skip it since we already transfered it.
            if iti == 6000:
                continue

            wt = itiToInbetween(iti)

            # get the inbetween delta
            inbetweenDelta = getDelta(blendshape=blendshape, target=target, inbetween=wt)
            # add a new inbetween target and set the delta
            addEmptyTarget(blendshape=targetBlendshape, target=target, inbetween=wt)
            setDelta(blendshape=targetBlendshape, target=target, deltaDict=inbetweenDelta, inbetween=wt)

        # set the target value
        targetValue = cmds.getAttr(f"{blendshape}.{target}")
        cmds.setAttr(f"{targetBlendshape}.{target}", targetValue)

        if copyConnections:
            # get the source value or input connection
            input = connection.getPlugInput(f"{blendshape}.{target}")
            if input:
                cmds.connectAttr(input[-1], f"{targetBlendshape}.{target}", f=True)
            # set the target value or input connection
            outputs = connection.getPlugOutput(f"{blendshape}.{target}")
            for output in outputs:
                cmds.connectAttr(f"{targetBlendshape}.{target}", output, f=True)

    # get the blendshape weights
    weights = getWeights(blendshape=blendshape, geometry=base)
    # set the blendshape weights
    setWeights(blendshape=targetBlendshape, weights=weights, geometry=targetMesh)

    return targetBlendshape