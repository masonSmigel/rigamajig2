import os.path

import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.meta as meta


def showLocalRotationAxis(nodes):
    """
    Show the local rotation axis for the given nodes
    :param nodes: list of nodes to display local rotation axis
    :return: None
    """
    if not common.DEBUG:
        return

    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.objExists(node):
            cmds.setAttr("{}.displayLocalAxis".format(node), 1)


def hide(nodes):
    """
    Hide nodes if we are not in debug mode
    :param nodes: nodes to hide
    :return:
    """
    if not common.DEBUG:
        cmds.hide(nodes)


def createProxyGeo(joints):
    """
    Joints to use to create proxy geometry for
    :param joints:
    :return:
    """
    import rigamajig2.maya.joint as joint

    for jnt in joints:
        if joint.isEndJoint(jnt):
            continue
        node, shape = cmds.polyCube(n=jnt + '_prxyGeo')
        decendents = cmds.ls(cmds.listRelatives(jnt, c=True) or [], type='joint')
        childJoint = decendents[0]
        rig_transform.matchTranslate([jnt, childJoint], node)
        rig_transform.matchRotate(jnt, node)

        axis = rig_transform.getAimAxis(jnt, allowNegative=False)
        cmds.setAttr("{}.s{}".format(node, axis), joint.length(jnt))
        cmds.setAttr("{}.s{}".format(node, axis), lock=True)

        for attr in ["{}{}".format(x, y) for x in 'tr' for y in 'xyz']:
            cmds.setAttr("{}.{}".format(node, attr), lock=True, k=False)
            cmds.setAttr("{}.{}".format(node, attr), cb=False)


def createAxisMarker(nodes=None):
    """
    Create an axis marker geometry on the given nodes.
    his can be helpful over LRA's since the geometry will show scale as well as orientation
    :param nodes: nodes to add markers to
    :return:
    """
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    # if we dont have any nodes. use the selection
    if not nodes:
        nodes = cmds.ls(sl=True)

    asset = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../misc/axis_marker.ma"))
    print asset

    if not cmds.objExists("axisMarker_hrc"):
        cmds.createNode("transform", name="axisMarker_hrc")

    for node in nodes:
        if not cmds.objExists(node):
            continue
        marker = '{}_marker'.format(node)
        if cmds.objExists(marker):
            raise RuntimeError("A marker already exists with the name '{}'".format(marker))

        marker_node = cmds.ls(cmds.file(asset, i=True, returnNewNodes=True, ns='marker'), type='transform')
        cmds.rename(marker_node,marker)
        cmds.parent(marker, "axisMarker_hrc")

        rig_transform.matchTransform(node, marker)
        rig_transform.connectOffsetParentMatrix(node, marker)


def generateRandomAnim(nodes=None, attributes=list(), keysIncriment=10):
    """
    Generate random animation channels for nodes.
    If no nodes are provided use all controls in the scne
    :param nodes: nodes to animate
    :param attributes: attributes to generate animation for
    :param keysIncriment: incriment for how often keyframes are generated
    :return:
    """
    import random

    if not nodes:
        nodes = meta.getTagged("control")

    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    if not attributes:
        attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 's']

    time_max = cmds.playbackOptions(q=True, maxTime=True)
    for i in range(int(time_max-1 / keysIncriment)):
        for control in nodes:
            current_time = keysIncriment * i
            if current_time > time_max:
                break

            for attr in attributes:
                value = float(random.uniform(0, 5))
                if 't' in attr: value = float(random.uniform(-25, 25))
                if 'r' in attr: value = float(random.uniform(-360, 360))
                if 's' in attr: value = float(random.uniform(0.01, 3))

                cmds.setKeyframe(control, attribute=attr, v=value, t=current_time)
    print("Generated Test animation for {} nodes with time range of {}.".format(len(nodes), time_max))
