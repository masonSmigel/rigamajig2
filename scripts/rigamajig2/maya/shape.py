"""
Functions for shapes in maya
"""
import maya.cmds as cmds
import maya.OpenMaya as om

import rigamajig2.maya.omUtils
import rigamajig2.shared.common as common


def getType(node):
    """
    Get the type from a transform. If the node is a tranform it gets the type based on the shape nodes.
    :param node: object to get the type for
    :return:
    """

    nodeType = cmds.nodeType(node)
    if nodeType == 'transform':
        shapes = common.toList(getShapes(node))
        shapeTypes = list()
        for shape in shapes:
            shapeTypes.append(cmds.nodeType(shape))
        if len(shapeTypes) > 1:
            nodeType = 'mixed'
        else:
            nodeType = list(shapeTypes)[0]

    return str(nodeType)


def getShapes(node):
    """
    Get the shapes of an object. If the node is a tranform it gets the shape node.
    :param node: object to get shapes from
    :return:
    """
    shape_types = ['mesh', 'nurbsSurface', 'nurbsCurve', 'subdiv']
    node_type = cmds.nodeType(node)
    if node_type in shape_types:
        return node

    if node_type == 'transform':
        shape = cmds.listRelatives(node, s=1, ni=1)
        if shape:
            return shape[0]


def getPointCount(shape):
    """
    Get the point count of a nurbsCurve or mesh
    :param shape:
    :return:
    """
    if cmds.nodeType(shape) == 'transform':
        shape = cmds.listRelatives(shape, s=True, ni=True)[0]

    shape_type = cmds.nodeType(shape)
    if shape_type == 'mesh':
        pointCount = cmds.polyEvaluate(shape, v=True)
    if shape_type == 'nurbsCurve':
        pointCount = int(cmds.ls("{}.cv[*]".format(shape_type))[0].split(":")[1][:-1])
        pointCount += 1
    return pointCount


if __name__ == '__main__':
    print getDeformShape('head_Cluster_geo')
