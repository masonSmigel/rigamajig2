import os
import rigamajig2.maya.data.curve_data as curve_data
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase

import rigamajig2.maya.rig.builder as buider


class TestBasicRigBuild(TestCase):

    def test_simple_biped(self):
        """
        build a simple biped rig
        """

        self.load_plugin('quatNodes')
        self.load_plugin('matrixNodes')

        archetype_path = (os.path.abspath(os.path.join(os.path.dirname(__file__),"../archetypes/biped/biped.rig")))

        b = buider.Builder(archetype_path)
        b.run()

        self.assertTrue(True)



