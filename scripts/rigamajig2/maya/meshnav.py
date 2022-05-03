"""
This module contains functions to navigate mesh topology
"""

import maya.api.OpenMaya as om2
import maya.cmds as cmds
import rigamajig2.maya.mesh


def getClosestFace(mesh, point):
    """
    Return closest face on mesh to the point.
    :param mesh: mesh name
    :param point: world space coordinate
    :return: tuple of vertex id and distance to point
    :rtype: tuple
    """
    faceId = getClosestFacePoint(mesh, point)[-1]
    return mesh + '.f[{}]'.format(faceId)


def getClosestFacePoint(mesh, point):
    """
    Return closest facePoint on mesh to the point.
    :param mesh: mesh name
    :param point: world space coordinate
    :return: tuple of vertex id and distance to point
    :rtype: tuple
    """
    mfnMesh = rigamajig2.maya.mesh.getMeshFn(mesh)

    pos = om2.MPoint(point[0], point[1], point[2])
    return mfnMesh.getClosestPoint(pos, om2.MSpace.kWorld)


def getClosestVertex(mesh, point):
    """
    Return closest vertex on mesh to the point.
    :param mesh: mesh to get the closest vertex of
    :param point: world space coordinate
    :return: tuple of vertex id and distance to point
    :rtype: tuple
    """
    pos = om2.MPoint(point[0], point[1], point[2])
    mfn_mesh = rigamajig2.maya.mesh.getMeshFn(mesh)

    index = mfn_mesh.getClosestPoint(pos, space=om2.MSpace.kWorld)[1]
    faceVtx = mfn_mesh.getPolygonVertices(index)
    vtxDist = [(vtx, mfn_mesh.getPoint(vtx, om2.MSpace.kWorld).distanceTo(pos)) for vtx in faceVtx]

    return min(vtxDist, key=operator.itemgetter(1))


def getClosestUV(mesh, point):
    """
    Return closest UV on mesh to the point.
    :param mesh: mesh name
    :param point: world space coordinate
    :return: Uv coordinates
    :rtype: tuple
    """

    mfnMesh = rigamajig2.maya.mesh.getMeshFn(mesh)

    pos = om2.MPoint(point[0], point[1], point[2])
    uvFace = mfnMesh.getUVAtPoint(pos)
    closest_UV = (uvFace[0], uvFace[1])
    return closest_UV


# bounding box Info
def getBboxCenter(obj):
    """
    Get the bounding box center of a mesh object
    :param obj: object name
    :return:
    """
    bbox = cmds.exactWorldBoundingBox(obj)
    bbox_min = bbox[:3]
    bbox_max = bbox[3:]
    center = [(bbox_min[x] + bbox_max[x]) / 2.0 for x in range(3)]
    return center
