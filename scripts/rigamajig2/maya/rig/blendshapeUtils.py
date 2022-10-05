#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: blendshapeUtils.py
    author: masonsmigel
    date: 10/2022
    discription: A bunch of usefull utilities for working with blendshapes

"""
import maya.cmds as cmds

from rigamajig2.shared import common

from rigamajig2.maya import skinCluster
from rigamajig2.maya import blendshape
from rigamajig2.maya import attr
from rigamajig2.maya import shape


def createSplitBlendshapes(targets, splitJoints, splitMesh, base=None):
    """
    Create a collection of blendshapes split based on various input joints.
    This function will create new blendshape targets based on the influence weight of the provided skin cluster.

    You must first paint a split map on a mesh using ONLY joints you wish to use as split influences.

    :param targets: list of meshes to add as targets. They will be split!
    :param splitJoints: list of joints to use in the split. They must all be bound to the split mesh
    :param splitMesh: the mesh with the split weights painted on it.
    :param base: the base mesh to use as to create the splits
    :return: a list of newly created blendshapeTargets
    """
    outputTargets = list()

    targets = common.toList(targets)
    splitJoints = common.toList(splitJoints)
    splitMesh = common.getFirstIndex(splitMesh)

    skinClusterNode = skinCluster.getSkinCluster(splitMesh)

    if not skinClusterNode:
        raise Exception("Your split mesh ({}) MUST have a skinCluster".format(splitMesh))

    skinWeights, vertexCount = skinCluster.getWeights(splitMesh)

    # create a temp group to put everything in
    split_hrc = cmds.createNode("transform", name="tmp_split_hrc")

    # now we will create a tempory duplicate of the base mesh to use as the blendshape base
    bshpSplitMesh = createBaseFromSkinned(splitMesh, parent=split_hrc)

    for splitJoint in splitJoints:
        # create a new dictionary to use to set the baseWeights of our new blendshape
        # frist lets get a list of all the influence weights
        sourceWeights = skinWeights[splitJoint]

        outputWeightList = list()
        for i in range(vertexCount):
            value = sourceWeights.get(i) or sourceWeights.get(str(i)) or 0.0
            outputWeightList.insert(i, value)

        # now put them into a dictionary
        blendshapeDict = dict()
        blendshapeDict['baseWeights'] = outputWeightList

        blendshapeNode = blendshape.create(bshpSplitMesh, targets=targets, origin='local')
        blendshape.setWeights(blendshapeNode, weights=blendshapeDict, targets=['baseWeights'])

        bshpTargetsList = blendshape.getTargetList(blendshapeNode)

        for target in bshpTargetsList:
            # turn the blendshape ON
            cmds.setAttr("{}.{}".format(blendshapeNode, target), 1)

            # now create a duplicate, this will be the skinned version
            targetName = "{}_{}".format(target, splitJoint)
            dup = cmds.duplicate(bshpSplitMesh)
            cmds.rename(dup, targetName)

            outputTargets.append(targetName)

            # turn the blendshape OFF
            cmds.setAttr("{}.{}".format(blendshapeNode, target), 0)

    # now we can delete the split mesh
    cmds.delete(bshpSplitMesh)

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

    if skinClusterNode:  cmds.setAttr("{}.envelope".format(skinClusterNode), 0)
    dup = cmds.duplicate(mesh)
    if skinClusterNode:  cmds.setAttr("{}.envelope".format(skinClusterNode), 1)

    base = "{}_split_base".format(mesh)
    cmds.rename(dup, base)
    attr.unlock(base, attr.TRANSFORMS)
    cmds.parent(base, parent)

    return base
