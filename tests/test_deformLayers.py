#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_deform_layers.py.py
    author: masonsmigel
    date: 09/2023
    discription: 

"""

import maya.cmds as cmds
import pytest

from rigamajig2.maya import blendshape
from rigamajig2.maya import deformer
from rigamajig2.maya.data import deformLayerData
from rigamajig2.maya.rig import deformLayer
from rigamajig2.shared.pytestUtils import getTempFilePath

EXPECTED_LAYERS = ["d0_pSphere1_layer01", "d1_pSphere1_layer02", "d2_pSphere1_layer03"]
EXPECTED_BLENDSHAPE_TARGETS = ["target01", "target02", "target03"]


@pytest.fixture()
def layerDataFile(tmp_path):
    return getTempFilePath(tmp_path, filename="deformLayerData.json")


def setupScene():
    """Setup the initial scene"""
    cmds.file(newFile=True, force=True)
    sphere = cmds.polySphere()[0]
    cmds.delete(sphere, constructionHistory=True)

    # create a joint
    joint = cmds.createNode("joint")

    cmds.skinCluster(joint, sphere, name="pSphere1_skinCluster")

    # create a delta mush
    cmds.deltaMush("pSphere1", name="pSphere1_deltaMush")

    # create a blendshape
    blendshapeNode = blendshape.create(sphere)
    blendshape.addEmptyTarget(blendshapeNode, "target01")
    blendshape.addEmptyTarget(blendshapeNode, "target02")
    blendshape.addEmptyTarget(blendshapeNode, "target03")

    return sphere


@pytest.fixture()
def setupDeformLayers(layerDataFile):
    """Setup the deformation layers"""
    sphere = setupScene()

    sphereDeformLayers = deformLayer.DeformLayer(sphere)
    sphereDeformLayers.createDeformLayer("layer01")
    sphereDeformLayers.createDeformLayer("layer02")
    sphereDeformLayers.createDeformLayer("layer03")

    layerDataObj = deformLayerData.DeformLayerData()
    layerDataObj.gatherData(sphere)
    layerDataObj.write(layerDataFile)

    return sphere, layerDataFile


def test_addDeformationLayers(setupDeformLayers):
    """Test to see if we can add deformation layers"""
    sphere, layerDataFile = setupDeformLayers
    sphereDeformLayers = deformLayer.DeformLayer(sphere)
    assert sphereDeformLayers.getDeformationLayers() == EXPECTED_LAYERS


def test_exportLayerData(setupDeformLayers):
    """Ensure the deform layer data can be exported"""

    sphere, layerDataFile = setupDeformLayers

    layerDataObj = deformLayerData.DeformLayerData()
    layerDataObj.gatherData(sphere)
    data = layerDataObj.getData()

    # check to see if there are 5 keys in the layerData ('dagPath', 'deformLayerGroup' plus 3 deformationLayers)
    assert len(data[sphere].keys()) == 5


def test_importDeformLayerData(setupDeformLayers):
    """Make sure the deform layer data can be imported"""
    sphere, layerDataFile = setupDeformLayers
    cmds.file(newFile=True, force=True)

    # re setup the scene to  test importing the deformLayers
    setupScene()

    layerDataObj = deformLayerData.DeformLayerData()
    layerDataObj.read(layerDataFile)

    layerDataObj.applyAllData()

    assert cmds.objExists("d0_pSphere1_layer01")
    assert cmds.objExists("d1_pSphere1_layer02")
    assert cmds.objExists("d2_pSphere1_layer03")


def test_transferDeformers(setupDeformLayers):
    """Ensure that deformers can be transferred"""

    test_importDeformLayerData(setupDeformLayers)

    newBlendshape = deformLayer.transferAllDeformerTypes(
        deformerName="pSphere1_bshp", sourceGeo="pSphere1", targetGeo="d2_pSphere1_layer03"
    )
    newSkincluster = deformLayer.transferAllDeformerTypes(
        deformerName="pSphere1_skinCluster", sourceGeo="pSphere1", targetGeo="d2_pSphere1_layer03"
    )
    newDeltaMush = deformLayer.transferAllDeformerTypes(
        deformerName="pSphere1_deltaMush", sourceGeo="pSphere1", targetGeo="d2_pSphere1_layer03"
    )

    deformerStack = deformer.getDeformerStack("d2_pSphere1_layer03")

    # check to see if there are 4 deformers in the deformerStack (3 deformers plus deformLayer input blendhape)
    assert len(deformerStack) == 4

    # check to see if all blendshapes were transferred
    assert blendshape.getTargetList(newBlendshape) == EXPECTED_BLENDSHAPE_TARGETS
