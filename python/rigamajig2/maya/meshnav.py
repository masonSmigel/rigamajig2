"""
This module contains functions to navigate mesh topology
"""

import operator

import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import maya.cmds as cmds

import rigamajig2.maya.mesh


def getClosestFace(mesh, point):
    """
    Return closest face on mesh to the point.

    :param str mesh: mesh name
    :param list point: world space coordinate
    :return: tuple of vertex id and distance to point
    :rtype: tuple
    """
    faceId = getClosestFacePoint(mesh, point)[-1]
    return mesh + ".f[{}]".format(faceId)


def getClosestFacePoint(mesh, point):
    """
    Return closest facePoint on mesh to the point.

    :param str mesh: mesh name
    :param list point: world space coordinate
    :return: tuple of vertex id and distance to point
    :rtype: tuple
    """
    mfnMesh = rigamajig2.maya.mesh.getMeshFn(mesh)

    pos = om2.MPoint(point[0], point[1], point[2])
    return mfnMesh.getClosestPoint(pos, om2.MSpace.kWorld)


def getClosestVertex(mesh, point, returnDistance=False):
    """
    Return closest vertex on mesh to the point.

    :param str mesh: mesh to get the closest vertex of
    :param list point: world space coordinate
    :param bool returnDistance: if true returns a tuple of vertex id and distance to vertex
    :return: name of the closest vertex.
            If return Distance is True it will also return the distance between the point and vertex.
    :rtype: str
    """
    if isinstance(point, str):
        point = cmds.xform(point, q=True, ws=True, t=True)
    pos = om2.MPoint(point[0], point[1], point[2])
    mfnMesh = rigamajig2.maya.mesh.getMeshFn(mesh)

    index = mfnMesh.getClosestPoint(pos, space=om2.MSpace.kWorld)[1]
    faceVtx = mfnMesh.getPolygonVertices(index)
    vtxDist = [
        (vtx, mfnMesh.getPoint(vtx, om2.MSpace.kWorld).distanceTo(pos))
        for vtx in faceVtx
    ]

    vertexId, dist = min(vtxDist, key=operator.itemgetter(1))
    if returnDistance:
        return mesh + ".vtx[{}]".format(vertexId), dist
    return mesh + ".vtx[{}]".format(vertexId)


def getClosestUV(mesh, point):
    """
    Return closest UV on mesh to the point.

    :param str mesh: mesh name
    :param list point: world space coordinate
    :return: Uv coordinates
    :rtype: tuple
    """

    mfnMesh = rigamajig2.maya.mesh.getMeshFn(mesh)

    pos = om2.MPoint(point[0], point[1], point[2])
    uvFace = mfnMesh.getUVAtPoint(pos)
    closestUv = (uvFace[0], uvFace[1])
    return closestUv


# bounding box Info
def getBboxCenter(obj):
    """
    Get the bounding box center of a mesh object

    :param obj: object name
    :return: the bounding box size
    :rtype: list
    """
    bbox = cmds.exactWorldBoundingBox(obj)
    bboxMin = bbox[:3]
    bboxMax = bbox[3:]
    center = [(bboxMin[x] + bboxMax[x]) / 2.0 for x in range(3)]
    return center


def getConnectedVertices(mesh, vertexId):
    """
    Get vertices connected to a given vertex

    :param mesh: mesh to get vert connectivity from
    :param vertexId: vertex Id to get the connected vertices of
    """
    # Get the active selection
    mSel = om.MSelectionList()

    om.MGlobal.getSelectionListByName("{}.vtx[{}]".format(mesh, vertexId), mSel)
    dagPath = om.MDagPath()
    component = om.MObject()
    mSel.getDagPath(0, dagPath, component)

    # Iterate and calculate vectors based on connected vertices
    iter = om.MItMeshVertex(dagPath, component)
    connectedVertices = om.MIntArray()
    iter.getConnectedVertices(connectedVertices)

    return connectedVertices
