"""
Utilities for transforms
"""
import math
import maya.cmds as cmds
import maya.api.OpenMaya as om2

import rigamajig2.maya.hierarchy as dag
import rigamajig2.shared.common as common
import rigamajig2.maya.matrix as matrix


def matchTransform(source, target):
    """
    Match the translation and Rotation of the source to the target object
    :param source: source transfrom
    :param target: transform to snap
    :return:
    """
    matchTranslate(source, target)
    matchRotate(source, target)


def matchTranslate(source, target):
    """
    Match the translation of one object to another.
    :param source: Source transfrom
    :type source: str
    :param target:  Target transform to match
    :type target: str
    """
    pos = getAveragePoint(source)
    cmds.xform(target, ws=True, t=pos)


def matchRotate(source, target):
    """
    Match the rotation of one object to another rotation.
    This matching method is awesome. It works across regardless of mismatched rotation orders or transforms who's
    parents have different rotation orders.
    :param source: Source transfrom
    :type source: str
    :param target:  Target transform to match
    :type target: str
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


def getDagPath(name):
    """
    Get the DAG path of a node (For maya api 2 )
    :param name: name of the node to get the dag path from
    """
    sel = om2.MGlobal.getSelectionListByName(name)
    return sel.getDagPath(0)


def freezeToParentOffset(nodes):
    """
    Freeze the given transform nodes by adding their values to the offsetParentMatrix
    :param nodes: transform nodes to freeze
    """
    nodes = common.toList(nodes)

    if cmds.about(api=True) < 20200000:
        raise RuntimeError("OffsetParentMatrix is only available in Maya 2020 and beyond")
    for node in nodes:
        offset = localOffset(node)
        cmds.setAttr("{}.{}".format(node, 'offsetParentMatrix'), list(offset), type="matrix")
        for attr in ["jo", 'ra']:
            if cmds.objExists("{}.{}".format(node, attr)):
                cmds.setAttr("{}.{}".format(node, attr), 0, 0, 0)
        for attr in ["{}{}".format(x, y) for x in 'trs' for y in 'xyz']:
            is_locked = cmds.getAttr("{}.{}".format(node, attr), lock=True)
            if is_locked:
                cmds.setAttr("{}.{}".format(node, attr), lock=False)
            value = 1.0 if attr.startswith('s') else 0.0
            cmds.setAttr("{}.{}".format(node, attr), value)
            if is_locked:  cmds.setAttr("{}.{}".format(node, attr), lock=True)


def localOffset(node):
    """
    Get the local offset matrix of a node relative to its parent
    :param node: node name
    :return: MMatrix
    """
    offset = om2.MMatrix(cmds.getAttr('{}.{}'.format(node, 'worldMatrix')))
    parent = cmds.listRelatives(node, parent=True, path=True) or None
    if parent:
        parentInverse = om2.MMatrix(cmds.getAttr('{}.{}'.format(parent[0], 'worldInverseMatrix')))
        offset *= parentInverse
    return offset


def getAveragePoint(transforms):
    """
    get the average point between a list of transforms.
    :param transforms: list of transforms to average
    :return:
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


def mirror(trs, axis='x', mode='rotate'):
    """
    Mirrors transform axis vector. Searches for a destination node to mirror.
    The node "shouler_l_trs" mirror its position to "shouler_r_trs"


    :param trs: transforms to mirror:
    :type trs: str | list

    :param axis: axis to mirror across. ['XY', 'YZ', 'XZ']:
    :type axis: str

    :param mode: mirror mode. 'rotate' mirrors the rotation behaviour where 'translate' mirrors translation behavior as well.
                'translate' more is used more often in the face, 'rotate' in the body.
    :type mode: str

    """
    trs = common.toList(trs)
    # Validate cmds which to mirror axis,
    if axis.lower() not in ('x', 'y', 'z'):
        raise ValueError("Keyword Argument: 'axis' not of accepted value ('x', 'y', 'z').")

    for transform in trs:
        if not cmds.nodeType(transform) in ['transform']:
            cmds.warning("{} is not a transform and connot be mirrored".format(transform))
            return

        # Get the worldspace matrix, as a list of 16 float values
        destination = common.getMirrorName(transform)
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


def getAimAxis(transform, allowNegative=True):
    """
    Get the aim axis of a given transform.
    The axis closest to the offset between the child (aim at) and transform will be returned.
    The aim axis is calucated in the local space of the transform.

    :param transform: transform node to get the axis of
    :param allowNegative: allow negative axis
    :return: axis with the closest
    """
    child = cmds.listRelatives(transform, type='transform')
    if not child:
        raise RuntimeError('{} does not have a child to aim at'.format(transform))

    childLocalMatrix = localOffset(child[0])
    tx, ty, tz = matrix.getTranslation(childLocalMatrix)

    # Check which value is the largest.
    # Then get the proper direction
    # X
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

    # return the axis. If allow negetive is off, then just get the axis.
    if not allowNegative: return axis[-1]
    return axis


def decomposeRotation(node, twistAxis='x'):
    """
    decompose the swing and twist of a transform.
    :param node: tranform to get the swing and twist from
    :param twistAxis: local axis of the transform.
    :return:
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

    pinv = om2.MMatrix(cmds.getAttr(parentInverse))
    m = om2.MMatrix(cmds.getAttr(worldMatrix))
    invLocalRest = (m * pinv).inverse()
    cmds.setAttr("{}.matrixIn[2]".format(mult), list(invLocalRest), type='matrix')

    # get the twist
    rotation = cmds.createNode("decomposeMatrix", name='{}_rotation_{}'.format(node, common.DECOMPOSEMATRIX))
    cmds.connectAttr("{}.matrixSum".format(mult),
                     "{}.inputMatrix".format(rotation))

    twist = cmds.createNode('quatNormalize', name='{}_twist_{}'.format(node, 'quatNormalize'))
    cmds.connectAttr("{}.outputQuatW".format(rotation),
                     "{}.inputQuatW".format(twist))

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
