#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_limbs.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""

import os
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase
from rigamajig2.maya.builder import builder
from rigamajig2.maya.cmpts.main import main
from rigamajig2.maya.cmpts.basic import basic
from rigamajig2.maya.cmpts.limb import limb
from rigamajig2.maya.cmpts.arm import arm
from rigamajig2.maya.cmpts.leg import leg
from rigamajig2.maya.cmpts.spine import spine
from rigamajig2.maya.cmpts.neck import neck
from rigamajig2.maya.cmpts import base


class TestConnections(TestCase):

    def test_limbConnection(self):
        """
        Test the connection and space switches of the arm and leg components.
        Build a main control, a basic control and an arm and leg components.
        Connect the arm and leg to the basic component to test the spaces and connections.

        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        basicJoints = basic.Basic.createInputJoints("basic")
        armJoints = arm.Arm.createInputJoints("arm", side='r')
        legJoints = leg.Leg.createInputJoints("leg")

        mainCmpt = main.Main("main")
        basicCmpt = basic.Basic("basic", input=basicJoints)
        armCmpt = arm.Arm("arm_r", input=armJoints, ikSpaces={"basic": "basic_jnt"}, )
        legCmpt = leg.Leg("leg", input=legJoints, ikSpaces={"basic": "basic_jnt"})

        b = builder.Builder(log=False)
        b.setComponents([mainCmpt, basicCmpt, legCmpt, armCmpt])
        b.initalize()
        b.guide()
        b.build()
        b.connect()
        b.finalize()

    def test_SpineAndNeckConnection(self):
        """
        Test the connection and space switches of the arm and leg components.
        Build a main control, and a spine and neck control.
        Connect the neck to the spine to test the component connection.

        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        spineJoints = spine.Spine.createInputJoints("spine")
        neckJoints = neck.Neck.createInputJoints("neck")

        mainCmpt = main.Main("main")
        spineCmpt = spine.Spine("spine", input=spineJoints)
        neckCmpts = neck.Neck("neck", input=neckJoints, rigParent='chestTop')

        b = builder.Builder(log=False)
        b.setComponents([mainCmpt, spineCmpt, neckCmpts])
        b.initalize()
        b.guide()
        b.build()
        b.connect()
        b.finalize()





