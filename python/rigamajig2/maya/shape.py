"""
Functions for shapes in maya
"""
import maya.cmds as cmds

import rigamajig2.shared.common as common

MESH = "mesh"
CURVE = "nurbsCurve"
SURFACE = "nurbsSurface"
MIXED = "mixed"


def getType(node):
    """
    Get the type from a transform. If the node is a tranform it gets the type based on the shape nodes.

    :param node: object to get the type for
    :return: node type of the given node
    :rtype: str
    """

    nodeType = cmds.nodeType(node)
    if nodeType == "transform":
        shapes = common.toList(getShapes(node))
        shapeTypes = list()
        for shape in shapes:
            shapeTypes.append(cmds.nodeType(shape))
        if len(shapeTypes) > 1:
            nodeType = "mixed"
        else:
            nodeType = list(shapeTypes)[0]

    return str(nodeType)


def getShapes(node):
    """
    Get the shapes of an object. If the node is a tranform it gets the shape node.

    :param node: object to get shapes from
    :return: list of shape nodes for a given node
    :rtype: str
    """
    shapeTypes = ["mesh", "nurbsSurface", "nurbsCurve", "subdiv"]
    nodeType = cmds.nodeType(node)
    if nodeType in shapeTypes:
        return node

    if nodeType == "transform":
        shape = cmds.listRelatives(node, s=1, ni=1)
        if shape:
            return shape[0]
    return None


def getPointCount(shape):
    """
    Get the point count of a nurbsCurve or mesh

    :param shape: name of the shape node
    :return: number of points within the shape node
    """
    if cmds.nodeType(shape) == "transform":
        shape = cmds.listRelatives(shape, s=True, ni=True)[0]

    shapeType = cmds.nodeType(shape)
    if shapeType == "mesh":
        pointCount = cmds.polyEvaluate(shape, v=True)
    if shapeType == "nurbsCurve":
        degs = cmds.getAttr("{}.degree".format(shape))
        spans = cmds.getAttr("{}.spans".format(shape))

        pointCount = degs + spans
    return pointCount
