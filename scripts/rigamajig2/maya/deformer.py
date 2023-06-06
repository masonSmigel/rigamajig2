"""
Functions for deformers
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.OpenMayaAnim as oma
import maya.OpenMaya as om
import rigamajig2.shared.common as common
import rigamajig2.maya.openMayaUtils as omu
import rigamajig2.maya.shape
import rigamajig2.maya.mesh


def isDeformer(deformer):
    """
    Check if the deformer is a valid deformer

    :param str deformer: name of deformer to check
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    deformer = common.getFirstIndex(deformer)
    if not cmds.objExists(deformer): return False
    if not cmds.nodeType(deformer, i=True).count('weightGeometryFilter'): return False
    return True


def isSetMember(deformer, geo):
    """
    Check if the specified geo is a member of the deformer

    :param str deformer: name of the deformer to check
    :param str geo: name of the geometry to compare against
    :return: True if the the given deformer a set member of the deformer
    :rtype: bool
    """
    shape = geo
    if cmds.nodeType(geo) == 'transform':
        shape = cmds.listRelatives(geo, s=True, ni=True)[0]

    if shape in getAffectedGeo(deformer):
        return True
    else:
        return False


def getDeformShape(node):
    """
    Get the visible geo regardless of deformations applied

    :param str node: Name of the node to retreive shape node from
    """

    if cmds.nodeType(node) in ['nurbsSurface', 'mesh', 'nurbsCurve']:
        node = cmds.listRelatives(node, p=True)
    shapes = cmds.listRelatives(node, s=True, ni=False) or []

    if len(shapes) == 1:
        return shapes[0]
    else:
        realShapes = [x for x in shapes if not cmds.getAttr('{}.intermediateObject'.format(x))]
        return realShapes[0] if len(realShapes) else None


def reorderToTop(geometry, deformer):
    """
    Reorder the deformer stack so the specifed deformer is at the top of the deformer stack for the geometries

    :param str list geometry: geometries to act on
    :param str deformer: deformer to reorder
    """
    geometry = common.toList(geometry)
    for geo in geometry:
        stack = getDeformerStack(geo)

        if len(stack) < 2:
            cmds.warning('Only One deformer found on geometry {}. Nothing to reorder'.format(geometry))

        if deformer not in stack:
            cmds.error("Deformer '{}' was not found on the geometry '{}'".format(deformer, geometry))
            continue

        stack = [d for d in stack if d != deformer]

        # reorder the deformer
        cmds.reorderDeformers(stack[0], deformer, geo)
        cmds.reorderDeformers(deformer, stack[0], geo)

    # Refresh UI
    cmds.channelBox('mainChannelBox', e=True, update=True)


def reorderToBottom(geometry, deformer):
    """
    Reorder the deformer stack so the specifed deformer is at the bottom of the deformer stack for the geometries

    :param str list geometry: geometries to act on
    :param str deformer: deformer to reorder
    """
    geometry = common.toList(geometry)
    for geo in geometry:
        stack = getDeformerStack(geometry)

        if len(stack) < 2:
            cmds.warning('Only One deformer found on geometry {}. Nothing to reorder'.format(geo))

        if deformer not in stack:
            cmds.error("Deformer '{}' was not found on the geometry '{}'".format(deformer, geo))
            continue

        stack = [d for d in stack if d != deformer]
        # reorder the deformer
        cmds.reorderDeformers(stack[-1], deformer, geo)

    # Refresh UI
    cmds.channelBox('mainChannelBox', e=True, update=True)


def reorderSlide(geometry, deformer, up=True):
    """
    Reorder the deformer stack so the specifed deformer up or down in the deformer stack.

    :param list str geometry: geometries to act on
    :param str deformer: deformer to reorder
    :param bool up: if True move the deformer up in the deformer stack, false is down
    """
    geometry = common.toList(geometry)
    for geo in geometry:
        stack = getDeformerStack(geo)

        if len(stack) < 2:
            cmds.warning('Only One deformer found on geometry {}. Nothing to reorder'.format(geometry))

        if deformer not in stack:
            cmds.error("Deformer '{}' was not found on the geometry '{}'".format(deformer, geometry))
            continue

        if stack.index(deformer) == 0 and up: return
        if stack.index(deformer) == len(stack) - 1 and not up: return

        neighbor = stack[stack.index(deformer) - 1] if up else stack[stack.index(deformer) + 1]
        # reorder the deformer
        if up:
            cmds.reorderDeformers(deformer, neighbor, geo)
        else:
            cmds.reorderDeformers(neighbor, deformer, geo)

    # Refresh UI
    cmds.channelBox('mainChannelBox', e=True, update=True)


def getDeformerStack(geo, ignoreTypes=None):
    """
    Return the whole deformer stack as a list

    :param str geo: geometry object
    :param list ignoreTypes: types of deformers to exclude from the list
    :return: list of deformers affecting the specified geo
    :rtype: list
    """

    ignoreTypes = ignoreTypes or ['tweak']
    geo = common.getFirstIndex(geo)

    inputs = cmds.ls(cmds.listHistory(geo, pruneDagObjects=True, interestLevel=1), type="geometryFilter")

    # sometimes deformers can be connected to inputs that dont affect the deformation of the given geo.
    # This happens alot in blendshapes where one blendshape drives a bunch of others for small details.
    # we need to filter out any deformers from this list that dont affect the given geo.
    deformShape = getDeformShape(geo)
    for i in inputs:
        tgtDeformShape = common.getFirstIndex(cmds.deformer(i, q=1, g=1, gi=1))
        if tgtDeformShape != deformShape:
            inputs.remove(i)

    return [i for i in inputs if not cmds.nodeType(i) in ignoreTypes]


def getDeformersForShape(geo, ignoreTypes=None, ignoreTweaks=True):
    """
    Return the whole deformer stack as a list

    :param str geo: geometry object
    :param list ignoreTypes: types of deformers to exclude from the list
    :param bool ignoreTweaks: Ignore tweak nodes from the deformer list
    :return: list of deformers affecting the specified geo
    :rtype: list
    """
    ignoreTypes = ignoreTypes or list()

    geo = common.getFirstIndex(geo)
    result = []
    if ignoreTweaks:
        ignoreTypes += ['tweak']

    geometryFilters = cmds.ls(cmds.listHistory(geo), type="geometryFilter")
    shape = getDeformShape(geo)

    if shape is not None:
        shapeSets = cmds.ls(cmds.listConnections(shape), type='objectSet')

    for deformer in geometryFilters:
        # first lets try to use this using the old version from Maya2020.
        # if that fails we can ty another method.
        deformerSet = cmds.ls(cmds.listConnections(deformer), type="objectSet") or list()
        if deformerSet:
            if deformerSet[0] in shapeSets:
                # in almost every case we
                if not cmds.nodeType(deformer) in ignoreTypes:
                    result.append(deformer)

        else:
            result = cmds.deformableShape(shape, chain=True)

    return result


def getOrigShape(node):
    """
    Get an orig shape from the given geometry node

    :param node:  geometry or deformer name to get the orig shape for
    :return: orig shape or orig shape output plug
    """
    deformShape = getDeformShape(node)
    origShape = common.getFirstIndex(cmds.deformableShape(deformShape, originalGeometry=True))

    origShape = origShape.split(".")[0]
    return origShape


def createCleanGeo(geo, name=None):
    """
    create a completely clean version of the given geo. To do this we will revert the mesh to the shape of the orig shape

    :param geo: name of the geometry to create a clean shape for
    :param name: name for the newly created clean geometery
    :return:
    """
    dupGeo = cmds.duplicate(geo)[0]
    if not name: name = "{}_clean".format(geo)

    dupGeo = cmds.rename(dupGeo, name)
    origShape = getOrigShape(geo)
    shapes = cmds.listRelatives(dupGeo, s=True)

    # get the point positions of the orig shape
    origPoints = rigamajig2.maya.mesh.getVertPositions(origShape, world=False)

    # delete all intermediate shapes
    for shape in shapes:
        if cmds.getAttr("{}.intermediateObject".format(shape)):
            cmds.delete(shape)

    # set the point positions the ones from the orig shape
    rigamajig2.maya.mesh.setVertPositions(dupGeo, vertList=origPoints, world=False)

    return dupGeo


def setDeformerOrder(geo, order, top=True):
    """
    Set the deformer order from bottom to top. Unspecified deformers appear at the top

    :param str geo: geometry object name
    :param list order: list of deformers in the desired order
    :param bool top: whether to start at the top of the list or bottom
    """
    if top:
        order.reverse()
        for deformer in order:
            reorderToTop(geo, deformer)
    else:
        for deformer in order:
            reorderToBottom(geo, deformer)


def getAffectedGeo(deformer):
    """
    Get all geometry affected by the specified deformer

    :param str deformer: name of the deformer to get shapes from
    :return: list of mObjects a
    :rtype: list
    """
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return

    affectedObjects = list()

    deformerObj = omu.getOldMObject(deformer)
    deformFn = oma.MFnGeometryFilter(deformerObj)

    outputObjs = om.MObjectArray()
    deformFn.getOutputGeometry(outputObjs)
    for i in range(outputObjs.length()):
        outputIndex = deformFn.indexForOutputShape(outputObjs[i])
        outputNode = om.MFnDagNode(outputObjs[i])

        affectedObjects.append(outputNode.partialPathName())
    return affectedObjects


def getGeoIndex(deformer, geo):
    """
    Get the index of specifed geo in the deformer

    :param deformer: name of the deformer to
    :param geo:
    :return:
    """
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return

    geo = rigamajig2.maya.shape.getShapes(geo)
    if not geo:
        return
    deformedGeometry = cmds.deformer(deformer, q=1, g=1, gi=1)
    if not deformedGeometry:
        return

    # Get full path names in case a full path name was passed
    deformedGeometry = cmds.ls(deformedGeometry, l=1)
    geo = cmds.ls(geo, l=1)[0]

    # Get all used indexes
    deformedIndecies = cmds.deformer(deformer, q=1, gi=1)

    for n in range(len(deformedGeometry)):
        if deformedGeometry[n] == geo:
            return int(deformedIndecies[n])


def getWeights(deformer, geometry=None):
    """
    Get weights for the specified geometry.
    Optionally pass a geometry to get weights for specific geometry.

    :param str deformer: deformer to get the geometry weights for
    :param str geometry: name fo the geometry to get the weights for
    :return: a dictionary of geometry indices and a list of deformer weights ie {0: [1, 1, 1, 0, ...]
    :rtype: dict
    """
    weightList = dict()
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return

    if not geometry: geometry = common.getFirstIndex(getAffectedGeo(deformer))

    pointCount = rigamajig2.maya.shape.getPointCount(geometry) - 1

    geometryIndex = getGeoIndex(deformer, geometry)

    attr = "{}.wl[{}].w[0:{}]".format(deformer, geometryIndex, pointCount)
    attrDefaultTest = "{}.wl[{}].w[*]".format(deformer, geometryIndex)

    if not cmds.objExists(attrDefaultTest):
        values = [1 for _ in range(pointCount + 1)]
    else:
        values = cmds.getAttr(attr)
        values = [round(float(v), 5) for v in values]

    opimizedDict = dict()
    # optimize the value list
    for i, v in enumerate(values):
        # if the weights are almost equal to one skip adding them.
        if not abs(v - 1.0) <= 0.0001:
            opimizedDict[i] = v

    return opimizedDict


def setWeights(deformer, weights, geometry=None):
    """
    Set the specified deformer weights.
    Optionally pass a geometry to set weights for specific geometry.

    :param deformer: deformer to set the weights of
    :param weights: list of weights to set
    :param geometry: Optional- geometry to set the attributes of.
                If ommited the first geometry of the deformer will be used.
    """
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return

    if not geometry: geometry = common.getFirstIndex(getAffectedGeo(deformer))
    pointCount = rigamajig2.maya.shape.getPointCount(geometry) - 1

    geometryIndex = getGeoIndex(deformer, geometry)
    if geometryIndex is None:
        raise Exception(f"The geometry '{geometry}' is not part of the deformer set for '{deformer}'")

    tmpWeights = list()
    for i in range(pointCount + 1):
        # we need to check if there are weights in the dictionary. We can use get to check and return None if
        # there is not a key for the specified weight. After that we can check if the weight == None. If we does
        # we replace it with 1.0 since we stripped out any values at 1.0 when we gathered the weights
        if weights.get(i) is not None:
            tmpWeight = weights.get(i)
        elif weights.get(str(i)) is not None:
            tmpWeight = weights.get(str(i))
        else:
            tmpWeight = 1.0

        if tmpWeight is None: tmpWeight = 1.0
        # finally append the weight to the list
        tmpWeights.append(tmpWeight)

    attr = "{}.wl[{}].w[0:{}]".format(deformer, geometryIndex, pointCount)
    weightList = tmpWeights
    cmds.setAttr(attr, *weightList)


def addGeoToDeformer(deformer, geo):
    """
    Add a geometry to an existing deformer

    :param str deformer: deformer to add the new geo to
    :param str geo: geo to add to the deformer
    """
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return
    if not cmds.objExists(geo):
        cmds.error("object '{}' does not exist".format(geo))
        return

    cmds.deformer(deformer, e=True, g=geo)


def removeGeoFromDeformer(deformer, geo):
    """
    Remove the specifed geometry from the deformer

    :param str deformer: name of the deformer to remove from the geometry
    :param str geo: name of the geometry to remove the deformer from
    """
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return
    if not cmds.objExists(geo):
        cmds.error("object '{}' does not exist".format(geo))
        return
    cmds.deformer(deformer, e=True, rm=True, g=geo)

# def getDeformerSet(deformer):
#     """
#     Get the name of a deformer set for the specified deformer
#     :param deformer: name of the deformer to get the deformer set for
#     :return: name of the deformer set
#     """
#     if not cmds.objExists(deformer):
#         cmds.error("object '{}' does not exist".format(deformer))
#         return
#     if not cmds.objExists(deformer):
#         cmds.error("object '{}' is not a deformer".format(deformer))
#         return
#
#     deformerFn = getDeformerFn(deformer)
#     deformerSetObj = deformerFn.deformerSet()
#     if deformerSetObj.isNull():
#         cmds.error("Could not locate deformer set for '{}'".format(deformer))
#         return None
#     return om.MFnDependencyNode(deformerSetObj).name()

# def getDeformerFn(deformer):
#     """
#     Get an MFnWeightGeometryFilter for the specified deformer. Uses maya.OpenMaya to utlize MFnWeightGeometryFilter
#     :param deformer: name of deformer to get GeometryFilterMFn for
#     :type deformer: str
#     :return: MFnWeightGeometryFilter
#     """
#     if not isDeformer(deformer):
#         cmds.error("Deformer {} does not exist".format(deformer))
#         return
#
#     deformObj = utils.getOldMObject(deformer)
#
#     try:
#         deformerFn = oma.MFnWeightGeometryFilter(deformObj)
#         pass
#     except:
#         cmds.error("Unable to get geometry filter for deformer '{}'".format(deformer))
#         return
#
#     return deformerFn


# def getDeformerSetFn(deformer):
#     """
#     Get the deformer set of a deformer
#     :param deformer:  name of deformer to get deformer set Fn for
#     :return:
#     """
#     if not cmds.objExists(deformer):
#         cmds.error("object '{}' is not a deformer".format(deformer))
#         return
#
#     deformerSet = getDeformerSet(deformer)
#
#     deformerSetObj = utils.getOldMObject(deformerSet)
#     return om.MFnSet(deformerSetObj)

# def getSetMembers(deformer, geo=None):
#     """
#     Get set members of a deformer
#     :param deformer: name of the deformer to get set members of
#     :param geo: Optional -  specified geo to get the set members of. If Ommited the first geo will be returned
#     :return: MDagPath to the affected shape, MObject for the affected components
#     :rtype: list
#     """
#     deformerSetFn = getDeformerSetFn(deformer)
#
#     deformerSetSel = om.MSelectionList()
#     deformerSetFn.getMembers(deformerSetSel, True)
#     deformerSetPath = om.MDagPath()
#     deformerSetObj = om.MObject()
#
#     if geo:
#         index = getGeoIndex(deformer, geo)
#     else:
#         index = 0
#
#     if index >= deformerSetSel.length():
#         cmds.error('Geo index is out of range')
#         return
#     deformerSetSel.getDagPath(index, deformerSetPath, deformerSetObj)
#
#     return [deformerSetPath, deformerSetObj]


# def getSetMembersStrList(deformer, geo=None):
#     """
#     Get the set members of the specifed deformer as a string list.
#     :param deformer:  name of the deformer to get set members of
#     :param geo: Optional -  specified geo to get the set members of
#     :return: list of compoents affected by the deformer
#     """
#     deformerSetFn = getDeformerSetFn(deformer)
#
#     deformerSetSel = om.MSelectionList()
#     deformerSetFn.getMembers(deformerSetSel, True)
#
#     setMembersStr = list()
#     deformerSetSel.getSelectionStrings(setMembersStr)
#     setMembersStr = cmds.ls(setMembersStr, flatten=True)
#
#     if geo is not None:
#         geoSetMemberStr = list()
#         for x in setMembersStr:
#             if geo in x:
#                 geoSetMemberStr.append(x)
#         return geoSetMemberStr
#
#     return setMembersStr
