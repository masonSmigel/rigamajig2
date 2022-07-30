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
from rigamajig2.maya.cmpts.limb import limb
from rigamajig2.maya.cmpts.arm import arm
from rigamajig2.maya.cmpts.leg import leg
from rigamajig2.maya.cmpts.main import main
from rigamajig2.maya.cmpts.chain import chain
from rigamajig2.maya.cmpts.chain import splineFK
from rigamajig2.maya.cmpts.basic import basic
from rigamajig2.maya.cmpts.spine import spine
from rigamajig2.maya.cmpts.neck import neck
from rigamajig2.maya.cmpts.cog import cog
from rigamajig2.maya.cmpts.hand import hand
from rigamajig2.maya.cmpts.lookAt import lookAt
from rigamajig2.maya.cmpts.squash import simpleSquash
from rigamajig2.maya.cmpts import base


class TestComponents(TestCase):
    def test_armBuild(self):
        self.loadPlugins("quatNodes")
        for side in 'lr':
            name = "arm_{}".format(side)
            joints = arm.Arm.createInputJoints(name, side=side)
            cmpt = arm.Arm(name, input=joints)
            base.Base.testBuild(cmpt)

    def test_basicBuild(self):
        """
        Test the build of the basic component.
        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        name = "basic_l"
        side = 'l'
        joints = basic.Basic.createInputJoints(name, side=side)
        cmpt = basic.Basic(name, input=joints)
        base.Base.testBuild(cmpt)

    def test_chainBuild(self):
        """
        Test the build of the chain component.
        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        for side in 'lr':
            name = "chain_{}".format(side)
            joints = chain.Chain.createInputJoints(name, side=side)
            cmpt = chain.Chain(name, input=joints)
            base.Base.testBuild(cmpt)

    def test_splineFkBuild(self):
        """
        Test the build of the splineFK component.
        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        for side in 'lr':
            name = "splineFk_{}".format(side)
            joints = splineFK.SplineFK.createInputJoints(name, side=side)
            cmpt = splineFK.SplineFK(name, input=joints)
            base.Base.testBuild(cmpt)

    def test_cogBuild(self):
        self.loadPlugins("quatNodes")

        name = "cog"
        joints = cog.Cog.createInputJoints(name)
        cmpt = cog.Cog(name, input=joints)
        base.Base.testBuild(cmpt)

    def test_handBuild(self):
        self.loadPlugins("quatNodes")
        for side in 'lr':
            name = "side_{}".format(side)
            joints = hand.Hand.createInputJoints(name, side=side)
            cmpt = hand.Hand(name, input=joints)
            base.Base.testBuild(cmpt)

    def test_legBuild(self):
        self.loadPlugins("quatNodes")
        for side in 'lr':
            name = "leg_{}".format(side)
            joints = leg.Leg.createInputJoints(name, side=side)
            cmpt = leg.Leg(name, input=joints)
            base.Base.testBuild(cmpt)

    def test_limbBuild(self):
        self.loadPlugins("quatNodes")
        name = "limb_l"
        side = 'l'
        joints = limb.Limb.createInputJoints(name, side=side)
        cmpt = limb.Limb(name, input=joints)
        base.Base.testBuild(cmpt)

    def test_lookatBuild(self):
        """
        Test the build of the neck component.
        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        name = "lookAt"
        joints = lookAt.LookAt.createInputJoints(name)
        cmpt = lookAt.LookAt(name, input=joints)
        base.Base.testBuild(cmpt)

    def test_mainBuild(self):
        """
        Test the build of the neck component.
        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        name = "main"
        joints = main.Main.createInputJoints(name)
        cmpt = main.Main(name, input=joints)
        base.Base.testBuild(cmpt)

    def test_neckBuild(self):
        """
        Test the build of the neck component.
        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        name = "neck"
        joints = neck.Neck.createInputJoints(name)
        cmpt = spine.Spine(name, input=joints)
        base.Base.testBuild(cmpt)

    def test_spineBuild(self):
        """
        Test the build of the spine component.
        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        name = "spine"
        joints = spine.Spine.createInputJoints(name)
        cmpt = spine.Spine(name, input=joints)
        base.Base.testBuild(cmpt)

    def test_simpleSquashBuild(self):
        """
        Test the build of the neck component.
        The test passes if the component is properly built without error.
        """
        self.loadPlugins("quatNodes")
        name = "main"
        joints = simpleSquash.SimpleSquash.createInputJoints(name)
        cmpt = simpleSquash.SimpleSquash(name, input=joints)
        base.Base.testBuild(cmpt)