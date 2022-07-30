#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_biped.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""

import os
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase
from rigamajig2.maya.rig_builder import builder

ARCHETYPES_PATH = os.path.abspath(os.path.join(__file__, "../../../", 'archetypes'))


class TestBiped(TestCase):

    def test_bipedBuild(self):
        b = builder.Builder(os.path.join(ARCHETYPES_PATH, "biped", "biped.rig"), log=True)
        b.run()
        # self.assertEqual(cmds.objExists("skull"), True)
