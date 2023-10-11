"""
Geometry utilities
"""
import maya.api.OpenMaya as om2
import maya.cmds as cmds

import rigamajig2.maya.shape as shape
import rigamajig2.shared.common as common


def isMesh(node):
    """
    check if the node is a mesh.
    The function will return True for both transforms with a mesh Shape node or for a mesh Shapenode

    :param node: node to check
    :return: If the provided node is a mesh
    :rtype: bool
    """
    if not cmds.objExists(node): return False

    if 'transform' in cmds.nodeType(node, i=True):
        shape = cmds.ls(cmds.listRelatives(node, s=True, ni=True, pa=True) or [], type='mesh')
        if not shape: return False
        node = shape[0]
    if cmds.objExists(cmds.objExists(node) != 'mesh'): return False

    return True


def getMeshFn(mesh):
    """
    Get the MFn mesh object for a given mesh

    :param mesh: mesh name
    :return: Open Maya API mesh function set object.
    :rtype: MFnMesh
    """
    selList = om2.MSelectionList()
    selList.add(mesh)
    dagPath = selList.getDagPath(0)
    meshFn = om2.MFnMesh(dagPath)

    return meshFn


def getVertPositions(mesh, world=True):
    """
    Get a list of vertex positions for a single mesh.

    :param str mesh: mesh to get positions of
    :param bool world: Get the vertex position in world space. False is local position
    :return: List of vertex positions
    :rtype: list
    """
    if isinstance(mesh, (list, tuple)):
        mesh = mesh[0]

    if shape.getType(mesh) != 'mesh':
        cmds.error("Node must be of type 'mesh'. {} is of type {}".format(mesh, shape.getType(mesh)))

    sel = om2.MGlobal.getSelectionListByName(mesh)
    dagPath = sel.getDagPath(0)

    meshFn = om2.MFnMesh(dagPath)

    if world:
        points = meshFn.getPoints(space=om2.MSpace.kWorld)
    else:
        points = meshFn.getPoints(space=om2.MSpace.kObject)

    vertPos = list()
    for i in range((len(points))):
        vertPos.append([round(points[i].x, 5), round(points[i].y, 5), round(points[i].z, 5)])

    return vertPos


def setVertPositions(mesh, vertList, world=False):
    """
    Using a list of vertex positions set the vertex positions of the provided mesh.
    This function uses the maya commands. it is slower than the API version but undoable if run from the script editor.

    :param str mesh: mesh to set the vertices of
    :param list vertList: list of vertex positions:
    :param bool world: Space to set the vertex positions
    """
    for i, vtx in enumerate(getVerts(mesh)):
        if world:
            cmds.xform(vtx, worldSpace=True, translation=vertList[i])
        else:
            cmds.xform(vtx, worldSpace=False, translation=vertList[i])


def getVerts(mesh):
    """
    get a list of all verticies in a mesh

    :param str mesh: mesh to get verticies of
    :return: list of verticies. ie ('pCube1.vtx[0]', 'pCube1.vtx[1]'...)
    :rtype: list

    """
    if isinstance(mesh, (list, tuple)):
        mesh = mesh[0]

    verts = cmds.ls("{}.vtx[*]".format(mesh))
    return common.flattenList(verts)


def getVertexNormal(mesh, vertex, world=True):
    """
    Get the vertex normal of a vertex

    :param str mesh: mesh to get the vertex normal of
    :param int vertex: vertex ID to get the normal of
    :param bool world: Space to get the vertex normal in
    :return:
    """

    if isinstance(mesh, (list, tuple)):
        mesh = mesh[0]

    if shape.getType(mesh) != 'mesh':
        cmds.error("Node must be of type 'mesh'. {} is of type {}".format(mesh, shape.getType(mesh)))

    mfnMesh = getMeshFn(mesh)

    # fn_mesh.getVertexNormal(vertex, False, om.MSpace.kWorld)
    space = om2.MSpace.kWorld if world else om2.MSpace.kObject

    vertexNormal = mfnMesh.getVertexNormal(vertex, False, space)

    return vertexNormal


