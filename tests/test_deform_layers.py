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
from rigamajig2.maya.test.mayaunittest import TestCase

import rigamajig2.maya.blendshape as blendshape
import rigamajig2.maya.data.deformLayerData as deformLayer_data
import rigamajig2.maya.deformer as deformer
import rigamajig2.maya.rig.deformLayer as deformLayer


class TestDeformLayers(TestCase):
    EXPECTED_LAYERS = ['d0_pSphere1_layer01', 'd1_pSphere1_layer02', 'd2_pSphere1_layer03']
    EXPECTED_BLENDSHAPE_TARGETS = ['target01', 'target02', 'target03']

    def setupScene(self):
        """Setup the inital scene"""
        cmds.file(new=True, force=True)
        self.sphere = cmds.polySphere()[0]
        cmds.delete(self.sphere, constructionHistory=True)

        # create a joint
        joint = cmds.createNode("joint")

        cmds.skinCluster(joint, self.sphere, name="pSphere1_skinCluster")

        # create a delta mush
        cmds.deltaMush("pSphere1", name="pSphere1_deltaMush")

        # create a blendshape
        blendshapeNode = blendshape.create(self.sphere)
        blendshape.addEmptyTarget(blendshapeNode, "target01")
        blendshape.addEmptyTarget(blendshapeNode, "target02")
        blendshape.addEmptyTarget(blendshapeNode, "target03")

    def setupDeformLayers(self, filePath):
        """Setup the deformation layers"""
        self.setupScene()

        # add the deform layers
        sphereDeformLayers = deformLayer.DeformLayer(self.sphere)
        sphereDeformLayers.createDeformLayer("layer01")
        sphereDeformLayers.createDeformLayer("layer02")
        sphereDeformLayers.createDeformLayer("layer03")

        # export the data
        layerDataObj = deformLayer_data.DeformLayerData()
        layerDataObj.gatherData(self.sphere)

        layerDataObj.write(filePath)

    def testAddDeformationLayers(self):
        """Test to see if we can add deformation layers"""
        layerDataFile = self.getTempFilename("deformLayer_data.json")
        self.setupScene()
        self.setupDeformLayers(layerDataFile)

        sphereDeformLayers = deformLayer.DeformLayer(self.sphere)

        self.assertEqual(sphereDeformLayers.getDeformationLayers(), self.EXPECTED_LAYERS)

    def testExportLayerData(self):
        """Ensure the deform layer data can be exported """

        layerDataFile = self.getTempFilename("deformLayer_data.json")

        self.setupScene()
        self.setupDeformLayers(layerDataFile)

        layerDataObj = deformLayer_data.DeformLayerData()
        layerDataObj.gatherData(self.sphere)

        # check to make sure the file exists
        self.assertFileExists(layerDataFile)
        data = layerDataObj.getData()

        # check to see if there are 5 keys in the layerData ('dagPath', 'deformLayerGroup' plus 3 deformationLayers)
        self.assertEqual(len(data[self.sphere].keys()), 5)

    def testImportDeformLayerData(self):
        """Make sure the deform layer data can be imported"""

        # setup the scene and export the data
        layerDataFile = self.getTempFilename("deformLayer_data.json")
        self.setupScene()
        self.setupDeformLayers(layerDataFile)

        # clear the scene and try to import the layer data.
        cmds.file(new=True, force=True)

        self.setupScene()

        layerDataObj = deformLayer_data.DeformLayerData()
        layerDataObj.read(layerDataFile)

        layerDataObj.applyAllData()

        self.assertTrue(cmds.objExists("d0_pSphere1_layer01"))
        self.assertTrue(cmds.objExists("d1_pSphere1_layer02"))
        self.assertTrue(cmds.objExists("d2_pSphere1_layer03"))

    def testTransferDeformers(self):
        """ Ensure that deformers can be transfered"""

        self.testImportDeformLayerData()

        # with logger.DisableLogger():
        newBlendshape = deformLayer.transferAllDeformerTypes("pSphere1_bshp", "pSphere1", "d2_pSphere1_layer03")
        newSkincluster = deformLayer.transferAllDeformerTypes("pSphere1_skinCluster", "pSphere1", "d2_pSphere1_layer03")
        newDeltaMush = deformLayer.transferAllDeformerTypes("pSphere1_deltaMush", "pSphere1", "d2_pSphere1_layer03")

        deformerStack = deformer.getDeformerStack("d2_pSphere1_layer03")

        # check to see if there are 4 deformers in the deformerStack (3 deformers plus deformLayer input bshp)
        self.assertEqual(len(deformerStack), 4)

        # check to see if all blendshapes were transfered
        self.assertEqual(blendshape.getTargetList(newBlendshape), self.EXPECTED_BLENDSHAPE_TARGETS)
