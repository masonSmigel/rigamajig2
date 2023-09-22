#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: deformLayer.py
    author: masonsmigel
    date: 09/2022
    discription: This module contains a class to manage and setup deformation layers

"""
# PYTHON
from collections import OrderedDict
import logging

# MAYA
import maya.cmds as cmds

# RIGAMJIG2
from rigamajig2.shared import common
from rigamajig2.maya import mesh
from rigamajig2.maya import deformer
from rigamajig2.maya import meta
from rigamajig2.maya import attr
from rigamajig2.maya import joint
from rigamajig2.maya import blendshape
from rigamajig2.maya import skinCluster

LAYER_HRC = 'deformLayers'
LAYERS_ATTR = 'deformationLayers'
LAYER_ATTR = 'deformationLayer'
LAYER_GROUP_ATTR = "deformLayerGroup"

MAIN_NODE_NAME = 'main'

DEFORM_LAYER_BSHP_TAG = "deformLayerBshp"

CONNECTION_METHOD_LIST = ['bshp', 'inmesh']

DUMMY_JOINT = 'world_dummy_bind'

logger = logging.getLogger(__name__)


def _safeSetVisablity(node, value):
    """
    Utility to safely set the visability of a node since alot of places rely on this we want to avoid raising an exeption.
    :param node: node to set the visability on
    :param value: value to set the visabily to.
    :return:
    """
    try:
        cmds.setAttr("{}.v".format(node), value)
    except:
        pass


def transferAllDeformerTypes(deformerName, sourceGeo, targetGeo, override=False):
    """
   Transfer a deformer of any tupe to another geometry

   :param deformerName: name of the deformer to transfer
   :param str sourceGeo: name of the geometry copy from
   :param str targetGeo: name of the geometry to transfer to
   :param bool override: If True override the existing skin cluster
   :return: name of the transfered deformer
   """

    if deformerName not in deformer.getDeformerStack(sourceGeo):
        raise ValueError(f"'{deformerName}' is not part of the deformer stack for {sourceGeo}")

    if blendshape.isBlendshape(deformerName):
        layerId = targetGeo.split("_")[0]
        newDeformer = blendshape.transferBlendshape(
            blendshape=deformerName,
            targetMesh=targetGeo,
            blendshapeName=f"{deformerName}",
            copyConnections=True,
            deformOrder="before")  # We will need to apply the blendshape before the skin cluster to avoid bad deformation stacking.

        cmds.delete(deformerName)
        cmds.rename(newDeformer, deformerName)
        newDeformer = deformerName

    elif skinCluster.isSkinCluster(deformerName):
        if skinCluster.getSkinCluster(targetGeo) and not override:
            logger.warning(f"{deformerName} was not transfered because it would override the skincluster")
            return None
        newDeformer = skinCluster.copySkinClusterAndInfluences(sourceMesh=sourceGeo, targetMeshes=targetGeo)
        cmds.skinCluster(deformerName, e=True, unbind=True, unbindKeepHistory=False)

    elif deformer.isDeformer(deformerName):
        newDeformer = deformer.transferDeformer(deformer=deformerName, sourceMesh=sourceGeo, targetMesh=targetGeo)
        deformer.removeGeoFromDeformer(deformerName, geo=sourceGeo)

    else:
        logger.warning(f"{deformer_} is not stackable.")
        return None
    return newDeformer


def getRenderModelFromLayer(mesh):
    """
    Get a render model from the given mesh if is a rendermesh layer.
    :param mesh: name of deform layer mesh
    :return:
    """
    if not cmds.objExists(mesh):
        raise RuntimeError(f"Mesh with the name {mesh} does not exist in the scene")

    if cmds.objExists(f"{mesh}.{LAYERS_ATTR}"):
        return mesh

    if not cmds.objExists(f"{mesh}.{LAYER_ATTR}"):
        return None

    return meta.getMessageConnection(f"{mesh}.{LAYER_ATTR}")


def getLayerGroups():
    """
    get a list of all layer groups in a scene
    :return: return a list of layer groups in the scene
    """
    meshWithDeformLayers = meta.getTagged("hasDeformLayers")

    layerGroupsList = set()
    for mesh in meshWithDeformLayers:
        # get the layer group
        deformLayerObj = DeformLayer(mesh)
        layerGroup = deformLayerObj.getDeformLayerGroup()

        layerGroupsList.add(layerGroup)
    return list(layerGroupsList)


class DeformLayer(object):
    """
    This class is a manager for deformation layers.
    We will use defomation layers to setup stacking deformations.

    This class will be used for adding, retreiving or optimizing deformation layers.

    Connections to deformationlayers will be stored through a message array on the source mesh.
    """

    def __init__(self, model, layerGroup=None):
        """
        Constructor for the defomation Layer class object
        :param mesh: source mesh for working with defomation layers on. This will be the final output mesh.
                    Deformation layers will be added BEFORE this mesh.
        """

        if not mesh.isMesh(model):
            raise Exception("{} is not a mesh. Please provide a valid mesh to use deform layers.".format(model))

        self.model = model
        self.deformShape = deformer.getDeformShape(self.model)

        # tag the model as one that has deformation layers
        meta.tag(self.model, tag='hasDeformLayers')

        # all layers MUST belong to a layer group, so if one is not assigned, assign it to "main"

        if not cmds.objExists(f"{self.model}.{LAYER_GROUP_ATTR}"):
            layerGroup = layerGroup or "main"
            attr.createAttr(self.model, longName=LAYER_GROUP_ATTR, attributeType="string", value=layerGroup)
            attr.lock(self.model, attrs=LAYER_GROUP_ATTR)

    def _intialzeLayersSetup(self):
        """
        setup the required dag hierarchy for the deformation layer setup
        :return:
        """

        # build the main layer setup
        if not cmds.objExists(LAYER_HRC):
            cmds.createNode("transform", name=LAYER_HRC)
            attr.lock(LAYER_HRC, attr.TRANSFORMS)

            # if we have a main setup build parent the layers under the main component
            if cmds.objExists(MAIN_NODE_NAME):
                cmds.parent(LAYER_HRC, MAIN_NODE_NAME)

    def setDeformLayerGroup(self, layerGroup):
        """
        set the deform layer group.
        :param layerGroup: name of the layer group to set.
        :return:
        """

        attr.unlock(self.model, attrs=LAYER_GROUP_ATTR)
        attr.setPlugValue(f"{self.model}.{LAYER_GROUP_ATTR}", layerGroup)
        attr.lock(self.model, attrs=LAYER_GROUP_ATTR)

    def getDeformLayerGroup(self):
        """Get the name of the deform layer group"""
        if cmds.objExists(f"{self.model}.{LAYER_GROUP_ATTR}"):
            return cmds.getAttr(f"{self.model}.{LAYER_GROUP_ATTR}")
        return None

    def createDeformLayer(self, suffix=None, connectionMethod='bshp'):
        """
        Create a  new deformation Layer
        :param suffix: optional name to add to the deformation layer mesh name.
        :param connectionMethod: method to connect to the next blendshape.
                                 valid Values are 'bshp', 'inmesh'

                                 'bshp' - add a world shape blendshape connection
                                 'inmesh' - connect the outmesh of the source to the targets inmesh attrs

                                 For now this will all be
                                 handled with a blendshape however at the self.bake step this can be baked into an
                                 optimized setup.
        :return:
        """
        self._intialzeLayersSetup()

        index = self.getNumberOfDeformationLayers()

        deformLayerName = "deformLayer_{}".format(index)
        # create a group for each layer with a dummy joint
        if not cmds.objExists(deformLayerName):
            cmds.createNode("transform", name=deformLayerName)
            attr.lock(deformLayerName, attr.TRANSFORMS)
            cmds.parent(deformLayerName, LAYER_HRC)

            # create a dummy joint
            dummyJoint = "d{}_dummy_bind".format(index)
            cmds.createNode("joint", name=dummyJoint)
            cmds.parent(dummyJoint, deformLayerName)

            # create a dummy_bpm
            bpmJoint = "d{}_dummy_bpm".format(index)
            cmds.createNode("joint", name=bpmJoint)
            cmds.parent(bpmJoint, deformLayerName)

            joint.hideJoints([dummyJoint, bpmJoint])

        if suffix:
            meshDup = "d{index}_{model}_{suffix}".format(index=index, model=self.model, suffix=suffix)
        else:
            meshDup = "d{index}_{model}".format(index=index, model=self.model)

        # create the duplicate mesh
        tmpDup = cmds.duplicate(self.model)
        cmds.rename(tmpDup, meshDup)
        cmds.parent(meshDup, deformLayerName)
        meta.untag(meshDup, tag='hasDeformLayers')
        if cmds.objExists(f"{meshDup}.{LAYER_GROUP_ATTR}"):
            attr.unlock(meshDup, attrs=LAYER_GROUP_ATTR)
            cmds.deleteAttr(meshDup, attribute=LAYER_GROUP_ATTR)

        # rename the shapes
        shape = deformer.getDeformShape(meshDup)
        cmds.rename(shape, "{}Shape".format(meshDup))

        # hide the model.
        _safeSetVisablity(self.model, 0)
        cmds.setAttr("{}.v".format(meshDup), 1)

        # cleanup the new mesh
        mesh.cleanShapes(meshDup)
        attr.unlock(meshDup, attr.TRANSFORMS)
        if cmds.objExists("{}.{}".format(meshDup, LAYERS_ATTR)):
            cmds.deleteAttr("{}.{}".format(meshDup, LAYERS_ATTR))

        # setup connections from the model to the layer
        meta.addMessageListConnection(self.model, [meshDup], LAYERS_ATTR, LAYER_ATTR)

        # add additional metadata
        attr.createAttr(meshDup, longName='suffix', attributeType='string', value=suffix, locked=True)

        # add the connection method to the target
        if connectionMethod not in CONNECTION_METHOD_LIST:
            raise KeyError(
                "{} is not a valid connection type. Use: {}".format(connectionMethod, CONNECTION_METHOD_LIST))

        defaultConnectionMethod = CONNECTION_METHOD_LIST.index(connectionMethod)
        attr.createEnum(meshDup, longName='connectionMethod', enum=CONNECTION_METHOD_LIST,
                        value=defaultConnectionMethod)

        # connect the previous layer to the new layer
        # we can assume the layer before this is the source
        if self.getNumberOfDeformationLayers() > 1:
            previousLayer = self.getDeformationLayers()[-2]
            blendshapeName = "d{}_{}_layer".format(index, self.model)
            blendshapeNode = blendshape.create(base=meshDup, targets=None, name=blendshapeName)

            blendshape.addTarget(blendshape=blendshapeNode, target=previousLayer, targetWeight=1.0)

            # add a tag to makr the blendshape as NOT part of the deformation chain.
            meta.tag(blendshapeNode, tag=DEFORM_LAYER_BSHP_TAG)
            # hide the previous layer
            cmds.setAttr("{}.v".format(previousLayer), 0)

    def getDeformationLayers(self):
        """ return the names of all the deformation layers on a given model"""

        layers = meta.getMessageConnection("{}.{}".format(self.model, LAYERS_ATTR))
        return sorted(common.toList(layers)) if layers else None

    def getNumberOfDeformationLayers(self):
        """ return the number of deformation layers on a given node"""
        # get the index of the layer
        if cmds.objExists("{}.{}".format(self.model, LAYERS_ATTR)):

            mPlug = attr._getPlug("{}.{}".format(self.model, LAYERS_ATTR))
            numberLayers = mPlug.evaluateNumElements()

        else:
            numberLayers = 0

        return numberLayers

    def deleteDeformationLayer(self, layerIndex):
        """ delete a deformation layer at the given index"""
        raise NotImplementedError("Deleting deform layers has not yet been implemented")

    def setLayerVisability(self, value, layerIndex):
        """Set the current layer to be visable and the other to be hidden"""
        deformLayerMeshes = self.getDeformationLayers()

        for i, deformLayerMesh in enumerate(deformLayerMeshes):

            cmds.setAttr(f"{deformLayerMesh}.v", False)
            if value and i == layerIndex:
                cmds.setAttr(f"{deformLayerMesh}.v", True)

    def stackDeformLayers(self, cleanup=False):
        """
        Connect the layer hierarchy back to the original model by stacking the skinclusters
        :param cleanup: delete deformation layers after stacking them
        :return:
        """

        if not self.getNumberOfDeformationLayers() > 0:
            cmds.warning("No deformation layers to connect back to render model")
            return

        layers = self.getDeformationLayers()
        deformerCount = 0
        for layer in layers:
            # get a list of all deformers on a layer
            deformerStack = deformer.getDeformerStack(layer)

            # we need to reverse the deformer stack to transfer it. That way we can copy from the bottom
            # to the top as we transfer
            deformerStack.reverse()

            for deformer_ in deformerStack:
                if blendshape.isBlendshape(deformer_):
                    # if the blendshape is the input blendshape from the previous layer, Skip it.
                    if meta.hasTag(deformer_, DEFORM_LAYER_BSHP_TAG):
                        continue
                    layerId = layer.split("_")[0]
                    blendshapeName = f"stacked__{layerId}_{deformer_}"
                    blendshape.transferBlendshape(
                        blendshape=deformer_,
                        targetMesh=self.model,
                        blendshapeName=blendshapeName,
                        copyConnections=True,
                        deformOrder="after")
                elif skinCluster.isSkinCluster(deformer_):
                    skinCluster.stackSkinCluster(layer, self.model, skinName=f"stacked__{layer}_skinCluster")
                elif deformer.isDeformer(deformer_):
                    deformer.transferDeformer(deformer=deformer_, sourceMesh=layer, targetMesh=self.model)
                else:
                    logger.warning(f"{deformer_} is not stackable.")
                    continue
                # if the deformer was transfered increase the deformer count
                deformerCount += 1

            cmds.setAttr("{}.v".format(layer), 0)

        # Use a try exept block just incase the render mesh is connected to something.
        _safeSetVisablity(self.model, 1)

        # send out a message that the stack was sucessful
        logger.info(
            f"deform layers succesfully stacked '{self.model}' ({len(layers)} layers, {deformerCount} deformers)")

        # if we want to cleanup delete the deformation layers after stacking the skinClusters
        if cleanup:
            # delete all the deformation layers
            cmds.delete(layers)

    def transferDeformer(self, deformerName, sourceLayer, targetLayer, override=True):
        """
        Transfer a deformer to the geometry on the target layer index

        :param deformerName: name of the deformer to transfer
        :param int str sourceLayer: name of the geometry or index in the deform layers stack to copy from
        :param int str targetLayer: name of the geometry or index in the deform layers stack to transfer to
        :return: name of the transfered deformer
        """

        if isinstance(sourceLayer, int):
            sourceLayer = self.getDeformationLayers()[sourceLayer]
        if isinstance(targetLayer, int):
            targetLayer = self.getDeformationLayers()[targetLayer]

        transferAllDeformerTypes(deformerName, sourceLayer, targetLayer, override)
