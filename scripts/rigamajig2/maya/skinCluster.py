# coding=utf-8
"""
Functions for skin clusters. 


Thanks to:
Charles Wardlaw: Deformation Layering in Maya’s Parallel GPU World 
(https://medium.com/@kattkieru/deformation-layering-in-mayas-parallel-gpu-world-15c2e3d66d82)
"""
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

import rigamajig2.shared.common
import rigamajig2.maya.deformer
import rigamajig2.maya.omUtils
import rigamajig2.maya.shape


def isSkinCluster(skinCluster):
    """
    Check if the skincluster is a valid skincluster
    :param skinCluster:  name of skincluster to check
    :return: True if Valid. False is invalid.
    """
    if not cmds.objExists(skinCluster): return False
    if cmds.nodeType(skinCluster) != 'skinCluster': return False
    return True


def getSkinCluster(obj):
    """
    Get the skincluster connected to this node
    :param obj: object to get connected skin cluster
    :return: Skin cluster node
    """
    shape = rigamajig2.maya.deformer.getDeformShape(obj)
    if shape is None:
        return None
    skin = mel.eval('findRelatedSkinCluster "' + shape + '"')
    if not skin:
        skins = cmds.ls(cmds.listHistory(shape), type='skinCluster')
        if skin: skin = skins[0]
    if not skin: return None

    return skin


def create():
    """
    :return:
    """
    pass


def getSkinClusterFn(skinCluster):
    """
    Get a skin cluster function set from the skin cluster name
    :param skinCluster:
    :return:
    """
    if not isSkinCluster(skinCluster):
        raise Exception("{} is not a skinCluster".format(skinCluster))

    selectionList = om2.MSelectionList()
    selectionList.add(skinCluster)
    skinClusterObj = selectionList.getDependNode(0)
    skinClusterFn = oma2.MFnSkinCluster(skinClusterObj)
    return skinClusterFn


def getInfluenceObjects(skinCluster):
    """
    Get the influences of a skin cluster
    :param skinCluster: skinCluster to get influences from
    :return:
    """
    skinClusterFn = getSkinClusterFn(skinCluster)

    infPathArray = skinClusterFn.influenceObjects()
    infuenceNameArray = [infPathArray[i].partialPathName() for i in range(len(infPathArray))]

    return infuenceNameArray


def getInfluenceIndex(skinCluster, influence):
    """
    Get the index of an influence for a specified skin cluster
    :param skinCluster: Skincluster to get the index from
    :param influence: influcence of a skin cluster to get index of
    :return: index of a given influence
    """
    if not isSkinCluster(skinCluster):
        raise Exception("{} is not a skinCluster".format(skinCluster))
    if not cmds.objExists(influence):
        raise Exception("Influcence Object {} does not exist".format(influence))
    skinClusterFn = getSkinClusterFn(skinCluster)
    influencePath = rigamajig2.maya.omUtils.getDagPath2(influence)

    return skinClusterFn.indexForInfluenceObject(influencePath)


def getIfluenceAtIndex(skinCluster, influenceIndex):
    """
    Return the skin cluster influence at the index
    :param skinCluster: Skincluster to get the influence from
    :param influenceIndex: influence index to query
    :return: influence at index
    :rtype: str
    """
    if not isSkinCluster(skinCluster):
        raise Exception("{} is not a skinCluster".format(skinCluster))

    infConnections = cmds.listConnections(skinCluster + '.matrix[{}]'.format(influenceIndex), s=True, d=False)

    if not infConnections: raise Exception("No influence at index {}".format(influenceIndex))
    return infConnections[0]


def getInfluencePhysicalIndex(skinCluster, influence):
    """
    Return a physical index of an index for a specified skin cluster
    :param skinCluster: Skincluster to get the index from
    :param influence: influcence of a skin cluster to get index of
    :return: index of a given influence
    """
    if not isSkinCluster(skinCluster):
        raise Exception("{} is not a skinCluster".format(skinCluster))
    if not cmds.objExists(influence):
        raise Exception("Influcence Object {} does not exist".format(influence))

    skinClusterFn = getSkinClusterFn(skinCluster)

    infPathArray = skinClusterFn.influenceObjects()
    infuenceNameArray = [infPathArray[i].partialPathName() for i in range(len(infPathArray))]

    if influence not in infuenceNameArray:
        raise Exception("Unable to determine index for influence {}".format(influence))
    influenceIndex = infuenceNameArray.index(influence)

    return influenceIndex


def getWeights(skinCluster, influences=None, geometry=None):
    """
    Return the weights of an influnce for a specified skin cluster.
    Optionally pass influences, to only get specifed influences
    :param skinCluster: Skin cluster to get the weights of
    :param influences: Optional - Infuluence to query weights of. If None all are set from skincluster are used
    :param geometry: Optional -Name of geometry to get weights from
    :return:  list of component weights
    """
    weightList = dict()
    if not isSkinCluster(skinCluster):
        raise Exception("{} is not a skinCluster".format(skinCluster))

    if geometry:
        if not cmds.objExists(geometry): raise Exception("{} does not exist".format(geometry))
    else:
        geometry = rigamajig2.maya.deformer.getAffectedGeo(skinCluster)[0]

    point_count = rigamajig2.maya.shape.getPointCount(geometry) - 1

    if not influences:
        influences = getInfluenceObjects(skinCluster)
    else:
        influences = rigamajig2.shared.common.toList(influences)

    cmds.skinPercent(skinCluster, geometry, pruneWeights=0.005)
    for inf in influences:
        influenceIndex = getInfluenceIndex(skinCluster, inf)
        attr = "{}.wl[0:{}].w[{}]".format(skinCluster, point_count, influenceIndex)
        values = cmds.getAttr(attr)
        values = [round(v, 5) for v in values]
        weightList[inf] = values
    return weightList


def setWeights(skinCluster, weights, influences=None, geometry=None):
    """
    Set the skincluster weights.
    Optionally pass influences, to only set specifed influences
    :param skinCluster: skincluster to set Weights of
    :param weights: dictionary of influences and weight values
    :param influences: Optional- influences to set. If None all are set from the weight list
    :param geometry: Optional -Name of geometry to set weights on
    :return:
    """
    if not isSkinCluster(skinCluster):
        raise Exception("{} is not a skinCluster".format(skinCluster))

    if geometry:
        if not cmds.objExists(geometry): raise Exception("{} does not exist".format(geometry))
    else:
        geometry = rigamajig2.maya.deformer.getAffectedGeo(skinCluster)[0]

    point_count = rigamajig2.maya.shape.getPointCount(geometry) - 1

    if not influences:
        influences = weights.keys()
    else:
        influences = rigamajig2.shared.common.toList(influences)

    for inf in influences:
        influenceIndex = getInfluenceIndex(skinCluster, inf)
        attr = "{}.wl[0:{}].w[{}]".format(skinCluster, point_count, influenceIndex)
        weightList = weights[inf]
        cmds.setAttr(attr, *weightList)


def localize(skinclusters, transform):
    """
    Localize skincluster to given transform

    TODO: watch Cult of Rig to see how to build that
    :return:
    """
    for skincluster in skinclusters:
        pass


def break_localization(skinClusters):
    """
    Remove Localization from skinclusters
    :return:
    """
    for skinClusters in skinClusters:
        pass


def layer_skinclusters(source, target):
    """
    create layered skinclusters
    :param source: mesh to copy skincluster from
    :param target: mesh to add new skin cluster too
    """
    pass


if __name__ == '__main__':
    print(getSkinCluster(cmds.ls(sl=True)))
