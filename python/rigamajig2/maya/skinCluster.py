# coding=utf-8
"""
Functions for skin clusters. 


Thanks to:
Charles Wardlaw: Deformation Layering in Maya’s Parallel GPU World 
(https://medium.com/@kattkieru/deformation-layering-in-mayas-parallel-gpu-world-15c2e3d66d82)
"""
from typing import Union, Dict, Tuple, Optional, List

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

from rigamajig2.maya import deformer
from rigamajig2.maya import general
from rigamajig2.shared.common import toList, getFirst


class SurfaceCopyMode:
    ClosestPoint = "closestPoint"
    RayCast = "rayCast"
    ClosestComponent = "closestComponent"


class InfluenceCopyMode:
    ClosestJoint = "closestJoint"
    ClosestBone = "closestBone"
    JointLabel = "label"
    JointName = "name"
    OneToOne = "oneToOne"


class BindMethod:
    ClosestJoint = 0
    ClosestInHierarchy = 1
    HeatMap = 2
    GeodesicVoxel = 3


class NormalizationMode:
    NoNormalization = 0
    Interactive = 1
    Post = 1


class WeighDistribution:
    Distance = 0
    Neighbors = 1


def isSkinCluster(skinCluster: str) -> bool:
    """
    Check if the skincluster is a valid skincluster

    :param skinCluster:  name of skincluster to check
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    if skinCluster is None:
        return False
    if not cmds.objExists(skinCluster):
        return False
    if cmds.nodeType(skinCluster) != "skinCluster":
        return False
    return True


def createSkinCluster(
    geometry: str,
    influences: List[str],
    skinClusterName: Optional[str] = None,
    bindMethod=BindMethod.ClosestJoint,
    smoothWeights: float = 0.0,
    normalizeWeights: int = NormalizationMode.Interactive,
    maxInfluences: int = 3,
    dropoffRate: float = 1.0,
    weighDistribution=WeighDistribution.Neighbors,
):
    """
    Create a skin cluster

    :param geometry: geometry to skin
    :param influences: influence joints
    :param skinClusterName: skin cluster name
    :param bindMethod: bind method to use (BindMethod)
    :param smoothWeights: smooth the weights. Value between 0 and 1
    :param normalizeWeights: weight normalization mode (NormaliationMode)
    :param maxInfluences: Sets the maximum number of transforms that can influence a point
    :param dropoffRate:Sets the rate at which the influence of a transform drops as the distance from that transform increases.
    :param weighDistribution: Sets the weight DistributionMode
    :return:
    """
    if not skinClusterName:
        skinClusterName = f"{geometry}_skinCluster"

    resultSkinCluster = cmds.skinCluster(
        influences,
        geometry,
        name=skinClusterName,
        toSelectedBones=True,
        bindMethod=bindMethod,
        smoothWeights=smoothWeights,
        normalizeWeights=normalizeWeights,
        maximumInfluences=maxInfluences,
        dropoffRate=dropoffRate,
        weightDistribution=weighDistribution,
    )

    return getFirst(resultSkinCluster)


def getAllSkinClusters(obj: str) -> List[str]:
    """
    Get a list of all the skinclusters on a target object

    :param obj: object to get connected skin cluster
    :return: list of all skinclusters on an object
    :rtype: list
    """
    shape = deformer.getDeformShape(obj)
    if shape is None:
        return list()
    deformers = deformer.getDeformersForShape(shape)
    skins = [x for x in deformers if cmds.nodeType(x) == "skinCluster"]
    return skins


def getSkinCluster(obj: str) -> str:
    """
    Get the skincluster connected to this node

    :param obj: object to get connected skin cluster
    :return: Skin cluster node
    :rtype: str
    """
    skins = getAllSkinClusters(obj)

    assert (
        len(skins) < 2
    ), "Cannot use getSkinCluster on Stacked Skins. Please use get all Skinclusters instead"
    skin = skins[0] if len(skins) else None
    if skin:
        # This is a tip from Charles Wardlaw,
        # always ensure skin clusters weight distribution is set to neighbors.
        # setting it here ensrures that any time we tough a skincluster it gets set properly
        cmds.setAttr("{}.weightDistribution".format(skin), 1)

    return skin


def getMfnSkin(skinCluster: str) -> oma.MFnSkinCluster:
    """
    Get a skin cluster function set from the skin cluster name

    :param skinCluster: name of the skin cluster node
    :return: an om.MFnSkinCluster object
    :rtype MfnSkinCluster
    """
    if not isSkinCluster(skinCluster):
        raise Exception("{} is not a skinCluster".format(skinCluster))

    skinClusterObj = general.getMObject(skinCluster)
    return oma.MFnSkinCluster(skinClusterObj)


def getMfnShape(mesh):
    """
     Get a mesh function set from the skin cluster name

    :param str mesh: name of the mesh or nurbsCurve to get the Mfn object from
    :return: MFnMesh | MFnNurbsCurve
    """
    mObj = general.getMObject(mesh)
    dependNode = om.MFnDependencyNode(mObj)

    if cmds.nodeType(dependNode.name()) == "mesh":
        return om.MFnMesh(mObj)
    elif cmds.nodeType(dependNode.name()) == "nurbsCurve":
        return om.MFnNurbsCurve(mObj)


def getCompleteComponents(
    shape: Union[str, om.MFnMesh, om.MFnNurbsCurve]
) -> om.MFnSingleIndexedComponent:
    """
    Wrapper to get the complete component data from a mesh

    :param str shape: shape to get the component data from
    :return: complete component data
    """

    if isinstance(shape, om.MFnMesh):
        nodeType = "mesh"
    elif isinstance(shape, om.MFnNurbsCurve):
        nodeType = "nurbsCurve"
    else:
        nodeType = cmds.nodeType(shape)
        shape = getMfnShape(shape)

    if nodeType == "mesh":
        indexedComponent = om.MFnSingleIndexedComponent()
        completeComponentData = indexedComponent.create(om.MFn.kMeshVertComponent)
        indexedComponent.setCompleteData(shape.numVertices)
        return completeComponentData
    elif nodeType == "nurbsCurve":
        indexedComponent = om.MFnSingleIndexedComponent()
        completeComponentData = indexedComponent.create(om.MFn.kCurveCVComponent)
        indexedComponent.setCompleteData(shape.numCVs)
        return completeComponentData


def getWeights(mesh: str) -> Tuple[Dict[str, Dict[int, float]], int]:
    """
    Return a list of all skincluster weights on a mesh

    :param mesh: mesh (or NurbsCurve) to get the weights on
    :return: weight dictionary and vertex count. {"influence":[]}
    :rtype: list
    """
    meshShape = deformer.getDeformShape(mesh)
    mesh = cmds.listRelatives(meshShape, parent=True)[0]

    meshSkin = getSkinCluster(mesh)
    assert meshSkin, "No Skin for mesh {} -- cannot save".format(mesh)

    meshDag = general.getDagPath(mesh)
    skinMfn = getMfnSkin(meshSkin)
    shapeMfn = getMfnShape(meshShape)
    components = getCompleteComponents(shapeMfn)

    weights, influenceCount = skinMfn.getWeights(meshDag, components)

    influences = getInfluenceJoints(skinMfn)
    numInfluences = len(list(influences))
    numComponentsPerInfluence = int(len(weights) / numInfluences)

    weightDict = {}
    for influence in range(len(influences)):
        influenceName = influences[influence]
        influenceNoNs = influenceName.split(":")[-1]

        # build a dictionary of vtx:weight. Skip 0.0 weights
        infWeightDict = {
            i: weights[i * numInfluences + influence]
            for i in range(numComponentsPerInfluence)
            if weights[i * numInfluences + influence] != 0.0
        }
        vertexCount = int(len(weights) / float(numInfluences))
        weightDict[str(influenceNoNs)] = infWeightDict
    return weightDict, vertexCount


def setWeights(
    mesh: str,
    skincluster: str,
    weightDict: Dict[str, Dict[int, float]],
    compressed=True,
):
    """
    Set the skin cluster weights of a given mesh

    :param mesh: mesh (or NurbsCurve) to set the weights on
    :param skincluster: skin cluster node to hold the weights
    :param weightDict: skin cluster dict holding weight values for each influence
    :param compressed: if the weights are compressed or not
    """
    meshShape = deformer.getDeformShape(mesh)

    skinMfn = getMfnSkin(skincluster)
    shapeMfn = getMfnShape(meshShape)
    meshDag = general.getDagPath(meshShape)
    components = getCompleteComponents(shapeMfn)

    weights, influenceCount = skinMfn.getWeights(meshDag, components)
    weightList = weights

    influences = getInfluenceJoints(skinMfn)
    numInfluences = len(list(influences))
    numComponentsPerInfluence = int(len(weights) / numInfluences)

    for importedInfluence, wtValues in weightDict.items():
        for influence in range(len(influences)):
            influenceName = influences[influence]
            influenceNoNs = influenceName.split(":")[-1]
            if influenceNoNs == importedInfluence:
                if compressed:
                    for i in range(numComponentsPerInfluence):
                        weight = wtValues.get(i) or wtValues.get(str(i)) or 0.0
                        weightList[i * numInfluences + influence] = weight
    allIndices = om.MIntArray(range(numInfluences))
    skinMfn.setWeights(meshDag, components, allIndices, weightList, False)

    # normalize the skinweights. This is to account for any floating point precision issues.
    # even though they mostly would not be noticable its safer to manually normalize any drift.
    cmds.skinPercent(skincluster, meshShape, normalize=True)

    # Recache the bind matrices. This is from Charles Wardlaw.
    # Ensures the skin behaves correctly during playback
    cmds.skinCluster(skincluster, edit=True, recacheBindMatrices=True)


def getBlendWeights(mesh: str) -> Dict[int, float]:
    """
    Get the DQ blended weights

    :param mesh: mesh (or NurbsCurve) to get weights on
    :return: list of blendede weights
    :rtype: list
    """
    meshShape = deformer.getDeformShape(mesh)
    mesh = cmds.listRelatives(meshShape, p=True)[0]

    meshSkin = getSkinCluster(mesh)
    assert meshSkin, "No Skin for mesh {} -- cannot save".format(mesh)

    meshDag = general.getDagPath(mesh)
    skinMfn = getMfnSkin(meshSkin)
    shapeMfn = getMfnShape(meshShape)
    components = getCompleteComponents(shapeMfn)

    weights = skinMfn.getBlendWeights(meshDag, components)
    # round the weights down. This should be safe on Dual Quat blends
    # because it is not normalized. And 6 should be more than accurate enough.
    weightList = dict()
    for i in range((len(weights))):
        value = round(weights[i], 6)
        if value > 0.0:
            weightList[i] = value

    return weightList


def setBlendWeights(
    mesh: str, skincluster: str, weightDict: Dict[int, float], compressed: bool = True
):
    """
    Set the Blended weights

    :param mesh: name of the mesh (or NurbsCurve) to set the blended weights on
    :param skincluster: name of the skincluster to set the blended weights on
    :param weightDict: input weight dictionary
    :param bool compressed: if the data is compressed
    :return:
    """
    meshShape = deformer.getDeformShape(mesh)

    skinMfn = getMfnSkin(skincluster)
    shapeMfn = getMfnShape(meshShape)
    meshDag = general.getDagPath(meshShape)
    components = getCompleteComponents(shapeMfn)

    numVerts = skinMfn.getBlendWeights(meshDag, components)
    blendedWeights = om.MDoubleArray(range(len(numVerts)))

    if compressed:
        for i in range(len(blendedWeights)):
            weight = weightDict.get(i) or weightDict.get(str(i)) or 0.0
            blendedWeights[int(i)] = weight
    else:
        raise NotImplementedError("Not implemented")

    skinMfn.setBlendWeights(meshDag, components, blendedWeights)


def getMatrixConnections(mesh: str, attribute: str = "bindPreMatrix") -> List[str]:
    """
    Get a list of the the nodes or values set on the prebind matrix of each influence joint

    :param mesh: mesh (or NurbsCurve) to get matrix connections from
    :param attribute: Matrix attribute to get the values of.
    :return: A dictionary  of influence joints and the connection or value
    """
    skinCls = getSkinCluster(mesh)

    skinClusterMatrixAttr = "{}.{}".format(skinCls, attribute)

    matrixInputs = list()
    for i in range(len(getInfluenceJoints(skinCls))):
        matrixAttr = "{}[{}]".format(skinClusterMatrixAttr, i)
        matrixInputConnection = cmds.listConnections(
            matrixAttr, plugs=True, s=True, d=False
        )

        # append the result to a list of matricies
        matrixInputs.append(matrixInputConnection[0] if matrixInputConnection else None)

    return matrixInputs


def getMatrixValues(mesh: str, attribute="bindPreMatrix") -> List[List[float]]:
    """
    Get a list of the the nodes or values set on the prebind matrix of each influence joint

    :param mesh: mesh (or NurbsCurve) to get matrix values from
    :param attribute: Matrix attribute to get the values of.
    :return: A dictionary  of influence joints and the connection or value
    """
    skinCls = getSkinCluster(mesh)

    skinClusterMatrixAttr = "{}.{}".format(skinCls, attribute)

    matrixValues = list()
    for i in range(len(getInfluenceJoints(skinCls))):
        matrixAttr = "{}[{}]".format(skinClusterMatrixAttr, i)
        value = cmds.getAttr(matrixAttr)

        # append the result to a list of matricies
        matrixValues.append(value)

    return matrixValues


def setMatrixConnections(
    skinCluster: str, connectionsList: List[str], attribute: str = "bindPreMatrix"
):
    """
    Set the preBind Matrix connections of a skin cluster

    :param skinCluster: skin cluster to set the pre bind matrix connections on
    :param connectionsList: dictonary of influences and bind pre matrix connections
    :param attribute: attribute to set the matrix connections for
    """
    for i, bindInput in enumerate(connectionsList):
        if bindInput:
            try:
                matrixAttr = "{}.{}[{}]".format(skinCluster, attribute, i)
                connections = (
                    cmds.listConnections(matrixAttr, s=True, d=False, plugs=True)
                    or list()
                )
                if bindInput not in connections:
                    cmds.connectAttr(
                        bindInput, "{}.{}[{}]".format(skinCluster, attribute, i), f=True
                    )
            except RuntimeError:
                pass


def setMatrixValues(
    skinCluster: str, valuesList: List[List[float]], attribute: str = "bindPreMatrx"
):
    """
    Try to set the inital values of all connections for the matrix or bindPreMatrix
    """
    for i, value in enumerate(valuesList):
        try:
            cmds.setAttr("{}.{}[{}]".format(skinCluster, attribute, i), value)
        except RuntimeError:
            pass


def getInfluenceJoints(skinCluster: str):
    """
    Get the influences of a skin cluster

    :param str skinCluster: skinCluster to get influences from
    :return: list of influences for a given skincluster
    """
    if not isinstance(skinCluster, oma.MFnSkinCluster):
        skinCluster = getMfnSkin(skinCluster)

    infPathArray = skinCluster.influenceObjects()
    infuenceNameArray = [
        infPathArray[i].partialPathName() for i in range(len(infPathArray))
    ]

    return infuenceNameArray


def getInfluenceIndex(skinCluster: str, influence: str):
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
    influencePath = general.getDagPath(influence)

    return skinClusterFn.indexForInfluenceObject(influencePath)


def transferSkinCluster(sourceMesh: str, targetMesh: str, targetSkin: str):
    """
    Copy our skinweights for identical meshes. Rather than a typical copy opperation this will rebuild the joint
    matrix connections

    :param sourceMesh: source mesh to copy the skinning from
    :param targetMesh: target mesh to copy the skinning to
    :param targetSkin: target skinCluster to copy the values to
    """
    sourceSkinCluster = getSkinCluster(sourceMesh)

    weights, influenceCount = getWeights(sourceMesh)
    blendedWeights = getBlendWeights(sourceMesh)

    # now we need to store and copy over the influences
    matrixValues = getMatrixValues(sourceMesh, attribute="matrix")
    matrixConnections = getMatrixConnections(sourceMesh, attribute="matrix")

    bpmValues = getMatrixValues(sourceMesh, attribute="bindPreMatrix")
    bpmConnections = getMatrixConnections(sourceMesh, attribute="bindPreMatrix")

    # set the matrix connections
    setMatrixValues(targetSkin, matrixValues, attribute="matrix")
    setMatrixValues(targetSkin, bpmValues, attribute="bindPreMatrix")

    setMatrixConnections(targetSkin, matrixConnections, attribute="matrix")
    setMatrixConnections(targetSkin, bpmConnections, attribute="bindPreMatrix")

    # now copy that over to the new mesh
    setWeights(targetMesh, skincluster=targetSkin, weightDict=weights)
    setBlendWeights(targetMesh, skincluster=targetSkin, weightDict=blendedWeights)

    # copy the skin cluster settings
    attrs = [
        "skinningMethod",
        "dqsSupportNonRigid",
        "normalizeWeights",
        "maxInfluences",
        "maintainMaxInfluences",
    ]
    for attr in attrs:
        value = cmds.getAttr("{}.{}".format(sourceSkinCluster, attr))
        cmds.setAttr("{}.{}".format(targetSkin, attr), value)


def stackSkinCluster(sourceMesh: str, targetMesh: str, skinName: Optional[str] = None):
    """
    Copy and stack the skincluster from the source mesh to the target mesh

    :param sourceMesh: mesh with the skincluster to copy from.
    The source mesh is our authoring mesh and should only have ONE skin cluster
    :param targetMesh: the mesh to copy the skin cluster to. This is the result mesh and can have several skin clusters.
    :param skinName: Optional- give the new skin cluster a name
    """
    sourceSkin = getSkinCluster(sourceMesh)
    allTargetSkins = getAllSkinClusters(targetMesh)

    if len(allTargetSkins):
        targetSkinName = skinName or "stacked__" + sourceSkin
        targetSkin = cmds.deformer(targetMesh, type="skinCluster", n=targetSkinName)[0]
    else:
        # no skins yet-- make sure to use this command
        sourceInfluences = getInfluenceJoints(sourceSkin)
        targetSkinName = skinName or targetMesh + "_skinCluster"
        targetSkin = cmds.skinCluster(
            sourceInfluences, targetMesh, tsb=True, mi=3, dr=4.0, n=targetSkinName
        )[0]

    # set the weight distribution to neighbors
    cmds.setAttr("{}.weightDistribution".format(targetSkin), 1)

    # copy the skinweights and data
    transferSkinCluster(sourceMesh, targetMesh=targetMesh, targetSkin=targetSkin)

    # finally recache the bind matricies
    cmds.skinCluster(targetSkin, e=True, recacheBindMatrices=True)


def copySkinClusterAndInfluences(
    sourceMesh: str,
    targetMeshes: str,
    surfaceMode: str = SurfaceCopyMode.ClosestPoint,
    influenceMode: str = InfluenceCopyMode.ClosestJoint,
    uvSpace: bool = False,
):
    """
    Copy skin cluster and all influences to a target mesh

    :param str sourceMesh: source mesh to copy the skin cluster from
    :param list tuple targetMeshes: target mesh to copy the skin clustes to
    :param str surfaceMode: surface association method for copy skin weights
    :param str influenceMode: influence association to copy the skin weights
    :param bool uvSpace: transfer the skins in UV space. This is great for transfering to a smoothed mesh
    :return:
    """
    targetMeshes = toList(targetMeshes)

    srcSkinCluster = getSkinCluster(sourceMesh)
    srcInfluences = getInfluenceJoints(srcSkinCluster)

    for tgtMesh in targetMeshes:
        tgtSkinCluster = getSkinCluster(tgtMesh)

        # if the target does not have a skin cluster create one with the input joints
        if not tgtSkinCluster:
            skinClusterName = tgtMesh + "_skinCluster"
            tgtSkinCluster = cmds.skinCluster(
                srcInfluences,
                tgtMesh,
                name=skinClusterName,
                toSelectedBones=True,
                bindMethod=BindMethod.ClosestJoint,
                smoothWeights=0,
                normalizeWeights=1,
            )[0]

        # otherwise add the missing influences to the skin cluster.
        else:
            tgtInfluences = getInfluenceJoints(tgtSkinCluster)
            for influence in srcInfluences:
                if influence not in tgtInfluences:
                    cmds.skinCluster(tgtSkinCluster, edit=True, addInfluence=influence)

        # copy the skin cluster settings
        attrs = [
            "skinningMethod",
            "dqsSupportNonRigid",
            "normalizeWeights",
            "maxInfluences",
            "maintainMaxInfluences",
        ]
        for attr in attrs:
            value = cmds.getAttr("{}.{}".format(srcSkinCluster, attr))
            cmds.setAttr("{}.{}".format(tgtSkinCluster, attr), value)

        kwargs = {
            "surfaceAssociation": surfaceMode,
            "influenceAssociation": influenceMode,
        }
        if uvSpace:
            sourceUVSet = cmds.polyUVSet(sourceMesh, q=True, currentUVSet=True)[0]
            DestUvSet = cmds.polyUVSet(tgtMesh, q=True, currentUVSet=True)[0]

            kwargs["uv"] = [sourceUVSet, DestUvSet]

        # copy the skin weights
        cmds.copySkinWeights(
            sourceSkin=srcSkinCluster,
            destinationSkin=tgtSkinCluster,
            normalize=True,
            noMirror=True,
            **kwargs,
        )
        print(
            "weights copied: {}({}) -> {}({})".format(
                sourceMesh, srcSkinCluster, tgtMesh, tgtSkinCluster
            )
        )

        return tgtSkinCluster


def connectExistingBPMs(skinCluster: str, influences: List[str] = None):
    """
    Look for existist bpm nodes and connect them to the appropriate slot of the skincluster.

    you can pass specific influences to connect or connect to all available bmps.

    :param skinCluster: skin cluster to connect the Bpm nodes to
    :param influences: list of influences to connect
    """

    if not influences:
        influences = getInfluenceJoints(skinCluster)

    for influence in influences:
        index = getInfluenceIndex(skinCluster, influence)

        bpmInfluence = influence.replace("bind", "bpm")
        if cmds.objExists(bpmInfluence):
            cmds.connectAttr(
                "{}.worldInverseMatrix".format(bpmInfluence),
                "{}.bindPreMatrix[{}]".format(skinCluster, index),
                f=True,
            )
        else:
            logger.warning("No Bpm exists for {}".format(influence))
