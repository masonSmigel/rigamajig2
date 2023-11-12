#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_base.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""

import os

from rigamajig2.maya import file
from rigamajig2.maya.builder import builder
from rigamajig2.maya.test.mayaTestCase import TestCase

ARCHETYPES_PATH = os.path.abspath(os.path.join(__file__, "../../../", 'archetypes'))


class TestBase(TestCase):

    def test_baseBuild(self):
        file.new(f=True)
        # with logger.DisableLogger():
        b = builder.Builder(os.path.join(ARCHETYPES_PATH, "base", "base.rig"))
        b.run()

    # self.assertEqual(cmds.objExists("skull"), True)

    def test_bipedBuild(self):
        file.new(f=True)
        # with logger.DisableLogger():
        b = builder.Builder(os.path.join(ARCHETYPES_PATH, "biped", "biped.rig"))
        b.run()

    def test_propBuild(self):
        file.new(f=True)
        # with logger.DisableLogger():
        b = builder.Builder(os.path.join(ARCHETYPES_PATH, "prop", "prop.rig"))
        b.run()

    def test_faceBuild(self):
        file.new(f=True)
        # with logger.DisableLogger():
        b = builder.Builder(os.path.join(ARCHETYPES_PATH, "face", "face.rig"))
        b.run()
