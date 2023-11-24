"""
uv functions
"""
import maya.cmds as cmds
import maya.mel as mel

import rigamajig2.maya.mesh
import rigamajig2.maya.shape
import rigamajig2.shared.common as common


def hasUvs(obj):
    """
    Check if an object has Uvs

    :param obj: Object to check for Uvs
    :return: True if an object has UVs
    :rtype: uvs
    """
    obj = common.getFirst(obj)
    return bool(cmds.polyEvaluate(obj, uvcoord=True))


def getUvCoordsFromVertex(geometry, vertexId):
    """
    Get U and V coordinates from vertex id

    :param geometry: geometry to get Uv position from
    :param vertexId: Vertex Id to get UV of.
    :return: U and V coordiates
    :rtype: tuple
    """

    if rigamajig2.maya.shape.getType(geometry) != "mesh":
        return None
    cmds.select("{}.vtx[{}]".format(geometry, vertexId), r=True)
    mel.eval("ConvertSelectionToUVs()")
    uvs = cmds.polyEditUV(q=True)
    cmds.select(clear=True)
    return uvs[0], uvs[1]


def checkIfOverlapping(geometry):
    """
    Check if the provided geometry has overlapping UVs
    :param geometry: geometry to check if is overlapping
    :return: True if the mesh has overlapping Uvs False if it does not.
    """
    geometry = common.getFirst(geometry)

    if rigamajig2.maya.shape.getType(geometry) != "mesh":
        return False

    uvComponentList = cmds.polyListComponentConversion(geometry, toUV=True)
    overlap = common.toList(
        cmds.polyUVOverlap(uvComponentList, overlappingComponents=True)
    )
    return bool(overlap)


def transferUvsToRigged(source, targets):
    """
    transfer Uvs to a rigged model.
    This is really usefull when a model has updates but a rigamajig2 rig was not used to construct the rig,
    therefore making uv changes more difficult.

    The tool works by temporarily turning off the orig shape allowing us to transfer the UVs
    and delete history without damaging the deformation stack


    :param str source: mesh with the uvs to transfer to targets
    :param str targets: mesh(s) to transfer the Uvs to
    """
    source = common.getFirst(source)
    targets = common.toList(targets)

    for target in targets:
        targetShapes = cmds.listRelatives(target, s=True, pa=True)
        orig = None
        for shape in targetShapes:
            if cmds.getAttr("{}.intermediateObject".format(shape)):
                orig = shape
                break

        if orig is None:
            raise Exception("Target mesh '{}' has no origin shape".format(target))

        # turn off the indermidate object switch temporaily to transfer the UVs
        cmds.setAttr("{}.intermediateObject".format(orig), 0)
        cmds.transferAttributes(source, orig, transferUVs=True, searchMethod=3)

        # delete construction history and turn the intermidete object back on
        cmds.delete(orig, ch=True)
        cmds.setAttr("{}.intermediateObject".format(orig), 1)
        print("\tsuccessfully transfered Uvs from '{}' to '{}'".format(source, orig))


def transferUVs(sourceMesh, targetMesh, checkVertCount=True, constructionHistory=False):
    """
    Transfer the uvs from one mesh to another. This will also check to ensure the models have a compatable vertex count.

    :param str  sourceMesh: mesh with the source UVs
    :param str targetMesh: mesh to tranfer the UVs to.
    :param bool checkVertCount: check if the vertex counts match. If they dont then no transfer will take place
    :param bool constructionHistory: if True keep history at the end of the transfer. Default is False
    :return:
    """

    if not rigamajig2.maya.mesh.isMesh(sourceMesh):
        raise Exception(
            "{} is not a mesh object. Cannot transfer UVs on non-mesh objects.".format(
                sourceMesh
            )
        )

    if not rigamajig2.maya.mesh.isMesh(targetMesh):
        raise Exception(
            "{} is not a mesh object. Cannot transfer UVs on non-mesh objects.".format(
                targetMesh
            )
        )

    if checkVertCount:
        sourceVertCount = len(rigamajig2.maya.mesh.getVerts(sourceMesh))
        targetVertCount = len(rigamajig2.maya.mesh.getVerts(targetMesh))

        if sourceVertCount != targetVertCount:
            raise Exception(
                "vertex count of target {} does not match source {}".format(
                    targetMesh, sourceMesh
                )
            )

    # finally after all the checks we can do the transfer. This command used units instead of bools...
    # its probaly to account for any future additions.
    # Just to be super safe I'm using units even though True and False return 1 and 0.
    cmds.transferAttributes(
        sourceMesh,
        targetMesh,
        transferUVs=1,
        transferColors=0,
        transferNormals=0,
        transferPositions=0,
        searchMethod=3,
    )

    # next we need to delete the extra color sets that seem to always transfer anyway
    colorSets = cmds.polyColorSet(targetMesh, q=True, allColorSets=True) or []
    for colorSet in colorSets:
        cmds.polyColorSet(targetMesh, delete=True, colorSet=colorSet)

    if not constructionHistory:
        cmds.delete(targetMesh, constructionHistory=True)

    print("transfered UVs from {}  to {}".format(sourceMesh, targetMesh))
