import os 
import maya.cmds as cmds

from rigamajig.shared.test.mayaunittest import TestCase


class MyTestCase(TestCase):
    def test_something(self):
        self.assertEqual(True, False)

