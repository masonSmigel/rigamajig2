#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_scriptLayering.py
    author: masonsmigel
    date: 08/2022
    discription: 

"""

import os
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase
from rigamajig2.maya.builder import builder
from rigamajig2.maya.builder import core
from rigamajig2.shared import common
from rigamajig2.maya.builder import constants
from rigamajig2.maya.test import mayaunittest
from rigamajig2.shared import logger


class TestBuilderScriptLayering(TestCase):
    """ Test the builder script layering functionality"""

    def test_builderlayering(self):
        """
        Ensure the script layering is resulting in two lists of equal length
        """
        with logger.DisableLogger():
            tempDir = mayaunittest.Settings.temp_dir
            rigFile = core.newRigEnviornmentFromArchetype(tempDir, "biped", "tempRig")

        for scriptType in [constants.PRE_SCRIPT, constants.POST_SCRIPT, constants.PUB_SCRIPT]:
            archetypeScriptList = core.GetCompleteScriptList.getScriptList(rigFile, scriptType=scriptType)

            scriptLocalPath = core.getRigData(rigFile, scriptType)

            # manually build a list to compare to.
            baseScriptsPath = os.path.join(common.ARCHETYPES_PATH, 'base', scriptLocalPath[0])
            baseScriptList = core.validateScriptList(baseScriptsPath)

            bipedScriptsPath = os.path.join(common.ARCHETYPES_PATH, 'biped', scriptLocalPath[0])
            bipedScriptList = core.validateScriptList(bipedScriptsPath)

            combinedCheckList = bipedScriptList + baseScriptList

            # check if the lists are equal.
            self.assertEqual(len(archetypeScriptList), len(combinedCheckList))


if __name__ == '__main__':
    t = TestBuilderScriptLayering()
    t.test_builderlayering()
