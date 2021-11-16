"""
uv functions
"""
import maya.cmds as cmds
import maya.mel as mel
import rigamajig2.maya.shape


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

    if not rigamajig2.maya.shape.getType(geometry) == 'mesh':
        return
    cmds.select('{}.vtx[{}]'.format(geometry, vertexId), r=True)
    mel.eval("ConvertSelectionToUVs()")
    uvs = cmds.polyEditUV(q=True)
    cmds.select(clear=True)
    return uvs[0], uvs[1]
