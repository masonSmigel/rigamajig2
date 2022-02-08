import os

import maya.app.evaluationToolkit.evaluationToolkit as et
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase
import rigamajig2.maya.rig.builder as buider


class TestBasicRigBuild(TestCase):

    def test_biped_build(self):
        """
        build a simple biped rig
        """
        archetype_path = (os.path.abspath(os.path.join(os.path.dirname(__file__),"../archetypes/biped/biped.rig")))

        b = buider.Builder(archetype_path)
        b.run()

        self.assertTrue(True)
