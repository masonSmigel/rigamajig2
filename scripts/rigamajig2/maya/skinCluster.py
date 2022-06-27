# coding=utf-8
"""
Functions for skin clusters. 


Thanks to:
Charles Wardlaw: Deformation Layering in Maya’s Parallel GPU World 
(https://medium.com/@kattkieru/deformation-layering-in-mayas-parallel-gpu-world-15c2e3d66d82)
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

import rigamajig2.shared.common
import rigamajig2.maya.deformer
import rigamajig2.maya.utils
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
    deformers = rigamajig2.maya.deformer.getDeformersForShape(shape)
    skins = list(filter(lambda x: cmds.nodeType(x) == 'skinCluster', deformers))

    assert len(skins) < 2, "Cannot use getSkinCluster on Stacked Skins"
    skin = skins[0] if len(skins) else None
    if skin:
        # This is a tip from Charles Wardlaw,
        # always ensure skin clusters weight distribution is set to neighbors.
        # setting it here ensrures that any time we tough a skincluster it gets set properly
        cmds.setAttr("{}.weightDistribution".format(skin), 1)

    return skin


def getMfnSkin(skinCluster):
    """
    Get a skin cluster function set from the skin cluster name
    :param skinCluster:
    :return:
    """
    if not isSkinCluster(skinCluster):
        raise Exception("{} is not a skinCluster".format(skinCluster))

    skinClusterObj = rigamajig2.maya.utils.getMObject(skinCluster)
    return oma2.MFnSkinCluster(skinClusterObj)


def getMfnMesh(mesh):
    """
    :param mesh: name of the mesh to get the Mfn mesh object from
    :return:
    """
    mesh = rigamajig2.maya.utils.getMObject(mesh)
    return om2.MFnMesh(mesh)


def getCompleteComponents(mesh):
    if not isinstance(mesh, om2.MFnMesh):
        mesh = getMfnMesh(mesh)
    comp = om2.MFnSingleIndexedComponent()
    ob = comp.create(om2.MFn.kMeshVertComponent)
    comp.setCompleteData(mesh.numVertices)
    return ob


def tryMatrixSet(plug, value):
    """try to set a matrix plug to given value. used to avoid errors seting an invalid value"""
    try:
        cmds.setAttr(plug, value)
    except RuntimeError:
        pass


def tryMatrixConnect(plug, target):
    """try to connect a given target to a matrix plug . used to avoid errors seting an invalid value"""
    try:
        cmds.connectAttr(plug, target)
    except RuntimeError:
        pass


def getWeights(mesh):
    """
    Return a list of all skincluster weights on a mesh
    :param mesh: mesh to get the weights on
    :return:
    """
    meshShape = rigamajig2.maya.deformer.getDeformShape(mesh)
    mesh = cmds.listRelatives(meshShape, p=True)[0]

    mesh_skin = getSkinCluster(mesh)
    assert mesh_skin, "No Skin for mesh {} -- cannot save".format(mesh)

    meshDag = rigamajig2.maya.utils.getDagPath(mesh)
    skinMfn = getMfnSkin(mesh_skin)
    meshMfn = getMfnMesh(meshShape)
    components = getCompleteComponents(meshMfn)

    weights, influenceCount = skinMfn.getWeights(meshDag, components)

    influences = getInfluenceObjects(skinMfn)
    numInfluences = len(list(influences))
    numComponentsPerInfluence = int(len(weights) / numInfluences)

    weightDict = {}
    for ii in range(len(influences)):
        influenceName = influences[ii]
        influenceNoNs = influenceName.split(":")[-1]

        # build a dictionary of vtx:weight. Skip 0.0 weights
        # This is a super slick solution from Mgear!
        infWeightDict = {
            jj: weights[jj * numInfluences + ii]
            for jj in range(numComponentsPerInfluence)
            if weights[jj * numInfluences + ii] != 0.0
            }
        vertexCount = int(len(weights) / float(numInfluences))
        weightDict[str(influenceNoNs)] = infWeightDict
    return weightDict, vertexCount


def setWeights(mesh, skincluster, weightDict, compressed=True):
    """
    Set the skin cluster weights of a given mesh

    :param mesh: mesh to set the weights on
    :param skincluster: skin cluster node to hold the weights
    :param weightDict: skin cluster dict holding weight values for each influence
    :param compressed: if the weights are compressed or not
    :return:
    """
    meshShape = rigamajig2.maya.deformer.getDeformShape(mesh)

    skinMfn = getMfnSkin(skincluster)
    meshMfn = getMfnMesh(meshShape)
    meshDag = rigamajig2.maya.utils.getDagPath(meshShape)
    components = getCompleteComponents(meshMfn)

    weights, influenceCount = skinMfn.getWeights(meshDag, components)
    weightList = weights

    influences = getInfluenceObjects(skinMfn)
    numInfluences = len(list(influences))
    numComponentsPerInfluence = int(len(weights) / numInfluences)

    for importedIfluence, wtValues in weightDict.items():
        for ii in range(len(influences)):
            influenceName = influences[ii]
            influenceNoNs = influenceName.split(":")[-1]
            if influenceNoNs == importedIfluence:
                if compressed:
                    for jj in range(numComponentsPerInfluence):
                        wt = wtValues.get(jj) or wtValues.get(str(jj)) or 0.0
                        weightList[jj * numInfluences + ii] = wt
    allIndices = om2.MIntArray(range(numInfluences))
    skinMfn.setWeights(meshDag, components, allIndices, weightList, False)

    # normalize the skinweights. This is to account for any floating point precision issues.
    # even though they mostly would not be noticable its safer to manually normalize any drift.
    cmds.skinPercent(skincluster, meshShape, normalize=True)

    # Recache the bind matricies. This is from Charles Wardlaw.
    # Ensures the skin behaves correctly durring playback
    cmds.skinCluster(skincluster, e=True, recacheBindMatrices=True)


def getBlendWeights(mesh):
    """
    Get the DQ blended weights
    :param mesh: mesh to get weights on
    :return:
    """
    meshShape = rigamajig2.maya.deformer.getDeformShape(mesh)
    mesh = cmds.listRelatives(meshShape, p=True)[0]

    mesh_skin = getSkinCluster(mesh)
    assert mesh_skin, "No Skin for mesh {} -- cannot save".format(mesh)

    meshDag = rigamajig2.maya.utils.getDagPath(mesh)
    skinMfn = getMfnSkin(mesh_skin)
    meshMfn = getMfnMesh(meshShape)
    components = getCompleteComponents(meshMfn)

    weights = skinMfn.getBlendWeights(meshDag, components)
    # round the weights down. This should be safe on Dual Quat blends
    # because it is not normalized. And 6 should be more than accurate enough.
    weightList = dict()
    for i in range((len(weights))):
        value = round(weights[i], 6)
        if value > 0.0:
            weightList[i] = value

    return weightList


def setBlendWeights(mesh, skincluster, weightDict, compressed=True):
    """
    Set the Blended weights
    :param mesh:
    :param skincluster:
    :param weightDict:
    :param compressed:
    :return:
    """
    meshShape = rigamajig2.maya.deformer.getDeformShape(mesh)

    skinMfn = getMfnSkin(skincluster)
    meshMfn = getMfnMesh(meshShape)
    meshDag = rigamajig2.maya.utils.getDagPath(meshShape)
    components = getCompleteComponents(meshMfn)

    numVerts = skinMfn.getBlendWeights(meshDag, components)
    blendedWeights = om2.MDoubleArray(range(len(numVerts)))

    if compressed:
        for i in range(len(blendedWeights)):
            wt = weightDict.get(i) or weightDict.get(str(i)) or 0.0
            blendedWeights[int(i)] = wt
    else:
        raise NotImplementedError("Not implemented")

    # print len(blendedWeights), components.length()
    skinMfn.setBlendWeights(meshDag, components, blendedWeights)


def getInfluenceObjects(skinCluster):
    """
    Get the influences of a skin cluster
    :param skinCluster: skinCluster to get influences from
    :return:
    """
    if not isinstance(skinCluster, oma2.MFnSkinCluster):
        skinCluster = getMfnSkin(skinCluster)

    infPathArray = skinCluster.influenceObjects()
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
    skinClusterFn = getMfnSkin(skinCluster)
    influencePath = rigamajig2.maya.utils.getDagPath(influence)

    return skinClusterFn.indexForInfluenceObject(influencePath)


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


def stack_skinclusters(source, target):
    """
    create stacked skinclusters
    :param source: mesh to copy skincluster from
    :param target: mesh to add new skin cluster too
    """
    pass


if __name__ == '__main__':
    print(getSkinCluster(cmds.ls(sl=True)))
