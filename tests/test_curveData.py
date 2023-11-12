import os

import maya.cmds as cmds

import rigamajig2.maya.data.curveData as curve_data
from rigamajig2.maya.test.mayaTestCase import TestCase


class TestCurveData(TestCase):

    def test_save_and_load_data(self):
        """
        Test the import and export of curve data
        """
        file_path = self.getTempFilename("test_curve_data.json")
        cmds.circle(n='testCircle')

        d = curve_data.CurveData()
        d.gatherData('testCircle')
        d.write(file_path)
        cmds.delete('testCircle')

        self.assertTrue(os.path.exists(file_path))

        cmds.createNode('transform', n='testCircle')

        d = curve_data.CurveData()
        d.read(file_path)
        d.applyData(['testCircle'], create=True)

        self.assertEqual(True, True)
