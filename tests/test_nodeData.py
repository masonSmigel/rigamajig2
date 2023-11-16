import os

import maya.cmds as cmds
import pytest

from rigamajig2.maya.data import nodeData
from rigamajig2.shared import common
from rigamajig2.shared import pytestUtils

goalMatrix = [
    -3.280700704929646,
    -6.152131968012792,
    12.195182885943089,
    0.0,
    -6.497116357792855,
    11.73516618898354,
    4.172237294187388,
    0.0,
    -12.014936221501332,
    -4.665978702679926,
    -5.586068458957761,
    0.0,
    -64.40059897611667,
    31.978133101507908,
    40.416999149985685,
    1.0,
]

tolerance = 1e-6


@pytest.fixture()
def sourceLocatorData(tmp_path):
    filePath = pytestUtils.getTempFilePath(tmp_path, filename="test_nodeData.json")

    cmds.file(force=True, newFile=True)
    # Create a locator and move it somewhere
    loc = common.getFirstIndex(cmds.spaceLocator(name="loc"))
    cmds.xform(loc, matrix=goalMatrix)

    d = nodeData.NodeData()
    d.gatherData(loc)
    d.write(filePath)

    cmds.file(force=True, newFile=True)
    return filePath


def test_exportData(sourceLocatorData, tmp_path):
    """
    Ensure the export node data works
    """

    file_path = sourceLocatorData
    # Check if the file was created
    assert os.path.exists(file_path)

    # Create a new locator and attempt to apply data from it.
    loc = common.getFirstIndex(cmds.spaceLocator(name="loc"))
    d = nodeData.NodeData()
    d.read(file_path)
    d.applyData(common.toList(loc))

    # Check if the new locator matches the source position
    locatorMatrix = cmds.xform(common.getFirstIndex(loc), query=True, matrix=True)
    pytestUtils.assertListsAlmostEqual(locatorMatrix, goalMatrix)


def test_importWorldSpace(sourceLocatorData, tmp_path):
    """
    Ensure the import node data in worldspace works
    """
    file_path = sourceLocatorData
    # self.create_source_locator(file_path)

    # Create a new locator and attempt to apply data from it.
    loc = common.getFirstIndex(cmds.spaceLocator(name="loc"))
    d = nodeData.NodeData()
    d.read(file_path)
    d.applyData(common.toList(loc), worldSpace=True)

    # Check if the new locator matches the source position
    locatorMatrix = cmds.xform(common.getFirstIndex(loc), query=True, matrix=True)
    pytestUtils.assertListsAlmostEqual(locatorMatrix, goalMatrix)
