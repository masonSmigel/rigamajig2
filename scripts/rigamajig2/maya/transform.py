"""
Utilities for transforms
"""
import math
import maya.cmds as cmds
import maya.api.OpenMaya as om2

import rigamajig2.maya.hierarchy as dag
import rigamajig2.shared.common as common
import rigamajig2.maya.matrix as matrix
import rigamajig2.maya.mathUtils as mathUtils

ROTATEORDER = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']


def matchTransform(source, target):
    """
    Match the translation and Rotation of the source to the target object

    :param str source: source transfrom
    :param str target: transform to snap
    """
    matchTranslate(source, target)
    matchRotate(source, target)


def matchTranslate(source, target):
    """
    Match the translation of one object to another.

    :param str source: Source transfrom
    :param str target:  Target transform to match
    """
    pos = getAveragePoint(source)
    cmds.xform(target, ws=True, t=pos)


def matchRotate(source, target):
    """
    Match the rotation of one object to another rotation.
    This matching method is awesome. It works across regardless of mismatched rotation orders or transforms who's
    parents have different rotation orders.

    :param str source: Source transfrom
    :param str target:  Target transform to match
    """
    rotOrder = cmds.getAttr('{}.rotateOrder'.format(source))
    matrixList = cmds.getAttr('{}.worldMatrix'.format(source))

    # Create an empty MMatrix from the world space matrix:
    mMatrix = om2.MMatrix(matrixList)  # MMatrix
    mTransformMtx = om2.MTransformationMatrix(mMatrix)
    eulerRot = mTransformMtx.rotation()  # MEulerRotation

    # Update rotate order to match original object
    eulerRot.reorderIt(rotOrder)

    angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]
    cmds.xform(target, ws=True, rotation=angles)


def freezeToParentOffset(nodes):
    """
    Freeze the given transform nodes by adding their values to the offsetParentMatrix

    :param list nodes: transform nodes to freeze
    """
    nodes = common.toList(nodes)

    if cmds.about(api=True) < 20200000:
        raise RuntimeError("OffsetParentMatrix is only available in Maya 2020 and beyond")
    for node in nodes:
        offset = localOffset(node)
        cmds.setAttr("{}.{}".format(node, 'offsetParentMatrix'), list(offset), type="matrix")
        resetTransformations(node)


def unfreezeToTransform(nodes):
    """
    remove postional information from the offset parent matrix and add it to the main transformation

    :param list nodes: nodes to match mostions
    """
    nodes = common.toList(nodes)
    identityMatrix = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]

    if cmds.about(api=True) < 20200000:
        raise RuntimeError("OffsetParentMatrix is only available in Maya 2020 and beyond")
    for node in nodes:
        offest = localOffset(node)
        cmds.xform(node, m=offest)
        cmds.setAttr("{}.offsetParentMatrix".format(node), identityMatrix, type='matrix')


def connectOffsetParentMatrix(driver, driven, mo=False, t=True, r=True, s=True, sh=True):
    """
    Create a connection between a driver and driven node using the offset parent matrix.
    the maintain offset option creates a transform node to store the offset.
    the t, r, s, sh attributes can be used to select only some transformations to affect the driven using a pickMatrix node.

    :param str driver: driver node
    :param str driven: driven node(s)
    :param bool mo: add a transform node to store the offset between the driver and driven nodes
    :param bool t: Apply translation transformations
    :param bool r: Apply rotation transformations
    :param bool s: Apply scale transformations
    :param bool sh: Apply shear transformations
    :return: multmatrix,  pickmatrix
    :rtype: list
    """
    if cmds.about(api=True) < 20200000:
        raise RuntimeError("OffsetParentMatrix is only available in Maya 2020 and beyond")
    drivens = common.toList(driven)

    for driven in drivens:
        offset = list()
        if mo:
            offset = offsetMatrix(driver, driven)

        parentList = cmds.listRelatives(driven, parent=True, path=True)
        parent = parentList[0] if parentList else None

        if not parent and not mo:
            outputPlug = "{}.{}".format(driver, 'worldMatrix')
        else:
            multMatrix = cmds.createNode("multMatrix", name="{}_{}_mm".format(driver, driven))
            if offset:
                cmds.setAttr("{}.{}".format(multMatrix, "matrixIn[0]"), offset, type='matrix')

            cmds.connectAttr("{}.{}".format(driver, 'worldMatrix'), "{}.{}".format(multMatrix, 'matrixIn[1]'), f=True)

            if parent:
                cmds.connectAttr("{}.{}".format(parent, 'worldInverseMatrix'),
                                 "{}.{}".format(multMatrix, 'matrixIn[2]'),
                                 f=True)
            outputPlug = "{}.{}".format(multMatrix, 'matrixSum')

        pickMat = None
        if not t or not r or not s or not sh:
            # connect the output into a pick matrix node
            pickMat = cmds.createNode('pickMatrix', name="{}_{}_pickMatrix".format(driver, driven))
            cmds.connectAttr(outputPlug, "{}.inputMatrix".format(pickMat))
            cmds.setAttr(pickMat + '.useTranslate', t)
            cmds.setAttr(pickMat + '.useRotate', r)
            cmds.setAttr(pickMat + '.useScale', s)
            cmds.setAttr(pickMat + '.useShear', sh)
            outputPlug = pickMat + '.outputMatrix'

        cmds.connectAttr(outputPlug, "{}.{}".format(driven, 'offsetParentMatrix'), f=True)

        # now we need to reset the trs
        resetTransformations(driven)

    return multMatrix, pickMat


def blendedOffsetParentMatrix(driver1, driver2, driven, mo=False, t=True, r=True, s=True, sh=True, blend=0):
    """
    Create a blended offset parent matrix connection setup

    :param driver1: first driver node
    :param driver2: second driver node
    :param driven: driven node
    :param bool mo: add a transform node to store the offset between the driver and driven nodes
    :param bool t: Apply translation transformations
    :param bool r: Apply rotation transformations
    :param bool s: Apply scale transformations
    :param bool sh: Apply shear transformations
    :param blend: default blend between the driver1 and driver2.
    :return: blend Matrix node
    """
    mm1, pick1 = connectOffsetParentMatrix(driver1, driven, mo=mo, t=t, r=r, s=s, sh=sh)
    mm2, pick2 = connectOffsetParentMatrix(driver2, driven, mo=mo, t=t, r=r, s=s, sh=sh)

    blendMatrix = cmds.createNode("blendMatrix", n="{}_blendMatrix".format(driven))

    # connect the other two matricies into the blendMatrix
    matrix1Out = "{}.outputMatrix".format(pick1) if pick1 else "{}.matrixSum".format(mm1)
    matrix2Out = "{}.outputMatrix".format(pick2) if pick2 else "{}.matrixSum".format(mm2)

    cmds.connectAttr(matrix1Out, "{}.inputMatrix".format(blendMatrix))
    cmds.connectAttr(matrix2Out, "{}.target[0].targetMatrix".format(blendMatrix))

    # connect the blend matrix back to the joint
    cmds.connectAttr("{}.outputMatrix".format(blendMatrix), "{}.offsetParentMatrix".format(driven), f=True)
    cmds.setAttr("{}.envelope".format(blendMatrix), blend)

    return blendMatrix


def multiMatrixConstraint(driverList, driven, valueList, mo=True, t=True, r=True, s=True, sh=True):
    """
    Create a multi blended matrix constraint. This will blend the input matrix of the drivers into the driven node

    :param driverList: list of driver nodes
    :param valueList: list of driver weight values
    :param driven: driven node
    :param bool mo: add a transform node to store the offset between the driver and driven nodes
    :param bool t: Apply translation transformations
    :param bool r: Apply rotation transformations
    :param bool s: Apply scale transformations
    :param bool sh: Apply shear transformations
    """
    if not mathUtils.isEqual(sum(valueList), 1):
        cmds.warning("Value list is not normalized. This may produce unexpected results")

    wtAddMatrix = cmds.createNode("wtAddMatrix", name="{}_multiBlended_wtAddMatrix".format(driven))

    # check if the list of drivers and valyes are the same lengh
    if not len(driverList) == len(valueList):
        raise ValueError(
            "Must provide an equal amount of drivers and values. drivers ({}) != values ({})".format(len(driverList),
                                                                                                     len(valueList)))

    # for each driver in the list of drivers connect it to the wtAddMatrix
    for i in range(len(driverList)):
        driver = driverList[i]
        value = valueList[i]

        mm, pickMatrix = connectOffsetParentMatrix(driver, driven, mo=mo, t=t, r=r, s=s, sh=sh)

        # check if a pick matrix node was created. If so use that to connect to the wtAddMatrix. If not use the multMatrix
        if pickMatrix:
            outPlug = "{}.outputMatrix"
        else:
            outPlug = "{}.matrixSum".format(mm)

        # connect the out plug into the wtAddMatrix
        cmds.connectAttr(outPlug, "{}.wtMatrix[{}].matrixIn".format(wtAddMatrix, i))
        cmds.setAttr("{}.wtMatrix[{}].weightIn".format(wtAddMatrix, i), value)

    # connect the wtAddMatrix to the driven offsetParentMatrix
    cmds.connectAttr("{}.matrixSum".format(wtAddMatrix), "{}.{}".format(driven, 'offsetParentMatrix'), f=True)

    return wtAddMatrix


def localOffset(node):
    """
    Get the local offset matrix of a node relative to its parent.

    :param node: name of the node
    :return: offset matrix between the given node and its parent
    :rtype: MMatrix
    """
    offset = om2.MMatrix(cmds.getAttr('{}.{}'.format(node, 'worldMatrix')))
    parent = cmds.listRelatives(node, parent=True, path=True) or None
    if parent:
        parentInverse = om2.MMatrix(cmds.getAttr('{}.{}'.format(parent[0], 'worldInverseMatrix')))
        offset *= parentInverse
    return offset


def offsetMatrix(node1, node2):
    """
    Calculate an offset matrix between two nodes. 
    Returns the matrix of node2 relative to node 1

    :param node1: first node
    :param node2: second node
    :return: relative offset matrix between node1 and node2
    :rtype: MMatrix
    """
    node1Matrix = om2.MMatrix(cmds.getAttr("{}.{}".format(node1, 'worldMatrix')))
    node2Matrix = om2.MMatrix(cmds.getAttr("{}.{}".format(node2, 'worldMatrix')))

    # invert the parent matrix
    node1Inverted = om2.MTransformationMatrix(node1Matrix).asMatrixInverse()
    offset = node2Matrix * node1Inverted

    return offset


def getAveragePoint(transforms):
    """
    Get the average point between a list of transforms.

    :param transforms: list of transforms to average
    :return: average postion between a list of transforms
    :rtype: list
    """
    transforms = common.toList(transforms)

    avPoint = om2.MPoint(0, 0, 0)
    for tranform in transforms:
        if not cmds.objExists(tranform):
            cmds.warning("Object does not exist")
        p = om2.MPoint(cmds.xform(tranform, q=True, ws=True, rp=True))
        avPoint += p

    result = avPoint / len(transforms)
    return result.x, result.y, result.z


def mirror(trs=None, axis='x', leftToken=None, rightToken=None, mode='rotate'):
    """
    Mirrors transform axis vector. Searches for a destination node to mirror.
    The node "shouler_l_trs" mirror its position to "shouler_r_trs"

    :param str list trs: transforms to mirror:
    :param str axis: axis to mirror across. ['x', 'y', 'z']:
    :param str leftToken: token for the left side
    :param str rightToken: token for the right side
    :param str mode: mirror mode. 'rotate' mirrors the rotation behaviour
                    where 'translate' mirrors translation behavior as well.
                    'translate' more is used more often in the face, 'rotate' in the body.

    """
    if trs is None:
        trs = cmds.ls(sl=True)

    trs = common.toList(trs)
    # Validate cmds which to mirror axis,
    if axis.lower() not in ('x', 'y', 'z'):
        raise ValueError("Keyword Argument: 'axis' not of accepted value ('x', 'y', 'z').")

    for transform in trs:
        if not cmds.nodeType(transform) in ['transform', '']:
            cmds.warning("{} is not a transform and connot be mirrored".format(transform))
            return

        # Get the worldspace matrix, as a list of 16 float values
        destination = common.getMirrorName(transform, left=leftToken, right=rightToken)
        mtx = cmds.xform(transform, q=True, ws=True, m=True)

        # Invert rotation columns,
        rx = [n * -1 for n in mtx[0:9:4]]
        ry = [n * -1 for n in mtx[1:10:4]]
        rz = [n * -1 for n in mtx[2:11:4]]

        # Invert translation row,
        t = [n * -1 for n in mtx[12:15]]

        # Set matrix based on given cmds, and whether to include behaviour or not.
        if axis.lower() == 'z':
            mtx[14] = t[2]  # set inverse of the Z translation

            # Set inverse of all rotation columns but for the one we've set translate to.
            if mode == 'rotate':
                mtx[0:9:4] = rx
                mtx[1:10:4] = ry

        elif axis.lower() == 'x':
            mtx[12] = t[0]  # set inverse of the X translation

            if mode == 'rotate':
                mtx[1:10:4] = ry
                mtx[2:11:4] = rz
        else:
            mtx[13] = t[1]  # set inverse of the Y translation

            if mode == 'rotate':
                mtx[0:9:4] = rx
                mtx[2:11:4] = rz

        # Finally set matrix for transform,
        cmds.xform(destination, ws=True, m=mtx)


def getAimAxis(transform, allowNegative=True, asVector=False):
    """
    Get the aim axis of a given transform.
    The axis closest to the offset between the child (aim at) and transform will be returned.
    The aim axis is calucated in the local space of the transform.

    :param str transform: transform node to get the axis of
    :param bool allowNegative: if true allow negative axis returns.
    :param bool asVector: if true return the aim axis as a vector
    :return: aim axis
    :rtype: str
    """
    child = cmds.listRelatives(transform, type='transform')
    if not child:
        raise RuntimeError('{} does not have a child to aim at'.format(transform))

    axis = getClosestAxis(transform, child[0], allowNegative=allowNegative)

    if asVector:
        return getVectorFromAxis(axis)
    return axis


def getClosestAxis(transform, target, allowNegative=True):
    """
    Get the closest axis betwen the transform and target node.

    This is caulculated by extracting the local offset matrix and
    comparing the lenghts of the directions.

    The longest direction can be assumed as the aim direction,
    considering most often a single translate is the aim axis)

    :param transform: transform to get the axis from
    :param target: target to get the axis from
    :param allowNegative: if true allow negative axis returns.
    :return: closest axis
    :rtype: str
    """
    offset = offsetMatrix(transform, target)

    tx, ty, tz = matrix.getTranslation(offset)

    axis = None
    if (abs(tx) > abs(ty)) and (abs(tx) > abs(tz)):
        if (tx > ty) and (tx > tz): axis = 'x'  # x
        if (tx < ty) and (tx < tz): axis = '-x'  # -x
    # Y
    elif (abs(ty) > abs(tx)) and (abs(ty) > abs(tz)):
        if (ty > tx) and (ty > tz): axis = 'y'  # y
        if (ty < tx) and (ty < tz): axis = '-y'  # -y
    # Z
    else:
        if (tz > tx) and (tz > ty): axis = 'z'  # z
        if (tz < tx) and (tz < ty): axis = '-z'  # -z

    # if axis is still None then we failed to find one. This probably occured because the
    # transform and target are at the same location.
    if not axis:
        raise RuntimeError(
            "Failed to calucate an axis between {} and {}. They may have the same transform".format(transform, target))

    # return the axis. If allow negetive is off, then just get the axis.
    if not allowNegative: return axis[-1]

    return axis


# TODO: rewrite to account for offset parent matrix
def decomposeRotation(node, twistAxis='x'):
    """
    decompose the swing and twist of a transform.
    :param str node: tranform to get the swing and twist from
    :param str twistAxis: local axis of the transform.
    :return: Decompose the rotation into separate XYZ rotations
    """
    node = common.getFirstIndex(node)

    # add the attributes
    for attr in ['decomposeX', 'decomposeY', 'decomposeZ']:
        if not cmds.objExists("{}.{}".format(node, attr)):
            cmds.addAttr(node, ln=attr, k=False)
            cmds.setAttr("{}.{}".format(node, attr), cb=True)

    mult = cmds.createNode('multMatrix', name="{}_local_{}".format(node, common.MULTMATRIX))
    parentInverse = "{}.parentInverseMatrix[0]".format(node)
    worldMatrix = "{}.worldMatrix[0]".format(node)
    cmds.connectAttr(worldMatrix, "{}.matrixIn[0]".format(mult))
    cmds.connectAttr(parentInverse, "{}.matrixIn[1]".format(mult))

    parentInverseMatrix = om2.MMatrix(cmds.getAttr(parentInverse))
    worldMatrix = om2.MMatrix(cmds.getAttr(worldMatrix))
    invLocalRest = (worldMatrix * parentInverseMatrix).inverse()
    cmds.setAttr("{}.matrixIn[2]".format(mult), list(invLocalRest), type='matrix')

    # get the twist
    rotation = cmds.createNode("decomposeMatrix", name='{}_rotation_{}'.format(node, common.DECOMPOSEMATRIX))
    cmds.connectAttr("{}.matrixSum".format(mult),
                     "{}.inputMatrix".format(rotation))

    twist = cmds.createNode('quatNormalize', name='{}_twist_{}'.format(node, 'quatNormalize'))
    cmds.connectAttr("{}.outputQuatW".format(rotation), "{}.inputQuatW".format(twist))

    cmds.connectAttr("{}.outputQuat{}".format(rotation, twistAxis.upper()),
                     "{}.inputQuat{}".format(twist, twistAxis.upper()))

    # swing = twist.inverse() * rotation
    invTwist = cmds.createNode("quatInvert", name='{}_invertTwist_quatInvert'.format(node))
    cmds.connectAttr("{}.outputQuat".format(twist),
                     "{}.inputQuat".format(invTwist))
    swing = cmds.createNode("quatProd", name="{}_swing_quatProd".format(node))
    cmds.connectAttr("{}.outputQuat".format(invTwist), "{}.input1Quat".format(swing))
    cmds.connectAttr("{}.outputQuat".format(rotation), "{}.input2Quat".format(swing))

    # invSwing = cmds.createNode("quatInvert", name="{}_invertSwing_quatInvert".format(node))
    # cmds.connectAttr("{}.outputQuat".format(swing), "{}.inputQuat".format(invSwing))

    # add the swing and twist to a new matrix
    rotationProd = cmds.createNode('quatProd', name="{}_rotationProd_quatProd".format(node))
    cmds.connectAttr("{}.outputQuat".format(twist), "{}.input1Quat".format(rotationProd))
    cmds.connectAttr("{}.outputQuat".format(swing), "{}.input2Quat".format(rotationProd))

    # calulate the twist.
    # This is different than the overall rotation the input quat of the anim axis and W.
    # convert the rotationProd into a Euler angle
    twistEuler = cmds.createNode("quatToEuler", name="{}_twistEuler_quatToEuler".format(node))
    cmds.setAttr("{}.inputRotateOrder".format(twistEuler), cmds.getAttr("{}.rotateOrder".format(node)))
    cmds.connectAttr("{}.outputQuatW".format(rotationProd), "{}.inputQuatW".format(twistEuler))
    cmds.connectAttr("{}.outputQuat{}".format(rotationProd, twistAxis.upper()),
                     "{}.inputQuatX".format(twistEuler, twistAxis.upper()))

    rotationMatrix = cmds.createNode('composeMatrix', name='{}_rotationMatrix_compMatrix'.format(node))
    cmds.setAttr("{}.useEulerRotation".format(rotationMatrix), 0)
    cmds.connectAttr("{}.outputQuat".format(rotationProd), "{}.inputQuat".format(rotationMatrix))

    output = cmds.createNode("decomposeMatrix", name='{}_output_{}'.format(node, common.DECOMPOSEMATRIX))
    cmds.connectAttr("{}.outputMatrix".format(rotationMatrix), "{}.inputMatrix".format(output))

    # connect the output to the start
    for axis in 'XYZ':
        if axis == twistAxis.upper():
            cmds.connectAttr("{}.outputRotateX".format(twistEuler, axis), "{}.decompose{}".format(node, axis), f=True)
        else:
            cmds.connectAttr("{}.outputRotate{}".format(output, axis), "{}.decompose{}".format(node, axis), f=True)
        cmds.setAttr("{}.decompose{}".format(node, axis), lock=True)

    # return the three attributes
    return ["{}.decompose{}".format(node, axis) for axis in 'XYZ']


def aimChain(chain, aimVector, upVector, worldUpObject=None, worldUpType='object', worldUpVector=(0, 1, 0)):
    """
    aim a series of transforms at its child.
    if its the child then reverse the aimVector and aim at the parent

    :param list chain: list of transforms to aim
    :param list tuple aimVector: aim vector to use.
    :param list tuple upVector: up vector to use.
    :param str worldUpObject: world up object to use in the aim constraint
    :param str worldUpType: world up type to use in the aim constraint
    :param list tuple worldUpVector: world up vector to use in the aim constraint
    """

    if not isinstance(chain, (list, tuple)):
        raise Exception("{} Is not a list, nothing to aim".format(chain))

    aimVector = aimVector
    for i in range(len(chain)):
        if i == len(chain) - 1:
            aimVector = mathUtils.scalarMult(aimVector, -1)
            aimTarget = chain[i - 1]
        else:
            aimTarget = chain[i + 1]

        const = cmds.aimConstraint(aimTarget, chain[i],
                                   aimVector=aimVector,
                                   upVector=upVector,
                                   worldUpType=worldUpType,
                                   worldUpObject=worldUpObject,
                                   worldUpVector=worldUpVector,
                                   mo=False)
        cmds.delete(const)


def resetTransformations(nodes):
    """
    Reset the channel box transformations of a given node.

    :param nodes: list of nodes to reset the transformations
    """
    nodes = common.toList(nodes)
    for node in nodes:
        for attr in ["jo", 'ra']:
            if cmds.objExists("{}.{}".format(node, attr)):
                cmds.setAttr("{}.{}".format(node, attr), 0, 0, 0)
        for attr in ["{}{}".format(x, y) for x in 'trs' for y in 'xyz']:
            isLocked = cmds.getAttr("{}.{}".format(node, attr), lock=True)
            connection = cmds.listConnections("{}.{}".format(node, attr), s=True, d=False, plugs=True) or []
            isConnected = len(connection)
            if isLocked:
                cmds.setAttr("{}.{}".format(node, attr), lock=False)
            if isConnected:
                cmds.disconnectAttr(connection[0], "{}.{}".format(node, attr))

            value = 1.0 if attr.startswith('s') else 0.0
            cmds.setAttr("{}.{}".format(node, attr), value)
            if isConnected: cmds.connectAttr(connection[0], "{}.{}".format(node, attr), f=True)
            if isLocked:  cmds.setAttr("{}.{}".format(node, attr), lock=True)


def getVectorFromAxis(axis):
    """
    Return a vector based on the given axis string

    :param axis: Axis name. Valid values are ['x', 'y', 'z', '-x', '-y', '-z']
    :return list tuple: Axis
    """
    if axis.lower() == 'x':
        vector = [1, 0, 0]
    elif axis.lower() == 'y':
        vector = [0, 1, 0]
    elif axis.lower() == 'z':
        vector = [0, 0, 1]
    elif axis.lower() == '-x':
        vector = [-1, 0, 0]
    elif axis.lower() == '-y':
        vector = [0, -1, 0]
    elif axis.lower() == '-z':
        vector = [0, 0, -1]
    else:
        raise ValueError("Keyword Argument: 'axis' not of accepted value ('x', 'y', 'z', '-x', '-y', '-z').")
    return vector


def getRotateOrder(order):
    """
    Get the proper rotate order index.
    This is used to convert the index of a rotate order attribute to its respective string value.

    for example: getRotateOrder(0) returns "xyz"

    :param order: rotate order
    :type order: str
    :return:
    """
    return ROTATEORDER.index(order)
