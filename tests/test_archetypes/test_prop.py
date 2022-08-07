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
import logging
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase
from rigamajig2.maya.builder import builder
from rigamajig2.shared import logger


ARCHETYPES_PATH = os.path.abspath(os.path.join(__file__, "../../../", 'archetypes'))


class TestBase(TestCase):

    def test_propBuild(self):
        with logger.DisableLogger():
            b = builder.Builder(os.path.join(ARCHETYPES_PATH, "prop", "prop.rig"))
            b.run()
