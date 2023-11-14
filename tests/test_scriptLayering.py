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


def test_builderLayering(tmpdir):
    """
    Ensure the script layering is resulting in two lists of equal length
    """
    rigFile = core.newRigEnvironmentFromArchetype(str(tmpdir), "biped", "tempRig")

    for scriptType in [constants.PRE_SCRIPT, constants.POST_SCRIPT, constants.PUB_SCRIPT]:
        archetypeScriptList = scriptManager.GetCompleteScriptList.getScriptList(rigFile, scriptType=scriptType)

        assert bool(len(archetypeScriptList))


if __name__ == "__main__":
    t = TestBuilderScriptLayering()
    t.test_builderlayering()
