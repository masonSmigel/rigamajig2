#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: actorize.py.py
    author: masonsmigel
    date: 02/2023
    discription: This module contains functions to actorize a rig. This includes making an actor-anim and an actor-ue

"""
from collections import OrderedDict

import maya.cmds as cmds

from rigamajig2.maya import blendshape
from rigamajig2.maya import deformer
from rigamajig2.maya import mesh
from rigamajig2.maya import meta
from rigamajig2.maya import shape
from rigamajig2.maya import skinCluster
from rigamajig2.maya import uv

SOURCE_SUFFIX = "__src"

POLYSMOOTH_KWARGS = OrderedDict(method=0, divisions=1, keepHardEdge=False, propagateEdgeHardness=False,ch=False, ofb=0)


def createNewGeometry():
    """
    Get the model node from the scene and create a duplicate
    :return:
    """

    modelRoot = meta.getTagged("model_root")
    modelRootDup = cmds.duplicate(modelRoot)

    # process the original model. This inlcudes: renaming nodes and deformers.
    meshNodes = cmds.listRelatives(modelRoot, ad=True, path=True, type="transform") + modelRoot

    for meshNode in meshNodes:
        nodeName = meshNode.split("|")[-1]
        newNodeName = "{}{}".format(nodeName, SOURCE_SUFFIX)
        cmds.rename(meshNode, newNodeName)

        # look for meshes, and if we find one we should also rename the deformers.
        if mesh.isMesh(newNodeName):
            deformers = deformer.getDeformerStack(newNodeName)
            for nodeDeformer in deformers:
                if SOURCE_SUFFIX not in nodeDeformer:
                    newDeformerName = "{}{}".format(nodeDeformer, SOURCE_SUFFIX)
                    cmds.rename(nodeDeformer, newDeformerName)

    # process the duplicate model, This includes smoothing it and running a clean shapes opperation on it.

    for newModel in modelRootDup:
        if mesh.isMesh(newModel):
            # first lets cleanup the shape nodes
            mesh.cleanShapes(newModel)

            # now we can run the poly smooth opperation
            cmds.polySmooth(newModel, **POLYSMOOTH_KWARGS)

            # delete the history
            cmds.delete(newModel, ch=True)

            # poly smooth will select the geo so we need to clear out selection
            cmds.select(clear=True)

            # get the source model if it exists (which it always should) and create a message connection to use later
            srcModel = "{}{}".format(newModel, SOURCE_SUFFIX)
            if not cmds.objExists(srcModel):
                cmds.warning("The model {} does not have a valid source. ".format(modelNode))
                continue
            meta.createMessageConnection(newModel, srcModel, "sourceModel")

    # the first node of the modelDupRoot will get renamed, so lets set the name to the name of the old one.
    cmds.rename(modelRootDup[0], modelRoot[0])

    return modelRoot[0]


def copyDeformations(modelRootDup):
    """
    Copy the deformations from the source to desination model

    :param modelRootDup:
    :return:
    """

    modelsToTransfer = list()
    dstModels = cmds.listRelatives(modelRootDup, ad=True, path=True, type="transform")
    for destModel in dstModels:
        # try to grab the mesh name
        if mesh.isMesh(destModel):
            sourceModel = meta.getMessageConnection("{}.{}".format(destModel, "sourceModel"))

            modelsToTransfer.append([destModel, sourceModel])

    # now lets copy the deformations
    for destModel, sourceModel in modelsToTransfer:

        deformerStack = deformer.getDeformerStack(sourceModel)

        # provide a warning about any deformers that wont be transfered.
        for sourceDeformer in deformerStack:
            if not skinCluster.isSkinCluster(sourceDeformer) and not blendshape.isBlendshape(sourceDeformer):
                deformerType = cmds.nodeType(sourceDeformer)

        # reverse the deformer stack so we start on the bottom and work up. THis will preserve the order of the source.
        deformerStack = reversed(deformerStack)
        # loop through the other deformers and transfer them.
        for sourceDeformer in deformerStack:

            if skinCluster.isSkinCluster(sourceDeformer):
                transferSkinCluster(sourceModel=sourceModel, sourceDeformer=sourceDeformer, destModel=destModel)

            # transfer blendshapes
            if blendshape.isBlendshape(sourceDeformer):
                # Some blendshapes may be driven by another blendshape. Theese driver shapes also show up in the deformer stack.
                # to avoid this we need to make sure the source deformer actully drives the geo of the source model.
                affectedGeo = blendshape.getBaseGeometry(sourceDeformer)
                if affectedGeo not in shape.getShapes(sourceModel):
                    continue

                # now we can transfer the blendshape!
                transferBlendshape(sourceModel=sourceModel, sourceDeformer=sourceDeformer, destModel=destModel)


def finalizeActor():
    """
    Finalize the acotr by deleting uneeded stuff
    :return:
    """
    sourceNodes = cmds.ls("*{}".format(SOURCE_SUFFIX))
    cmds.delete(sourceNodes)


def transferSkinCluster(sourceModel, sourceDeformer, destModel):
    """
    transfer the skin cluster to the higher resolution mesh
    """
    # start with the skin cluster. first we need to check if it has overlapping UVS.
    # It will be faster to check the  source and the two have identical layouts.
    if uv.checkIfOverlapping(sourceModel):
        skinCluster.copySkinClusterAndInfluences(sourceModel, destModel, uvSpace=False)
    else:
        skinCluster.copySkinClusterAndInfluences(sourceModel, destModel, uvSpace=True)


def transferBlendshape(sourceModel, sourceDeformer, destModel):
    """
    Transfer a blendshape node to the higer resolution parent
    """

    # first lets smooth the high res model. need to use the same arguments as before. But this time we'll turn on history
    smooth_kwargs = POLYSMOOTH_KWARGS
    smooth_kwargs['ch'] = True

    tmpSmoothNode = cmds.polySmooth(sourceModel, **smooth_kwargs)

    # now lets create a new blendshape target
    deformerName = sourceDeformer.split(SOURCE_SUFFIX)[0]
    destDeformer = blendshape.create(destModel, name=deformerName)

    # start transfering the blendshapes
    sourceTargets = blendshape.getTargetList(sourceDeformer)
    targetInfoDict = OrderedDict()

    # first we need to gather information about each target, disconnect any input connections and set them all to 0
    for target in sourceTargets:
        # first lets set the target value to 1
        targetPlug = "{}.{}".format(sourceDeformer, target)

        # get the defaults
        defaultValue = cmds.getAttr(targetPlug)
        innConnections = cmds.listConnections(targetPlug, source=True, d=False, plugs=True)
        outConnections = cmds.listConnections(targetPlug, source=False, destination=True, plugs=True) or []

        targetInfoDict[target] = {'value': defaultValue,
                                  'innConnections': innConnections,
                                  'outConnections': outConnections
                                  }

        # break the connetion and set the target to 0
        if innConnections:
            cmds.disconnectAttr(innConnections[0], targetPlug)
        cmds.setAttr(targetPlug, 0)

    # next we can extract smoothed versions of each blendshape by individually turning them all on
    # now we can turn on each target and create a duplicate
    for target in sourceTargets:
        targetPlug = "{}.{}".format(sourceDeformer, target)
        cmds.setAttr(targetPlug, 1)
        targetGeo = cmds.duplicate(sourceModel, name=target)[0]
        cmds.setAttr(targetPlug, 0)

        # add the target to the destination deformer
        blendshape.addTarget(destDeformer, target=targetGeo)
        cmds.delete(targetGeo)

    # finally we can re-connect the input and output connections
    for target in list(targetInfoDict.keys()):
        destTargetPlug = "{}.{}".format(destDeformer, target)
        # apply the info back to the destination deformer
        value = targetInfoDict[target]['value']
        innConnection = targetInfoDict[target]['innConnections']
        outConnections = targetInfoDict[target]['outConnections']

        cmds.setAttr(destTargetPlug, value)

        # reconnect the input connections
        if innConnection:
            cmds.connectAttr(innConnection[0], destTargetPlug)

        # reconnect the output connections
        for outConnection in outConnections:
            cmds.connectAttr(destTargetPlug, outConnection, f=True)

    # finally lets delete the smooth node and add a log
    cmds.delete(tmpSmoothNode)


if __name__ == '__main__':
    createNewGeometry()
    copyDeformations('geo_all')
