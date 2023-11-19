#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: blendshapeUtils.py
    author: masonsmigel
    date: 10/2022
    description: A bunch of useful utilities for working with blendshapes

"""
from typing import Union, List

import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import blendshape
from rigamajig2.maya import skinCluster
from rigamajig2.shared import common

Multiuse = Union[List[str], str]


def splitBlendshapeTargets(targets: Multiuse, splitMesh: str, splitJoints: Multiuse = None, skinFile: str = None):
    """
    Split blendshapes into sections based on the skinweights of the input joints. This will produce a number
    of blendshapes split into individual targets with weights from the split joints.

    The skin cluster is determined from the splitMesh. All split joints must be a part of that skin cluster.
    Ideally the skincluster should be split between only the split joints, but arbirary weights can be used as well
    (understanding that the resulting blendshape targets will not be normalized)

    Optionally users can pass in a skinFile instead of keeping the skinweights on the splitMesh. This results in a
    more procedural approach.

    The output targets will be named with the split joint as a suffix: (`frown_l`)


    >>> splitBlendshapeTargets(targets=["smile", "frown"], splitMesh="body_geo", splitJoints=["l", "r"])

    :param targets: list of meshes to add as targets. They will be split!
    :param splitJoints: list of joints to use in the split. They must all be bound to the split mesh
    :param splitMesh: the mesh with the split weights painted on it.
    :param skinFile: Skin Weight file to load the weights from. otherwise grab the weights from the splitmesh.
    :return: a list of newly created blendshapeTargets
    """
    outputTargets = list()

    targets = common.toList(targets)
    splitMesh = common.getFirst(splitMesh)
    splitJoints = common.toList(splitJoints)

    if skinFile:
        skinData = skin_data.SkinData()
        skinData.read(skinFile)

        data = skinData.getData()
        skinClusterNode = skinCluster.getSkinCluster(splitMesh)
        skinWeights = data.get(skinClusterNode).get("weights")
        vertexCount = data.get(skinClusterNode).get("vertexCount")

    else:
        skinClusterNode = skinCluster.getSkinCluster(splitMesh)

        if not skinClusterNode:
            raise Exception("Your split mesh ({}) MUST have a skinCluster".format(splitMesh))

        skinWeights, vertexCount = skinCluster.getWeights(splitMesh)

    splitHierarchy = cmds.createNode("transform", name="tmp_split_hrc")

    temporaryBaseMesh = createBaseFromSkinned(splitMesh, parent=splitHierarchy)

    if not splitJoints:
        splitJoints = skinCluster.getInfluenceJoints(skinClusterNode)

    for splitJoint in splitJoints:
        sourceWeights = skinWeights[splitJoint]

        outputWeights = {}
        for i in range(vertexCount):
            value = sourceWeights.get(i) or sourceWeights.get(str(i)) or 0.0
            outputWeights[i] = value

        # now put them into a dictionary
        blendshapeDict = dict()
        blendshapeDict["baseWeights"] = outputWeights

        blendshapeNode = blendshape.create(temporaryBaseMesh, targets=targets, origin="local")
        blendshape.setWeights(blendshapeNode, weights=blendshapeDict, targets=["baseWeights"])

        targetsList = blendshape.getTargetList(blendshapeNode)

        for target in targetsList:
            # turn the blendshape ON
            cmds.setAttr("{}.{}".format(blendshapeNode, target), 1)

            # now create a duplicate, this will be the skinned version
            targetName = "{}_{}".format(target, splitJoint)
            dup = cmds.duplicate(temporaryBaseMesh)
            cmds.rename(dup, targetName)

            outputTargets.append(targetName)

            # turn the blendshape OFF
            cmds.setAttr("{}.{}".format(blendshapeNode, target), 0)

    # now we can delete the split mesh
    cmds.delete(temporaryBaseMesh)

    return outputTargets


def createBaseFromSkinned(mesh, parent=None):
    """
    Create a non-skinned blendshape base from a skinned mesh.

    used to create a base from the splitMesh.
    :param parent:
    :param mesh: Mesh to create a blendshape base from.
    :return: base_mesh
    """
    skinClusterNode = skinCluster.getSkinCluster(mesh)

    if skinClusterNode:
        cmds.setAttr("{}.envelope".format(skinClusterNode), 0)
    dup = cmds.duplicate(mesh)
    if skinClusterNode:
        cmds.setAttr("{}.envelope".format(skinClusterNode), 1)

    base = "{}_split_base".format(mesh)
    cmds.rename(dup, base)
    attr.unlock(base, attr.TRANSFORMS)
    cmds.parent(base, parent)

    return base
