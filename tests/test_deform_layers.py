#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_deform_layers.py.py
    author: masonsmigel
    date: 09/2023
    discription: 

"""
import os
import rigamajig2.maya.data.deformLayer_data as deformLayer_data
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase


class TestDeformLayers(TestCase):

    def setupScene(self):
        self.sphere = cmds.polySphere()
        cmds.delete(self.sphere, constructionHistory=True)

    def testAddDeformationLayers(self):
        """Test to see if we can add deformation layers"""
        self.setupScene()


