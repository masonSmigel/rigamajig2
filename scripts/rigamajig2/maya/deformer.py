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


def isDeformer(deformer):
    """
    Check if the deformer is a valid deformer
    :param deformer: name of deformer to check
    :return: True if Valid. False is invalid.
    """
    deformer = common.getFirstIndex(deformer)
    if not cmds.objExists(deformer): return False
    if not cmds.nodeType(deformer, i=True).count('weightGeometryFilter'): return False
    return True


def isSetMember(deformer, geo):
    """
    Check if the specified geo is a member of the deformer
    :param deformer:
    :param geo:
    :return:
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
    :param node: Node to retreive shape of
    :return:
    """

    if cmds.nodeType(node) in ['nurbsSurface', 'mesh', 'nurbsCurve']:
        node = cmds.listRelatives(node, p=True)
    shapes = cmds.listRelatives(node, s=True, ni=False) or []

    if len(shapes) == 1:
        return shapes[0]
    else:
        real_shapes = [x for x in shapes if not cmds.getAttr('{}.intermediateObject'.format(x))]
        return real_shapes[0] if len(real_shapes) else None


def reorderToTop(geo, deformer):
    """
    Reorder the deformer stack so the specifed deformer is at the top of the deformer stack for the geometries
    :param geo: geometries to act on
    :type geo: list | str
    :param deformer: deformer to reorder
    :type deformer: str
    """
    geo = common.toList(geo)
    for g in geo:
        stack = getDeformerStack(g)

        if len(stack) < 2:
            cmds.warning('Only One deformer found on geometry {}. Nothing to reorder'.format(geo))

        if deformer not in stack:
            cmds.error("Deformer '{}' was not found on the geometry '{}'".format(deformer, geo))
            continue

        stack = [d for d in stack if d != deformer]

        # reorder the deformer
        cmds.reorderDeformers(stack[0], deformer, g)
        cmds.reorderDeformers(deformer, stack[0], g)

    # Refresh UI
    cmds.channelBox('mainChannelBox', e=True, update=True)


def reorderToBottom(geo, deformer):
    """
    Reorder the deformer stack so the specifed deformer is at the bottom of the deformer stack for the geometries
    :param geo: geometries to act on
    :type geo: list | str
    :param deformer: deformer to reorder
    :type deformer: str
    """
    geo = common.toList(geo)
    for g in geo:
        stack = getDeformerStack(g)

        if len(stack) < 2:
            cmds.warning('Only One deformer found on geometry {}. Nothing to reorder'.format(geo))

        if deformer not in stack:
            cmds.error("Deformer '{}' was not found on the geometry '{}'".format(deformer, geo))
            continue

        stack = [d for d in stack if d != deformer]
        # reorder the deformer
        cmds.reorderDeformers(stack[-1], deformer, g)

    # Refresh UI
    cmds.channelBox('mainChannelBox', e=True, update=True)


def reorderSlide(geo, deformer, up=True):
    """
    Reorder the deformer stack so the specifed deformer up or down in the deformer stack.
    :param geo: geometries to act on
    :type geo: list | str
    :param deformer: deformer to reorder
    :type deformer: str
    :param up: if True move the deformer up in the deformer stack, false is down
    """
    geo = common.toList(geo)
    for g in geo:
        stack = getDeformerStack(g)

        if len(stack) < 2:
            cmds.warning('Only One deformer found on geometry {}. Nothing to reorder'.format(geo))

        if deformer not in stack:
            cmds.error("Deformer '{}' was not found on the geometry '{}'".format(deformer, geo))
            continue

        if stack.index(deformer) == 0 and up: return
        if stack.index(deformer) == len(stack) - 1 and not up: return

        neighbor = stack[stack.index(deformer) - 1] if up else stack[stack.index(deformer) + 1]
        # reorder the deformer
        if up:
            cmds.reorderDeformers(deformer, neighbor, g)
        else:
            cmds.reorderDeformers(neighbor, deformer, g)

    # Refresh UI
    cmds.channelBox('mainChannelBox', e=True, update=True)


def getDeformerStack(geo, ignoreTypes=['tweak']):
    """
    Return the whole deformer stack as a list
    :param geo: geometry object
    :param ignoreTypes: types of deformers to exclude from the list
    :return: list of deformers affecting the specified geo
    """
    geo = common.getFirstIndex(geo)

    inputs = cmds.ls(cmds.listHistory(geo, pruneDagObjects=True, interestLevel=1), type="geometryFilter")
    return [i for i in inputs if not cmds.nodeType(i) in ignoreTypes]


def getDeformersForShape(geo, ignoreTypes=['tweak']):
    """
    Return the whole deformer stack as a list
    :param geo: geometry object
    :param ignoreTypes: types of deformers to exclude from the list
    :return: list of deformers affecting the specified geo
    """
    geo = common.getFirstIndex(geo)
    result = []

    geometryFilters = cmds.ls(cmds.listHistory(geo), type="geometryFilter")
    shape = getDeformShape(geo)

    if shape is not None:
        shapeSets = cmds.ls(cmds.listConnections(shape), type='objectSet')

    for deformer in geometryFilters:
        deformerSet = cmds.ls(cmds.listConnections(deformer), type="objectSet")[0]
        if deformerSet in shapeSets:
            if not cmds.nodeType(deformer) in ignoreTypes:
                result.append(deformer)
    return result


def setDeformerOrder(geo, order, top=True):
    """
    Set the deformer order from bottom to top. Unspecified deformers appear at the top
    :param geo: geometry object name
    :param order: list of deformers in the desired order
    :param top: whether to start at the top of the list or bottom
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
    :param deformer: name of the deformer to get shapes from
    :return: list of mObjects a
    """
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return

    affectedObjects = list()

    deformerObj = omu.getMObject(deformer)
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
    :param deformer:
    :param geo:
    :return:
    """
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return

    geo = rigamajig2.maya.shape.getShapes(geo)
    if not geo:
        return
    deformed_geos = cmds.deformer(deformer, q=1, g=1, gi=1)
    if not deformed_geos:
        return

    # Get full path names in case a full path name was passed
    deformed_geos = cmds.ls(deformed_geos, l=1)
    geo = cmds.ls(geo, l=1)[0]

    # Get all used indexes
    deformed_indexes = cmds.deformer(deformer, q=1, gi=1)

    for n in range(len(deformed_geos)):
        if deformed_geos[n] == geo:
            return int(deformed_indexes[n])


def getWeights(deformer, geometry=None):
    """
    Get weights for the specified geometry.
    Optionally pass a geometry to get weights for specific geometry.
    :param deformer:
    :param geometry:
    :return:
    """
    weightList = dict()
    if not isDeformer(deformer):
        cmds.error("object '{}' is not a deformer".format(deformer))
        return

    if not geometry: geometry = common.getFirstIndex(getAffectedGeo(deformer))

    point_count = rigamajig2.maya.shape.getPointCount(geometry) - 1

    geometryIndex = getGeoIndex(deformer, geometry)

    attr = "{}.wl[{}].w[0:{}]".format(deformer, geometryIndex, point_count)
    attr_default_test = "{}.wl[{}].w[*]".format(deformer, geometryIndex)

    if not cmds.objExists(attr_default_test):
        values = [1 for _ in range(point_count + 1)]
    else:
        values = cmds.getAttr(attr)
        values = [round(float(v), 5) for v in values]

    weightList[0] = values
    return weightList


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
    point_count = rigamajig2.maya.shape.getPointCount(geometry) - 1

    geometryIndex = getGeoIndex(deformer, geometry)

    attr = "{}.wl[{}].w[0:{}]".format(deformer, geometryIndex, point_count)
    weightList = weights[0]
    cmds.setAttr(attr, *weightList)


def addGeoToDeformer(deformer, geo):
    """
    Add a geometry to an existing deformer
    :param deformer: deformer to add the new geo to
    :param geo: geo to add to the deformer
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
    :param deformer:
    :param geo:
    :return:
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
