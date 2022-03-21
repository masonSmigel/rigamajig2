"""
This module contains functions for maintaining interactablility
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2
import rigamajig2.shared.common as common
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.node as node
import rigamajig2.maya.transform as transform
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.meta as meta
import rigamajig2.maya.utils as utils

MIRROR_GRP_NAME = 'liveMirror_hrc'
PIN_HRC_NAME = 'rigamajig_pin_hrc'


def createlivePoleVector(matchList, poleVectorNode=None):
    """
    Get the live pole vector position. This does the same thing as ikfk.IkFkLimb.getPoleVectorPos,
    but its a live connection with nodes. If you only need a static pole vector pos use the other function.
    This is primarily for display purposes.
    :param matchList: list of transforms to get pole vector position from
    :param poleVectorNode: Optional- name of the pole vector object. If None we'll make one!
    :return:
    """
    if len(matchList) != 3:
        raise RuntimeError("Match list must have a length of 3")

    # if we dont have a poleVectorNode then make one.
    if not poleVectorNode:
        poleVectorNode = cmds.spaceLocator(name=matchList[1] + '_pvPos_' + common.TARGET)[0]
        cmds.setAttr("{}.overrideEnabled".format(poleVectorNode), 1)
        cmds.setAttr("{}.overrideColor".format(poleVectorNode), 28)
    if not cmds.objExists(poleVectorNode):
        raise RuntimeError("The poleVector node '{}' does not exist in the scene".format(poleVectorNode))

    # set some attributes on the poleVector Node
    cmds.setAttr("{}.inheritsTransform".format(poleVectorNode), False)
    for attr in ["{}{}".format(x, y) for x in 'trs' for y in 'xyz']:
        if attr.startswith('t'):
            cmds.setAttr('{}.{}'.format(poleVectorNode, attr), lock=True)
        else:
            cmds.setAttr('{}.{}'.format(poleVectorNode, attr), lock=True, k=False, cb=False)

    # check if the attribute "magnitude" exists. if not add it
    if not cmds.objExists("{}.{}".format(poleVectorNode, 'pvMag')):
        cmds.addAttr(poleVectorNode, ln='pvMag', at='float', dv=0, k=True)

    # get the world space factors of the three points
    start = node.decomposeMatrix("{}.worldMatrix".format(matchList[0]), name=matchList[0])
    mid = node.decomposeMatrix("{}.worldMatrix".format(matchList[1]), name=matchList[1])
    end = node.decomposeMatrix("{}.worldMatrix".format(matchList[2]), name=matchList[2])

    # get the line and point vectors
    line = node.plusMinusAverage3D(["{}.outputTranslate".format(end),
                                    "{}.outputTranslate".format(start)],
                                   operation='sub',
                                   name=matchList[1] + "_line")
    point = node.plusMinusAverage3D(["{}.outputTranslate".format(mid),
                                     "{}.outputTranslate".format(start)],
                                    operation='sub',
                                    name=matchList[1] + "_point")

    pointLine = node.vectorProduct("{}.output3D".format(line),
                                   "{}.output3D".format(point),
                                   operation='dot',
                                   name=matchList[1] + 'pointXLine')
    lineLine = node.vectorProduct("{}.output3D".format(line),
                                  "{}.output3D".format(line),
                                  operation='dot',
                                  name=matchList[1] + 'lineXLine')

    scaleValue = node.multiplyDivide("{}.output".format(pointLine),
                                     "{}.output".format(lineLine),
                                     operation='div',
                                     name=matchList[1] + 'scaleValue')
    projVec = node.multiplyDivide('{}.output3D'.format(line),
                                  "{}.output".format(scaleValue),
                                  name=matchList[1] + "_proj")
    projVecStart = node.plusMinusAverage3D(['{}.output'.format(projVec),
                                            '{}.outputTranslate'.format(start)],
                                           name=matchList[1] + "_projVec")

    offsetVec = node.plusMinusAverage3D(["{}.outputTranslate".format(mid),
                                         "{}.output3D".format(projVecStart)],
                                        operation='sub',
                                        name=matchList[1] + '_offset')
    offsetVecNormal = node.vectorProduct("{}.output3D".format(offsetVec),
                                         normalize=True,
                                         operation='none',
                                         name=matchList[1] + '_norm')

    # get the length between the two start and end (AKA the magnitude of the vector)
    midDist = cmds.createNode('distanceBetween', name=matchList[1] + '_mag_' + common.DISTANCEBETWEEN)
    cmds.connectAttr('{}.outputTranslate'.format(start), "{}.point1".format(midDist))
    cmds.connectAttr('{}.outputTranslate'.format(mid), "{}.point2".format(midDist))

    endDist = cmds.createNode('distanceBetween', name=matchList[2] + '_mag_' + common.DISTANCEBETWEEN)
    cmds.connectAttr('{}.outputTranslate'.format(mid), "{}.point1".format(endDist))
    cmds.connectAttr('{}.outputTranslate'.format(end), "{}.point2".format(endDist))

    fullDist = node.addDoubleLinear("{}.distance".format(midDist), "{}.distance".format(endDist),
                                    name=matchList[1] + 'addDist')

    outMag = node.addDoubleLinear("{}.output".format(fullDist),
                                  "{}.pvMag".format(poleVectorNode),
                                  name=matchList[1] + '_pvMag')

    magVec = node.multiplyDivide("{}.output".format(offsetVecNormal),
                                 ["{}.output".format(outMag) for _ in range(3)],
                                 name=matchList[0] + '_mag')
    pvPos = node.plusMinusAverage3D(["{}.output".format(magVec),
                                     "{}.outputTranslate".format(mid)],
                                    name=matchList[1] + '_pvPos')

    # connect our pvPos to the poleVectorNode
    cmds.connectAttr("{}.output3D".format(pvPos), "{}.t".format(poleVectorNode), f=True)

    meta.tag(poleVectorNode, 'guide')
    return poleVectorNode


def createLiveMirror(jointList, axis='x', mode='rotate'):
    """
    Create a live mirror between a joint and its mirror
    :param jointList: list of joints to mirror
    :param axis: axis to mirror across. ['x', 'y', 'z']
    :param mode: mirror mode. 'rotate' mirrors the rotation behaviour where 'translate' mirrors translation behavior as well.
                'translate' more is used more often in the face, 'rotate' in the body.
    :return: list of mirrored joints
    """
    jointList = common.toList(jointList)
    suf = '_lm'
    # Validate cmds which to mirror axis,
    if axis.lower() not in ('x', 'y', 'z'):
        raise ValueError("Keyword Argument: 'axis' not of accepted value ('x', 'y', 'z').")

    for jnt in jointList:
        if not cmds.objExists(jnt):
            raise RuntimeError("the Joint {} does not exist in the scene".format(jnt))

        mirrorJnt = common.getMirrorName(jnt)
        if not cmds.objExists(mirrorJnt):
            raise RuntimeError("Node not found: {}".format(mirrorJnt))

        # Create the mirror setup and nodes
        mirrorTgt = cmds.createNode('transform', n=mirrorJnt + suf + '_' + common.TARGET)
        cmds.delete(cmds.parentConstraint(mirrorJnt, mirrorTgt, mo=False))

        if not cmds.objExists(MIRROR_GRP_NAME):
            cmds.createNode('transform', n=MIRROR_GRP_NAME)
        cmds.parent(mirrorTgt, MIRROR_GRP_NAME)

        # create the node network to mirror the position
        dcmp = node.decomposeMatrix("{}.worldMatrix".format(jnt), name=jnt + suf)
        inversePos = node.multiplyDivide("{}.outputTranslate".format(dcmp),
                                         [-1, -1, -1],
                                         name=jnt + '_invertPos' + suf)
        # Issolate the x, y and z vectors.
        x_vec = node.vectorProduct("{}.outputTranslate".format(dcmp),
                                   [1, 0, 0], operation='dot',
                                   name=jnt + 'XVec' + suf)
        y_vec = node.vectorProduct("{}.outputTranslate".format(dcmp),
                                   [0, 1, 0],
                                   operation='dot',
                                   name=jnt + 'YVec' + suf)
        z_vec = node.vectorProduct("{}.outputTranslate".format(dcmp),
                                   [0, 0, 1],
                                   operation='dot',
                                   name=jnt + 'ZVec' + suf)
        # scale the vectors by 2
        scaled = node.multiplyDivide(
            ["{}.outputX".format(x_vec), "{}.outputX".format(y_vec), "{}.outputX".format(z_vec)],
            [2, 2, 2],
            name=jnt + 'dotScaled')
        # invert the isolated vectors
        invTotal = node.plusMinusAverage3D(["{}.output".format(inversePos),
                                            "{}.output".format(scaled)],
                                           name=jnt + '_total' + suf)

        # create the network for the mirror rotation
        quatInvert = cmds.createNode("quatInvert", n=jnt + '_quatInvert' + suf)
        cmds.connectAttr("{}.outputQuat".format(dcmp), "{}.inputQuat".format(quatInvert))

        if axis == 'x':
            posList = ["{}.outputX".format(inversePos), '{}.output3Dy'.format(invTotal),
                       '{}.output3Dz'.format(invTotal)]
            quatList = ["{}.outputQuatX".format(dcmp), "{}.outputQuatY".format(quatInvert),
                        "{}.outputQuatZ".format(quatInvert), "{}.outputQuatW".format(quatInvert)]
        if axis == 'y':
            posList = ['{}.output3Dx'.format(invTotal), "{}.outputY".format(inversePos),
                       '{}.output3Dz'.format(invTotal)]
            quatList = ["{}.outputQuatX".format(quatInvert), "{}.outputQuatY".format(dcmp),
                        "{}.outputQuatZ".format(quatInvert), "{}.outputQuatW".format(quatInvert)]
        if axis == 'z':
            posList = ['{}.output3Dx'.format(invTotal), "{}.output3Dy".format(invTotal),
                       '{}.outputZ'.format(inversePos)]
            quatList = ["{}.outputQuatX".format(quatInvert), "{}.outputQuatY".format(quatInvert),
                        "{}.outputQuatZ".format(dcmp), "{}.outputQuatW".format(quatInvert)]

        # Compose the mirrored position into a matrix to get a proper offset
        rotOrder = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx'][cmds.getAttr("{}.rotateOrder".format(mirrorJnt))]

        compMatrix = node.composeMatrix(inputTranslate=posList, inputQuat=quatList,
                                        eulerRotation=False, rotateOrder=rotOrder, name=jnt + '_mirrorMatrix' + suf)

        # Calculate the offset
        winv = om2.MMatrix(cmds.getAttr('{}.{}'.format(jnt, 'worldInverseMatrix')))
        m = om2.MMatrix(cmds.getAttr('{}.{}'.format(mirrorTgt, 'worldMatrix')))
        off = (m * winv)

        node.multMatrix(["{}.outputMatrix".format(compMatrix),
                         "{}.parentInverseMatrix".format(mirrorTgt)],
                        outputs=mirrorTgt, t=True, r=False,
                        name=mirrorTgt + '_mirrorPos' + suf)
        node.multMatrix([list(off), "{}.outputMatrix".format(compMatrix), "{}.parentInverseMatrix".format(mirrorTgt)],
                        outputs=mirrorTgt, t=False, r=True,
                        name=mirrorTgt + '_mirrorRot' + suf)

        # connect our mirror target with a parent constraint
        cmds.pointConstraint(mirrorTgt, mirrorJnt, n=mirrorJnt + common.POINTCONSTRAINT, mo=False)
        cmds.orientConstraint(mirrorTgt, mirrorJnt, n=mirrorJnt + common.ORIENTCONSTRAINT, mo=True)


@utils.oneUndo
@utils.preserveSelection
def pin(nodes=None):
    """
    Takes the given nodes and 'pins' them. This means they will maintain their position and orientation
    regardless of what the parent does.
    :param nodes:
    :return:
    """
    if not nodes:
        nodes = cmds.ls(sl=True)
    nodes = common.toList(nodes)

    # create a pin transform
    pin_hrc = PIN_HRC_NAME
    if not cmds.objExists(pin_hrc):
        pin_hrc = cmds.createNode("transform", name=pin_hrc)
    rig_attr.lockAndHide(pin_hrc, rig_attr.TRANSFORMS + ['v'])

    for node in nodes:
        if cmds.objExists("{}.__isPinned__".format(node)):
            continue

        cmds.addAttr(node, longName="__isPinned__", at="bool")

        pin_trs = cmds.spaceLocator(name=node + "_pin")[0]
        transform.matchTransform(node, pin_trs)
        cmds.parent(pin_trs, pin_hrc)
        rig_attr.lockAndHide(pin_trs, rig_attr.TRANSFORMS + ['v'])
        cmds.parentConstraint(pin_trs, node, mo=True)
        rig_attr.lock(node, rig_attr.TRANSFORMS)

        # store the color information before the pin.
        data = dict()
        data['prePin_overrideEnabled'] = cmds.getAttr("{}.overrideEnabled".format(node))
        data['prePin_overrideRGBColors'] = cmds.getAttr("{}.overrideRGBColors".format(node))
        if data['prePin_overrideRGBColors']:
            data['prePin_overrideColorRGB'] = cmds.getAttr("{}.overrideColorRGB".format(node))[0]
        else:
            data['prePin_overrideColor'] = cmds.getAttr("{}.overrideColor".format(node))

        meta_node = meta.MetaNode(pin_trs)
        meta_node.setDataDict(data, hide=True, lock=True)

        # set a new color
        for n in [node, pin_trs]:
            cmds.setAttr("{}.overrideEnabled".format(n), 1)
            cmds.setAttr("{}.overrideRGBColors".format(n), 0)
            cmds.setAttr("{}.overrideColor".format(n), 3)


@utils.oneUndo
def unpin(nodes=None):
    """
    unpin selected nodes
    :param nodes:
    :return:
    """
    if not nodes:
        nodes = cmds.ls(sl=True)
    nodes = common.toList(nodes)

    for node in nodes:
        if not cmds.objExists("{}.__isPinned__".format(node)):
            continue

        parent_const = cmds.ls(cmds.listConnections("{}.tx".format(node)), type='parentConstraint')[0] or None
        if parent_const:
            pin_trs = cmds.ls(cmds.listConnections("{}.target[0].targetParentMatrix".format(parent_const)),
                              type='transform')[0] or None

        # delete the parent constraint
        rig_attr.unlock(node, rig_attr.TRANSFORMS)
        cmds.delete(parent_const)

        # retreive color information and set it back
        meta_node = meta.MetaNode(pin_trs)
        color_data = meta_node.getAllData()

        for key in list(color_data.keys()):
            attribute = key.split("_")[-1]
            if isinstance(color_data[key], (list, tuple)):
                cmds.setAttr("{0}.{1}".format(node, attribute), *color_data[key])
            else:
                cmds.setAttr("{0}.{1}".format(node, attribute), color_data[key])

        # Remove the pinned tag so this node can be re-pined in the future.
        cmds.deleteAttr("{}.__isPinned__".format(node))
        cmds.delete(pin_trs)

    # check if the pin hrc is empty. If it is we can delete it.
    if len(cmds.listRelatives(PIN_HRC_NAME, c=True) or list()) == 0:
        cmds.delete(PIN_HRC_NAME)
