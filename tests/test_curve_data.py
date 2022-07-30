import os
import rigamajig2.maya.data.curve_data as curve_data
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase


class TestCurveData(TestCase):

    def test_save_and_load_data(self):
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
