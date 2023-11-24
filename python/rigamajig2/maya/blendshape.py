#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: blendshape.py
    author: masonsmigel
    date: 01/2021
    description: blendshape functions and helpers.
"""

from typing import List, Dict, Tuple

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

from rigamajig2.maya import connection
from rigamajig2.maya import deformer
from rigamajig2.maya import general
from rigamajig2.maya import mesh
from rigamajig2.maya import shape
from rigamajig2.shared import common


class BlendshapeOrigin:
    local = "local"
    world = "world"


def isBlendshape(blendshape: str) -> bool:
    """
    check if the blendshape is a valid blendshape

    :param blendshape: name of deformer to check
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    blendshape = common.getFirst(blendshape)
    if not cmds.objExists(blendshape) or not cmds.nodeType(blendshape) == "blendShape":
        return False
    return True


def create(
    base: str,
    targets: List[str] = None,
    origin: str = BlendshapeOrigin.local,
    deformOrder: str = None,
    name: str = None,
) -> str:
    """
    Create a blendshape deformer on the specified geometry

    :param str base: base shape of the blendshape
    :param str list targets: target shapes to add
    :param str origin: Optional - create the blendshape with a local or world origin
    :param str deformOrder: set the deformation order (use deformer.DeformOrder to get values)
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
    if deformOrder == deformer.DeformOrder.after:
        data["after"] = True
    elif deformOrder == deformer.DeformOrder.before:
        data["before"] = True
    elif deformOrder == deformer.DeformOrder.parallel:
        data["parallel"] = True
    elif deformOrder == deformer.DeformOrder.split:
        data["split"] = True
    elif deformOrder == deformer.DeformOrder.foc:
        data["foc"] = True

    blendshapeNode = cmds.blendShape(base, name=blendshapeName, origin=origin, **data)[
        0
    ]

    # add the blendshape targets
    for target in targets:
        addTarget(blendshape=blendshapeNode, target=target, base=base)

    return blendshapeNode


def addTarget(
    blendshape: str,
    target: str,
    targetAlias: str = None,
    base: str = None,
    targetIndex: int = -1,
    targetWeight: float = 0.0,
    topologyCheck: bool = False,
):
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

    cmds.blendShape(
        blendshape,
        edit=True,
        target=(base, targetIndex, target, 1.0),
        topologyCheck=topologyCheck,
    )

    targetName = targetAlias or getTargetName(blendshape, target)

    if targetAlias:
        renameTarget(blendshape, target, newName=targetAlias)

    if targetWeight:
        cmds.setAttr("{}.{}".format(blendshape, targetName), targetWeight)

    return "{}.{}".format(blendshape, targetName)


def addEmptyTarget(
    blendshape: str,
    target: str,
    base: str = None,
    targetIndex: int = -1,
    targetWeight: float = 0.0,
    inbetween: float = None,
    topologyCheck: bool = False,
) -> str:
    """
    Add an empty blendshape target from an existing blendshape node

    :param str blendshape: name of the blendshape node
    :param str  target: name of the target geometry to add. This will be a blank shape that doesn't exist in the scene.
    :param str base: base geometry of the blendshape. If Omitted use the first connected base
    :param int targetIndex: specified target index of the blendshape
    :param float inbetween:
    :param int float targetWeight: set the target weight
    :param  bool topologyCheck: check the topology of the model before adding the blendshape
    :return: plug of the new target added
    :rtype: str
    """

    if not base:
        base = getBaseGeometry(blendshape)
    blankTarget = deformer.createCleanGeo(base, name=f"tmp_{blendshape}_blendshapeNode")

    if inbetween:
        plug = addInbetween(
            blendshape,
            targetGeo=blankTarget,
            targetName=target,
            base=base,
            weight=inbetween,
        )
    else:
        plug = addTarget(
            blendshape,
            target=blankTarget,
            base=base,
            targetIndex=targetIndex,
            targetWeight=targetWeight,
            targetAlias=target,
            topologyCheck=topologyCheck,
        )

    cmds.delete(blankTarget)

    return plug


def addInbetween(
    blendshape, targetGeo, targetName, base=None, weight=0.5, absolute=True
) -> str:
    """
    Add a new target inbetween to the specified blendShape target

    :param str blendshape: Name of the blendshape node
    :param targetGeo: New target geo to add as an between target
    :param targetName: Name of the blendshape target to add the inbetween to
    :param str base: base geometry of the blendshape. If Omitted use the first connected base
    :param float weight: Set the weight of the target inbetween shape
    :param bool absolute: Add the between as an absolute target

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
    inbetweenType = "absolute" if absolute else "relative"
    cmds.blendShape(
        blendshape,
        edit=True,
        target=(base, targetIndex, targetGeo, weight),
        inBetween=True,
        inBetweenType=inbetweenType,
    )

    return "{}.{}".format(blendshape, targetName)


def getBaseGeometry(blendshape: str) -> str:
    """
    Get a list of blendshape geometry

    :param str blendshape: blendshape name to get the base geometry from
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a blendshape".format(blendshape))

    deformerObj = general.getMObject(blendshape)
    deformFn = oma.MFnGeometryFilter(deformerObj)

    baseObject = deformFn.getOutputGeometry()
    outputNode = om.MFnDagNode(baseObject[0])

    return outputNode.partialPathName()


def getBaseIndex(blendshape: str, base: str) -> str:
    """
    Get the index for a given base geometry

    :param blendshape: blendshape node
    :param base: base node
    :return:
    """
    # get the blendshape as a geometry filter
    deformerObj = general.getMObject(blendshape)
    deformFn = oma.MFnGeometryFilter(deformerObj)

    # get the deforming shape and an mObject for it.
    deformingShape = deformer.getDeformShape(base)
    deformingShapeMObj = general.getMObject(deformingShape)

    return deformFn.indexForOutputShape(deformingShapeMObj)


def getBlendshapeNodes(geometry: str) -> str:
    """
    Get the blendshape nodes
    :param geometry:
    :return: blendshape node attached to the geometry
    :rtype: str
    """
    deformers = deformer.getDeformerStack(geometry)
    blendshapeNodes = cmds.ls(deformers, type="blendShape")
    return blendshapeNodes


def getTargetList(blendshape: str) -> List[str]:
    """
    Get the list of connected targets
    :param str blendshape: Blendshape node to get the target list geometry from
    :return: list of targe indicies
    :rtype: list
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape node".format(blendshape))

    targetList = common.toList(cmds.listAttr(blendshape + ".w", multi=True))
    return common.toList(targetList)


def hasTargetGeo(
    blendShape: str, target: str, base: str = None, inbetween: float = None
) -> bool:
    """
    Check if the specified blendShape target has live target geometry.

    :param blendShape: Name of blendShape to query
    :param str target: BlendShape target to query
    :param str base: The base geometry index to check for live target geometry.
    :param float inbetween: Optional specify to get the between target at a specific value
    """
    # Check blendShape
    if not isBlendshape(blendShape):
        raise Exception(f"Object '{blendShape}' is not a valid blendShape node")

    if target not in getTargetList(blendShape):
        raise Exception(f"BlendShape '{blendShape}' has no target '{target}'")

    targetGeo = getTargetGeo(blendShape, target, base=base, inbetween=inbetween)

    return bool(targetGeo)


def getTargetGeo(
    blendShape: str,
    target: str,
    base: str = None,
    inbetween: float = None,
    plugs: bool = False,
) -> List[str]:
    """
    Get the connected target geometry given a blendShape and specified target.

    :param str blendShape: BlendShape node to get target geometry from
    :param str target: BlendShape target to get source geometry from
    :param str base: The base geometry of the blendshape to get the target geometry for.
                      If empty, use base geometry at geomIndex 0.
    :param inbetween: inbetween weight value to get the target of
    :param plugs: return the input as a plug not a node

    """
    targetIndex = getTargetIndex(blendShape, target)

    geomIndex = 0
    if base:
        geomIndex = deformer.getGeoIndex(baseGeo, blendShape)

    wtIndex = 6000 if not inbetween else inbetweenToIti(inbetween)

    targetGeoAttr = (
        blendShape
        + ".inputTarget["
        + str(geomIndex)
        + "].inputTargetGroup["
        + str(targetIndex)
        + "].inputTargetItem["
        + str(wtIndex)
        + "].inputGeomTarget"
    )
    targetGeoConn = cmds.listConnections(
        targetGeoAttr, shapes=True, destination=False, plugs=plugs
    )

    if not targetGeoConn:
        targetGeoConn = [""]

    return common.getFirst(targetGeoConn)


def getTargetIndex(blendshape: str, target: str) -> int:
    """
    Get the index of a blendshape target based on the target name

    :param str blendshape: blendshape
    :param target: target name to find an index of
    :return: index
    :rtype: int
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape node".format(blendshape))

    if isinstance(target, int):
        return target

    targetCount = cmds.blendShape(blendshape, query=True, target=True, weightCount=True)
    n = i = 0
    while n < targetCount:
        alias = cmds.aliasAttr(blendshape + ".w[{}]".format(i), query=True)
        if alias == target:
            return i
        if alias:
            n += 1
        i += 1
    return -1


def renameTarget(blendshape: str, target: str, newName: str) -> None:
    """
    Rename a given blendshape target to a new name. This is accomplished by using the blendshape attribute alias

    :param blendshape: blendshape node
    :param target: target to rename (current name)
    :param newName: target alias to use (new name)
    """

    allAliases = cmds.aliasAttr(blendshape, query=True)
    if target not in allAliases:
        raise ValueError(
            "BlendShape node '{}' doesn't have an alias '{}'".format(blendshape, target)
        )
    oldAliasIndex = allAliases.index(target) + 1
    oldAliasAttr = allAliases[oldAliasIndex]
    cmds.aliasAttr(newName, "{}.{}".format(blendshape, oldAliasAttr))


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

    targetShape = shape.getShapes(targetGeometry)
    if not targetShape:
        raise Exception("invalid shape on target geometry {}".format(targetGeometry))

    targetConnections = cmds.listConnections(
        targetShape,
        shapes=True,
        destination=True,
        source=False,
        plugs=False,
        connections=True,
    )

    if not targetConnections.count(blendshape):
        raise Exception(
            "Target geometry {} is not connected to blendshape {}".format(
                targetShape, blendshape
            )
        )

    targetConnectionIndex = targetConnections.index(blendshape)
    targetConnectionAttr = targetConnections[targetConnectionIndex - 1]
    targetConnectionPlug = cmds.listConnections(
        targetConnectionAttr,
        shapes=True,
        plugs=True,
        destination=True,
        source=False,
        type="blendShape",
    )[0]

    targetIndex = int(targetConnectionPlug.split(".")[2].split("[")[1].split("]")[0])
    targetAlias = cmds.aliasAttr(
        "{}.weight[{}]".format(blendshape, targetIndex), query=True
    )

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

    lastIndex = getTargetIndex(blendshape, common.getLast(targetList))
    nextIndex = lastIndex + 1

    return nextIndex


def getWeights(blendshape, targets=None, geometry=None):
    """
    Get blendshape target weights as well as the baseWeights.
    If no target or geometry are provided all targets are gathered, and the first geometry.

    :param str blendshape: blendshape node to get
    :param str list targets: list of targets to get the blendshape weights from
    :param str geometry: Optional name of the geometry to get the targets from.
                         By default, it will find the first geometry attached to the node.
    :return: dictionary of blendshape weights {"baseweights":[], "target":[]}
    :rtype: dict
    """
    weightList = dict()
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape target".format(blendshape))

    if not targets:
        targets = getTargetList(blendshape)
    if not geometry:
        geometry = cmds.blendShape(blendshape, query=True, geometry=True)[0]

    pointCount = shape.getPointCount(geometry) - 1

    # Get the target weights
    for target in targets:
        targetIndex = getTargetIndex(blendshape, target)

        targetAttr = "{}.it[0].itg[{}].tw[0:{}]".format(
            blendshape, targetIndex, pointCount
        )
        attrDefaultTest = "{}.it[0].itg[{}].tw[*]".format(blendshape, targetIndex)
        if not cmds.objExists(attrDefaultTest):
            values = [1 for _ in range(pointCount + 1)]
        else:
            values = cmds.getAttr(targetAttr)
            values = [round(v, 5) for v in values]

        optimizedDict = dict()
        for i, v in enumerate(values):
            if not abs(v - 1.0) <= 0.0001:
                optimizedDict[i] = v

        weightList[target] = optimizedDict

    # get the base weights
    targetAttr = "{}.it[0].baseWeights[0:{}]".format(blendshape, pointCount)
    attrDefaultTest = "{}.it[0].baseWeights[*]".format(blendshape)
    if not cmds.objExists(attrDefaultTest):
        values = [1 for _ in range(pointCount + 1)]
    else:
        values = cmds.getAttr(targetAttr)
        values = [round(v, 5) for v in values]

    # optimize the value list
    optimizedDict = dict()
    for i, v in enumerate(values):
        if not abs(v - 1.0) <= 0.0001:
            optimizedDict[i] = v

    weightList["baseWeights"] = optimizedDict

    return weightList


def setWeights(
    blendshape: str,
    weights: Dict[str, Dict[int, float]],
    targets: List[str] = None,
    geometry: str = None,
):
    """
    Set blendshape target weights as well as the baseWeights.
    If no target or geometry are provided all targets are gathered, and the first geometry is used

    :param str blendshape: blendshape node to get
    :param str weights: dictionary of weights
    :param str targets: Optional - influences to set. If None all are set from the weight.
                        optionally use "baseWeights" to set the base
    :param str geometry: Optional - Name of geometry to set weights on
    """
    if not isBlendshape(blendshape):
        raise Exception("{} is not a valid blendshape".format(blendshape))

    if not targets:
        targets = getTargetList(blendshape) + ["baseWeights"]
    if not geometry:
        geometry = common.getFirst(
            cmds.blendShape(blendshape, query=True, geometry=True)
        )

    targets = common.toList(targets)

    pointCount = shape.getPointCount(geometry) - 1

    for target in targets:
        if not target:
            continue

        if target == "baseWeights":
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
                tmpWeights.append(tmpWeight)

            targetAttr = "{}.inputTarget[0].baseWeights[0:{}]".format(
                blendshape, pointCount
            )
            cmds.setAttr(targetAttr, *tmpWeights)
        else:
            tmpWeights = list()
            for i in range(pointCount + 1):
                if weights[target].get(i) is not None:
                    tmpWeight = weights[target].get(i)
                elif weights[target].get(str(i)) is not None:
                    tmpWeight = weights[target].get(str(i))
                else:
                    tmpWeight = 1.0

                # finally append the weight to the list
                tmpWeights.append(tmpWeight)

            targetIndex = getTargetIndex(blendshape, target)
            targetAttr = "{}.inputTarget[0].itg[{}].tw[0:{}]".format(
                blendshape, targetIndex, pointCount
            )
            cmds.setAttr(targetAttr, *tmpWeights)


def getInputTargetItemList(blendshape, target, base=None):
    """
    Get the input targetItem attribute from a blendshape node and a target.
    This is handy if we want to rebuild the targets from deltas
    or just check if nodes are connected to the targets already

    :param blendshape: name of the blendshape node to get the target item plug
    :param target: name of the blendshape target to check
    :param base: Optional pass in a specific base to query from.
    :return:
    """

    targetIndex = getTargetIndex(blendshape, target=target)

    if not base:
        base = getBaseGeometry(blendshape)
    baseIndex = getBaseIndex(blendshape, base)
    targetItemAttr = getInputTargetItemAttr(blendshape, baseIndex, targetIndex)

    indices = cmds.getAttr(targetItemAttr, multiIndices=True)
    return indices


def itiToInbetween(iti) -> float:
    """
    Convert the inputTargetItem index into float representing the inbetween value
    (index = wt * 1000 + 5000)
    """
    return float((int(iti) - 5000) / 1000)


def inbetweenToIti(inbetween) -> int:
    """Convert the inbetween float an inputTargetItem index"""
    return int((float(inbetween) * 1000) + 5000)


def getInputTargetItemAttr(
    blendshape: str, baseIndex: int, targetIndex: int, inputTargetItem: int = None
):
    """
    Get the input target item attribute for a blendshape

    :param blendshape: blendshape node
    :param baseIndex: base index of the blendshape
    :param targetIndex: blendshape target index
    :param inputTargetItem: unique identifier for each target index (index = wt * 1000 + 5000)
    :return:
    """
    targetItemAttr = f"{blendshape}.inputTarget[{baseIndex}].inputTargetGroup[{targetIndex}].inputTargetItem"
    if inputTargetItem:
        targetItemAttr += f"[{inputTargetItem}]"
    return targetItemAttr


def getDelta(
    blendshape: str, target: str, inbetween: float = None, prune: int = 5
) -> Dict[int, Tuple[float, float, float]]:
    """
    Gather the deltas for each vertex in a blendshape node.

    To optimize the dictonary prune any deltas with a magnitude below 0.0001.
    This returns a dictonary containing only the deltas of vertices that have been modified

    :param blendshape: name of the blendshape to gather blendshape data from.
    :param target: name of the target to gather the delta information for
    :param inbetween: inbetween weight value Specify to get the delta of a specific target
    :param prune: number of decimal places to prune from position delta
    :return: a dictionary containing the vertex ID as the key, and a tuple representing the delta
    """
    if not isBlendshape(blendshape):
        raise Exception("'{}' is not a valid blendshape".format(blendshape))

    targetIndex = getTargetIndex(blendshape, target)

    base = getBaseGeometry(blendshape)
    baseIndex = getBaseIndex(blendshape, base)

    inputTargetItem = 6000 if not inbetween else inbetweenToIti(inbetween)

    inputTargetItemPlug = getInputTargetItemAttr(
        blendshape, baseIndex, targetIndex, inputTargetItem
    )
    geoTargetPlug = "{}.igt".format(inputTargetItemPlug)

    deltaPointList = dict()

    if (
        len(
            cmds.listConnections(geoTargetPlug, source=True, destination=False)
            or list()
        )
        > 0
    ):
        inputShape = cmds.listConnections(
            geoTargetPlug, source=True, destination=False, plugs=True
        )
        inputShape = inputShape[0].split(".")[0]

        targetPoints = mesh.getVertPositions(inputShape, world=False)

        origShape = deformer.getOrigShape(base)
        origPoints = mesh.getVertPositions(origShape, world=False)

        deltaPointList = dict()
        for i in range(len(targetPoints)):
            offset = om.MVector(targetPoints[i]) - om.MVector(origPoints[i])

            # check if the magnitude is within a very small vector before adding it.
            # This will help us cut down on file sizes.
            if offset.length() >= 0.0001:
                deltaPointList[str(i)] = (
                    round(offset.x, prune),
                    round(offset.y, prune),
                    round(offset.z, prune),
                )

    else:
        pointsTarget = cmds.getAttr("{}.ipt".format(inputTargetItemPlug))
        componentsTarget = common.flattenList(
            cmds.getAttr("{}.ict".format(inputTargetItemPlug))
        )

        for point, componentTarget in zip(pointsTarget, componentsTarget):
            vertexId = componentTarget.split("[")[-1].split("]")[0]

            prunedPoint = (
                round(point[0], prune),
                round(point[1], prune),
                round(point[2], prune),
            )
            deltaPointList[vertexId] = prunedPoint

    return deltaPointList


def setDelta(
    blendshape: str,
    target: str,
    deltaDict: Dict[int, Tuple[float, float, float]],
    inbetween: float = None,
) -> None:
    """
    Set the delta values on a given blendshape target.

    Using the deltaDict we set inputPointsTarget attributes of a given inputTargetItem Index attribute
    add in the delta values of the target

    specify an inbetween to set the delta for the given target. Otherwise, replace inputTargetItem index 6000.

    :param blendshape: Name of the blendshape node
    :param target: name of the target to set the delta on
    :param deltaDict: delta data dictionary of deltas for vertex IDs. Gathered from getDeltas
    :param inbetween: inbetween weight value
    """
    if not isBlendshape(blendshape):
        raise Exception("'{}' is not a valid blendshape".format(blendshape))

    targetIndex = getTargetIndex(blendshape, target)

    base = getBaseGeometry(blendshape)
    baseIndex = getBaseIndex(blendshape, base)

    inputTargetItem = 6000 if not inbetween else inbetweenToIti(inbetween)

    inputTargetItemPlug = getInputTargetItemAttr(
        blendshape, baseIndex, targetIndex, inputTargetItem
    )
    geoTargetPlug = "{}.igt".format(inputTargetItemPlug)

    if (
        len(
            cmds.listConnections(geoTargetPlug, source=True, destination=False)
            or list()
        )
        > 0
    ):
        raise Warning(
            "{}.{} has a live blendshape connection".format(blendshape, target)
        )

    else:
        pointsList = [deltaDict[p] for p in list(deltaDict.keys())]
        componentsList = ["vtx[{}]".format(p) for p in list(deltaDict.keys())]

        cmds.setAttr(
            f"{inputTargetItemPlug}.inputPointsTarget",
            len(pointsList),
            *pointsList,
            type="pointArray",
        )
        cmds.setAttr(
            f"{inputTargetItemPlug}.inputComponentsTarget",
            len(componentsList),
            *componentsList,
            type="componentList",
        )


def reconstructTargetFromDelta(blendshape, deltaDict, name=None):
    """
    Reconstruct a blendshape target from a given delta dictionary.
    The deltaDict contains a vertex ID and a delta position per item.
    If no delta exists for the given vertex ID default to the position from the orig shape

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

    for vertexId in list(deltaDict.keys()):
        origPoint = om.MPoint(origShapePoints[int(vertexId)])
        delta = om.MVector(deltaDict[vertexId])

        absPoint = origPoint + delta
        absPoint = [absPoint.x, absPoint.y, absPoint.z]

        cmds.xform(
            "{}.vtx[{}]".format(targetGeo, vertexId),
            objectSpace=True,
            translation=absPoint,
        )

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

    inputTargetItemPlug = "{}.it[{}].itg[{}].iti[{}]".format(
        blendshape, baseIndex, targetIndex, inputTargetItem
    )

    # check if an inputTargetItem exists for the given inbetween
    if inputTargetItem not in getInputTargetItemList(blendshape, target):
        raise ValueError(
            "No inbetween exists for '{}.{}' at the inbetween {}".format(
                blendshape, target, inbetween
            )
        )

    # check if the plug is already connected to geometry
    if cmds.listConnections(
        "{}.igt".format(inputTargetItemPlug), source=True, destination=False, plugs=True
    ):
        print("{}.{} is already connected to input geometry".format(blendshape, target))
        return

    # if its not we can reconstruct the delta then connect it to the inputGeometryTarget plug.
    else:
        ibName = "{}_ib{}".format(
            target, str(inbetween).replace(".", "_").replace("-", "neg")
        )
        targetGeoName = target if not inbetween else ibName
        deltaDict = getDelta(blendshape, target, inbetween=inbetween)
        targetGeo = reconstructTargetFromDelta(
            blendshape, deltaDict=deltaDict, name=targetGeoName
        )

        targetGeoShape = cmds.listRelatives(targetGeo, shapes=True)[0]
        if connect:
            cmds.connectAttr(
                "{}.worldMesh[0]".format(targetGeoShape),
                "{}.igt".format(inputTargetItemPlug),
                force=True,
            )

        return targetGeo


def transferBlendshape(
    blendshape: str,
    targetMesh: str,
    blendshapeName: str = None,
    copyConnections: bool = True,
    deformOrder: str = deformer.DeformOrder.foc,
) -> str:
    """
    Transfer a blendshape from one node to another.

    :param blendshape: Blendshape to copy to another mesh
    :param targetMesh: mesh to transfer the blendshape to
    :param blendshapeName: name of the new blendshape
    :param copyConnections: copy input and output connections
    :param deformOrder: Override the deform order of the blendshape. default is "FrontOfChain"
    :return: new blendshape node
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
        for iti in getInputTargetItemList(
            blendshape=blendshape, target=target, base=base
        ):
            # if the index is the base (6000) we can skip it since we already transferred it.
            if iti == 6000:
                continue

            wt = itiToInbetween(iti)

            inbetweenDelta = getDelta(
                blendshape=blendshape, target=target, inbetween=wt
            )
            addEmptyTarget(blendshape=targetBlendshape, target=target, inbetween=wt)
            setDelta(
                blendshape=targetBlendshape,
                target=target,
                deltaDict=inbetweenDelta,
                inbetween=wt,
            )

        targetValue = cmds.getAttr(f"{blendshape}.{target}")
        cmds.setAttr(f"{targetBlendshape}.{target}", targetValue)

        if copyConnections:
            inputTargetConnections = common.getLast(
                connection.getPlugInput(f"{blendshape}.{target}")
            )
            if inputTargetConnections:
                cmds.connectAttr(
                    inputTargetConnections, f"{targetBlendshape}.{target}", force=True
                )
            outputs = connection.getPlugOutput(f"{blendshape}.{target}")
            for output in outputs:
                cmds.connectAttr(f"{targetBlendshape}.{target}", output, force=True)

    weights = getWeights(blendshape=blendshape, geometry=base)
    setWeights(blendshape=targetBlendshape, weights=weights, geometry=targetMesh)

    return targetBlendshape
