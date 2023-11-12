import os

import maya.cmds as cmds

import rigamajig2.maya.data.nodeData as node_data
import rigamajig2.shared.common as common
from rigamajig2.maya.test.mayaTestCase import TestCase


class TestNodeData(TestCase):
    goal_matrix = [
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
        1.0]

    def create_source_locator(self, file_path):
        # Create a locator and move it somewhere
        loc = common.getFirstIndex(cmds.spaceLocator(n='loc'))
        cmds.xform(loc, m=self.goal_matrix)

        d = node_data.NodeData()
        d.gatherData(loc)
        d.write(file_path)

        cmds.file(f=True, new=True)

    def test_export_data(self):
        """
        Ensure the export node data works
        """

        file_path = self.getTempFilename("test_node_data.json")
        self.create_source_locator(file_path)
        # Check if the file was created
        self.assertTrue(os.path.exists(file_path))

        # Create a new locator and attemp to apply data from it.
        loc = common.getFirstIndex(cmds.spaceLocator(n='loc'))
        d = node_data.NodeData()
        d.read(file_path)
        d.applyData(common.toList(loc))

        # Check if the new locator matches the source position
        self.assertListAlmostEqual(cmds.xform(common.getFirstIndex(loc), q=True, m=True), self.goal_matrix, 4)

    def test_import_worldspace(self):
        """
        Ensure the import node data in worldspace works
        """
        file_path = self.getTempFilename("test_node_data.json")
        self.create_source_locator(file_path)

        # Create a new locator and attemp to apply data from it.
        loc = common.getFirstIndex(cmds.spaceLocator(n='loc'))
        d = node_data.NodeData()
        d.read(file_path)
        d.applyData(common.toList(loc), worldSpace=True)

        # Check if the new locator matches the source position
        self.assertListAlmostEqual(cmds.xform(common.getFirstIndex(loc), q=True, m=True), self.goal_matrix, 4)

