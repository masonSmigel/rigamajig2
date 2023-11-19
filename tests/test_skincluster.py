#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_skincluster.py.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import pathlib

import maya.cmds as cmds
import pytest

from rigamajig2.maya import skinCluster
from rigamajig2.maya.data import skinData
from rigamajig2.shared import pytestUtils
from rigamajig2.shared.common import getFirst


@pytest.fixture()
def dataPath(tmp_path):
    return pytestUtils.getTempFilePath(tmp_path, "test_skinData.json")


@pytest.fixture()
def setupScene():
    cmds.file(newFile=True, force=True)
    sphere = getFirst(cmds.polySphere(constructionHistory=False, name="mySphere"))
    joint1 = cmds.createNode("joint", name="joint1")
    joint2 = cmds.createNode("joint", name="joint2")

    cmds.xform(joint1, translation=[1, 0, 0])
    cmds.xform(joint2, translation=[-1, 0, 0])

    skin = skinCluster.createSkinCluster(geometry=sphere, influences=[joint1, joint2])

    return sphere, joint1, joint2, skin


def test_getSkinCluster(setupScene):
    sphere, joint1, joint2, skin = setupScene
    assert skinCluster.getSkinCluster(sphere) == skin


def test_getInfluences(setupScene):
    sphere, joint1, joint2, skin = setupScene
    assert skinCluster.getInfluenceJoints(skin) == [joint1, joint2]


def test_exportSkinWeights(setupScene, dataPath):
    sphere, joint1, joint2, skin = setupScene

    data = skinData.SkinData()
    data.gatherData(sphere)
    data.write(dataPath)

    assert pathlib.Path(dataPath).is_file() and len(data.getData()) > 0


def test_weightGetAndSetIdentical(setupScene):
    sphere, joint1, joint2, skin = setupScene
    sourceWeights, _ = skinCluster.getWeights(sphere)
    sourceInfluences = skinCluster.getInfluenceJoints(skin)
    otherSphere = getFirst(cmds.polySphere(constructionHistory=False, name="mySphere"))

    otherSkinCluster = skinCluster.createSkinCluster(geometry=otherSphere, influences=sourceInfluences, maxInfluences=1)
    skinCluster.setWeights(mesh=otherSphere, skincluster=otherSkinCluster, weightDict=sourceWeights)

    otherWeights, _ = skinCluster.getWeights(otherSphere)
    assert sourceWeights == otherWeights


def test_importSkinData(setupScene, dataPath):
    test_exportSkinWeights(setupScene, dataPath)

    cmds.file(newFile=True, force=True)

    sphere = getFirst(cmds.polySphere(constructionHistory=False, name="mySphere"))
    cmds.createNode("joint", name="joint1")
    cmds.createNode("joint", name="joint2")

    data = skinData.SkinData()
    data.read(dataPath)
    data.applyAllData()

    skinNode = getFirst(skinCluster.getSkinCluster(sphere))
    assert cmds.objExists(skinNode) and bool(skinCluster.getInfluenceJoints(skinNode))


def test_copyInfluencesAndWeights(setupScene):
    sphere, joint1, joint2, skin = setupScene

    otherSphere = getFirst(
        cmds.polySphere(constructionHistory=False, name="myOtherSphere", subdivisionsX=16, subdivisionsY=16)
    )

    skinCluster.copySkinClusterAndInfluences(sphere, otherSphere)
    otherSkinCluster = skinCluster.getSkinCluster(otherSphere)

    assert skinCluster.getInfluenceJoints(skin) == skinCluster.getInfluenceJoints(otherSkinCluster)
