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

# MAYA
import maya.cmds as cmds

# RIGAMJIG2
from rigamajig2.shared import common
from rigamajig2.maya import mesh
from rigamajig2.maya import deformer
from rigamajig2.maya import meta
from rigamajig2.maya import attr
from rigamajig2.maya import blendshape

LAYER_HRC = 'deformLayers'

LAYER_ATTR = 'deformationLayers'

MAIN_NODE_NAME = 'main'

CONNECTION_METHOD_LIST = ['bshp', 'inmesh', 'skin']

DUMMY_JOINT = 'world_dummy_bind'


class DeformLayer(object):
    """
    This class is a manager for deformation layers.
    We will use defomation layers to setup stacking deformations.

    This class will be used for adding, retreiving or optimizing deformation layers.

    Connections to deformationlayers will be stored through a message array on the source mesh.
    """

    def __init__(self, model):
        """
        Constructor fot the defomation Layer class object
        :param mesh: source mesh for working with defomation layers on. This will be the final output mesh.
                    Deformation layers will be added BEFORE this mesh.
        """

        if not mesh.isMesh(model):
            raise Exception("{} is not a mesh. Please provide a valid mesh to use deform layers.".format(model))

        self.model = model
        self.deformShape = deformer.getDeformShape(self.model)

        self._intialzeLayersSetup()

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

    def createDeformLayer(self, suffix=None, connectionMethod='bshp'):
        """
        Create a  new deformation Layer
        :param suffix: optional name to add to the deformation layer mesh name.
        :param connectionMethod: method to connect to the next blendshape.
                                 valid Values are 'bshp', 'inmesh', and 'skin'.

                                 'bshp' - add a world shape blendshape connection
                                 'inmesh' - connect the outmesh of the source to the targets inmesh attrs
                                 'skin' - bake this into a stacked skin cluster.

                                 For now this will all be
                                 handled with a blendshape however at the self.bake step this can be baked into an
                                 optimized setup.
        :return:
        """
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

        if suffix:
            meshDup = "d{index}_{model}_{suffix}".format(index=index, model=self.model, suffix=suffix)
        else:
            meshDup = "d{index}_{model}".format(index=index, model=self.model)

        # create the duplicate mesh
        tmpDup = cmds.duplicate(self.model)
        cmds.rename(tmpDup, meshDup)
        cmds.parent(meshDup, deformLayerName)

        # cleanup the new mesh
        mesh.cleanShapes(meshDup)
        attr.unlock(meshDup, attr.TRANSFORMS)
        if cmds.objExists("{}.{}".format(meshDup, LAYER_ATTR)):
            cmds.deleteAttr("{}.{}".format(meshDup, LAYER_ATTR))

        # setup connections from the model to the layer
        meta.addMessageListConnection(self.model, [meshDup], LAYER_ATTR, "DeformationLayer")

        # add additional metadata
        attr.createAttr(meshDup, longName='suffix', attributeType='string', value=suffix, locked=True)

        # add the connection method to the target
        if connectionMethod not in CONNECTION_METHOD_LIST:
            raise KeyError(
                "{} is not a valid connection type. Please use {}".format(connectionMethod, CONNECTION_METHOD_LIST))

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

    def getDeformationLayers(self):
        """ return the names of all the deformation layers on a given model"""

        layers = meta.getMessageConnection("{}.{}".format(self.model, LAYER_ATTR))
        return sorted(common.toList(layers)) if layers else None

    def getNumberOfDeformationLayers(self):
        """ return the number of deformation layers on a given node"""
        # get the index of the layer
        if cmds.objExists("{}.{}".format(self.model, LAYER_ATTR)):

            mPlug = attr._getPlug("{}.{}".format(self.model, LAYER_ATTR))
            numberLayers = mPlug.evaluateNumElements()

        else:
            numberLayers = 0

        return numberLayers

    def deleteDeformationLayer(self, layerIndex):
        """ delete a deformation layer at the given index"""
        pass

    def connectToModel(self):
        """
        Connect the layer hierarchy back to the model.
        This must be dont after all layers are added so ensure proper deformation layering.
        :return:
        """

        if not self.getNumberOfDeformationLayers() > 0:
            raise Exception("No deformation layers to connect back to render model")

        layers = self.getDeformationLayers()
        lastLayer = layers[-1]

        blendshapeName = "d_out_{}".format(self.model)
        blendshapeNode = blendshape.create(base=self.model, targets=None, name=blendshapeName)

        blendshape.addTarget(blendshape=blendshapeNode, target=lastLayer, targetWeight=1.0)
        # force the blendshape node to be on the bottom of the deformer stack
        deformer.reorderToBottom(self.model, blendshapeNode)

        # finally hide all the previous layers

        for layer in layers:
            cmds.setAttr("{}.v".format(layer), 0)




