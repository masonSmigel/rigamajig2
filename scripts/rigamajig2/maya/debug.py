"""
This module is used for debugging a rigamajig2 builder
"""

import os.path

import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.transform as rig_transform


def showLocalRotationAxis(nodes):
    """
    Show the local rotation axis for the given nodes
    :param list nodes: list of nodes to display local rotation axis
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
    :param list nodes: nodes to hide
    """
    if not common.DEBUG:
        cmds.hide(nodes)


def createProxyGeo(joints):
    """
    Joints to use to create proxy geometry for
    :param list joints: list of joints to add prxy geometry on.
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

    This can be helpful over LRA's since the geometry will show scale as well as orientation

    :param list nodes: nodes to add markers to
    """
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    # if we dont have any nodes. use the selection
    if not nodes:
        nodes = cmds.ls(sl=True)

    asset = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../misc/axis_marker.ma"))

    if not cmds.objExists("axisMarker_hrc"):
        cmds.createNode("transform", name="axisMarker_hrc")

    for node in nodes:
        if not cmds.objExists(node):
            continue
        marker = '{}_marker'.format(node)
        if cmds.objExists(marker):
            raise RuntimeError("A marker already exists with the name '{}'".format(marker))

        markerNode = cmds.ls(cmds.file(asset, i=True, returnNewNodes=True, ns='marker'), type='transform')
        cmds.rename(markerNode,marker)
        cmds.parent(marker, "axisMarker_hrc")

        rig_transform.matchTransform(node, marker)
        rig_transform.connectOffsetParentMatrix(node, marker)
