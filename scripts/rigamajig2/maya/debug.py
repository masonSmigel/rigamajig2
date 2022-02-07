import os.path

import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.transform as rig_transform


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


def createAxisMarker(nodes):
    """
    Create an axis marker geometry on the given nodes.
    his can be helpful over LRA's since the geometry will show scale as well as orientation
    :param nodes: nodes to add markers to
    :return:
    """
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    asset = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../other/axis_marker.ma"))
    print asset

    if not cmds.objExists("axisMarkers_hrc"):
        cmds.createNode("transform", name="axisMarker_hrc")

    for node in nodes:
        marker_node = cmds.ls(cmds.file(asset, i=True, returnNewNodes=True, ns='marker'), type='transform')
        marker = '{}_marker'.format(node)
        cmds.rename(marker_node,marker)
        cmds.parent(marker, "axisMarker_hrc")

        rig_transform.matchTransform(node, marker)
        rig_transform.connectOffsetParentMatrix(node, marker)
