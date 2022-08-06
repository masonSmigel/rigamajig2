"""
uv functions
"""
import maya.cmds as cmds
import maya.mel as mel
import rigamajig2.maya.shape
import rigamajig2.shared.common as common


def hasUvs(obj):
    """
    Check if an object has Uvs
    :param obj: Object to check for Uvs
    :return:
    """

    if isinstance(obj, (list, tuple)):
        obj = obj[0]

    uvs = cmds.polyEvaluate(obj, uvComponent=True)


def getUvCoordsFromVertex(geometry, vertexId):
    """
    Get U and V coordinates from vertex id
    :param geometry: geometry to get Uv position from
    :param vertexId: Vertex Id to get UV of.
    :return: U and V coordiates
    :rtype: tuple
    """

    if rigamajig2.maya.shape.getType(geometry) != 'mesh':
        return
    cmds.select('{}.vtx[{}]'.format(geometry, vertexId), r=True)
    mel.eval("ConvertSelectionToUVs()")
    uvs = cmds.polyEditUV(q=True)
    cmds.select(clear=True)
    return uvs[0], uvs[1]


def transferUvsToRigged(source, targets):
    """
    transfer Uvs to a rigged model.
    :param source: mesh with the uvs to transfer to targets
    :param targets: mesh(s) to transfer the Uvs to
    :return:
    """
    source = common.getFirstIndex(source)
    targets = common.toList(targets)

    for target in targets:
        targetShapes = cmds.listRelatives(target, s=True, pa=True)
        orig = None
        for shape in targetShapes:
            if cmds.getAttr('{}.intermediateObject'.format(shape)):
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


