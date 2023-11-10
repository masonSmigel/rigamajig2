#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_scriptLayering.py
    author: masonsmigel
    date: 08/2022
    discription: 

"""

from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import core
from rigamajig2.maya.builder import scriptManager
from rigamajig2.maya.test import mayaunittest
from rigamajig2.maya.test.mayaunittest import TestCase


class TestBuilderScriptLayering(TestCase):
    """ Test the builder script layering functionality"""

    def test_builderlayering(self):
        """
        Ensure the script layering is resulting in two lists of equal length
        """

        # with logger.DisableLogger():
        tempDir = mayaunittest.Settings.temp_dir
        rigFile = core.newRigEnviornmentFromArchetype(tempDir, "biped", "tempRig")

        for scriptType in [constants.PRE_SCRIPT, constants.POST_SCRIPT, constants.PUB_SCRIPT]:
            archetypeScriptList = scriptManager.GetCompleteScriptList.getScriptList(rigFile, scriptType=scriptType)

            self.assertTrue(len(archetypeScriptList))


if __name__ == '__main__':
    t = TestBuilderScriptLayering()
    t.test_builderlayering()
