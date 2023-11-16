#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_blendshape.py.py
    author: masonsmigel
    date: 11/2023
    description:

"""
import pathlib
import random

import maya.cmds as cmds
import pytest

from rigamajig2.maya import blendshape
from rigamajig2.maya.data import blendshapeData
from rigamajig2.shared.common import getFirstIndex
from rigamajig2.shared.pytestUtils import assertAlmostEqual, getTempFilePath


@pytest.fixture
def testScene():
    cmds.file(newFile=True, force=True)
    sphere = getFirstIndex(cmds.polySphere(constructionHistory=False, name="mySphere"))
    target = getFirstIndex(cmds.polySphere(constructionHistory=False, name="target"))
    cmds.delete(sphere, constructionHistory=True)

    # create a blendshape
    blendshapeNode = blendshape.create(sphere)
    return sphere, blendshapeNode, target


@pytest.fixture()
def dataPath(tmp_path):
    return getTempFilePath(tmp_path, "blendshapeData.json")


def test_createBlendshape(testScene):
    """Test if the create function successfully creates a blendshape"""
    baseGeo, blendshapeNode, target = testScene
    assert blendshape.isBlendshape(blendshapeNode) is True


def test_addTargetToBlendshape(testScene):
    """Test if addTarget function adds a target to the blendshape successfully"""
    baseGeo, blendshapeNode, target = testScene
    result = blendshape.addTarget(blendshape=blendshapeNode, target=target, base=baseGeo)
    assert result == f"{blendshapeNode}.{target}" and cmds.objExists(result)


def test_addEmptyTargetToBlendshape(testScene):
    """Test if addEmptyTarget function adds an empty target to the blendshape successfully"""
    baseGeo, blendshapeNode, target = testScene
    targetName = "emptyTarget1"
    result = blendshape.addEmptyTarget(blendshape=blendshapeNode, target=targetName, base=baseGeo)
    assert result == f"{blendshapeNode}.{targetName}" and cmds.objExists(result)


def test_addInbetweenToBlendshape(testScene):
    """Test if addInbetween function adds an inbetween target to the blendshape successfully"""
    baseGeo, blendshapeNode, target = testScene
    targetName = "target1"
    inbetweenWeight = 0.5
    inbetweenWeight2 = 0.33

    blendshape.addEmptyTarget(blendshape=blendshapeNode, target=targetName, base=baseGeo)

    blendshape.addInbetween(
        blendshape=blendshapeNode,
        targetGeo=target,
        targetName=targetName,
        base=baseGeo,
        weight=inbetweenWeight,
        absolute=True,
    )

    blendshape.addEmptyTarget(
        blendshape=blendshapeNode,
        target=targetName,
        base=baseGeo,
        inbetween=inbetweenWeight2,
        targetWeight=0.0,
        topologyCheck=False,
    )

    assert blendshape.getInputTargetItemList(blendshapeNode, targetName) == [5330, 5500, 6000]


def test_getBaseGeometry(testScene):
    """Test if getBaseGeometry function correctly retrieves the base geometry of a blendshape"""
    baseGeo, blendshapeNode, target = testScene
    result = blendshape.getBaseGeometry(blendshapeNode)
    assert result == baseGeo + "Shape"


def test_getTargetList(testScene):
    """Test if getTargetList function correctly retrieves the list of connected targets to a blendshape"""
    baseGeo, blendshapeNode, target = testScene

    blendshape.addEmptyTarget(blendshape=blendshapeNode, target="target1", base=baseGeo)
    blendshape.addEmptyTarget(blendshape=blendshapeNode, target="target2", base=baseGeo)
    blendshape.addEmptyTarget(blendshape=blendshapeNode, target="target3", base=baseGeo)
    blendshape.addEmptyTarget(blendshape=blendshapeNode, target="target4", base=baseGeo)
    blendshape.addEmptyTarget(blendshape=blendshapeNode, target="target5", base=baseGeo)

    result = blendshape.getTargetList(blendshapeNode)
    # Add assertions based on the expected target list in your specific case and the list is the proper length
    assert isinstance(result, list) and len(result) == 5


def test_convertItiToInbetween():
    """test to ensure we can convert between input target index and inbetween weights"""
    arraySize = 10
    randomWeights = [random.uniform(-5, 10) for _ in range(arraySize)]

    for weight in randomWeights:
        inputTargetIndex = blendshape.inbetweenToIti(weight)
        assert assertAlmostEqual(blendshape.itiToInbetween(inputTargetIndex), weight)


def test_exportBlendshapeData(testScene, dataPath):
    """Test that blendshape data can be exporter properly"""
    baseGeo, blendshapeNode, target = testScene
    blendshape.addTarget(blendshape=blendshapeNode, target=target, base=baseGeo)
    blendshape.addEmptyTarget(blendshape=blendshapeNode, target="target2", base=baseGeo)

    data = blendshapeData.BlendshapeData()
    data.gatherData(baseGeo)
    data.write(dataPath)

    assert pathlib.Path(dataPath).is_file() and len(data.getData()) > 0


def test_importBlendshapeData(testScene, dataPath):
    """Test that blendshape data can be imported properly"""
    test_exportBlendshapeData(testScene, dataPath)

    cmds.file(newFile=True, force=True)
    sphere = getFirstIndex(cmds.polySphere(constructionHistory=False, name="mySphere"))

    data = blendshapeData.BlendshapeData()
    data.read(dataPath)
    data.applyAllData()

    blendshapeNode = getFirstIndex(blendshape.getBlendshapeNodes(sphere))
    assert cmds.objExists(blendshapeNode) and bool(blendshape.getTargetList(blendshapeNode))
