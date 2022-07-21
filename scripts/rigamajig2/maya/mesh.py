"""
Geometry utilities
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2

import rigamajig2.shared.common as common
import rigamajig2.maya.shape as shape


def isMesh(node):
    """
    check if the node is a mesh
    :param node: node to check
    :return:
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
    :return: mesh function set
    """
    selList = om2.MSelectionList()
    selList.add(mesh)
    dagPath = selList.getDagPath(0)
    meshFn = om2.MFnMesh(dagPath)

    return meshFn


def getVertPositions(mesh, world=True):
    """
    get a list of all mesh vertex positions.
    :param mesh: mesh to get positions of
    :param world: Get the vertex position in world space. False is local position
    :return: List of vertex positions
    :rtype: list
    """
    if isinstance(mesh, (list, tuple)):
        mesh = mesh[0]

    if not shape.getType(mesh) == 'mesh':
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
    :param mesh: mesh to set the vertices of
    :param vertList: list of vertex positions:
    :param world: Space to set the vertex positions
    :return:
    """
    for i, vtx in enumerate(getVerts(mesh)):
        if world:
            cmds.xform(vtx, worldSpace=True, translation=vertList[i])
        else:
            cmds.xform(vtx, worldSpace=False, translation=vertList[i])


def getVerts(mesh):
    """
    get a list of all verticies in a mesh
    :param mesh: mesh to get verticies of
    :type mesh: str

    :return: list of verticies. ie ('pCube1.vtx[0]', 'pCube1.vtx[1]'...)
    :rtype: list

    """
    if isinstance(mesh, (list, tuple)):
        mesh = mesh[0]

    verts = cmds.ls("{}.vtx[*]".format(mesh))
    return common.flattenList(verts)


def cleanShapes(nodes):
    """
    Cleanup a shape nodes. removes intermediate
    :param nodes:
    :return:
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.nodeType(node) in ['nurbsSurface', 'mesh', 'nurbsCurve']:
            node = cmds.listRelatives(node, p=True)
        shapes = cmds.listRelatives(node, s=True, ni=False, pa=True) or []

        if len(shapes) == 1:
            return shapes[0]
        else:
            intermidiate_shapes = [x for x in shapes if cmds.getAttr('{}.intermediateObject'.format(x))]
            cmds.delete(intermidiate_shapes)
            print("Deleted Intermeidate Shapes: {}".format(intermidiate_shapes))


def cleanModel(nodes=None):
    """
    Clean up model
    :param nodes: meshes to clean
    """
    if not nodes:
        nodes = cmds.ls(sl=True)
    nodes = common.toList(nodes)

    for node in nodes:
        cmds.delete(node, ch=True)
        cmds.makeIdentity(node, apply=True, t=True, r=True, s=True, n=0, pn=1)
        cmds.xform(node, a=True, ws=True, rp=(0, 0, 0), sp=(0, 0, 0))
        if isMesh(node):
            cleanShapes(node)
            print('Cleaned Mesh: {}'.format(node))
