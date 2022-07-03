#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: guide.py
    author: masonsmigel
    date: 07/2022

"""
import maya.cmds as cmds
import rigamajig2.sandbox.cmpts.base.guide as guide
import rigamajig2.maya.rig.control as control
import rigamajig2.maya.joint as joint
import rigamajig2.maya.rig.live as live

GUIDE_POSITIONS = {
    "clavicle": (0, 0, 0),
    "shoulder": (10, 0, 0),
    "elbow": (25, 0, -2),
    "wrist": (25, 0, 2)
    }


class ComponentGuide(guide.ComponentGuide):

    def __init__(
            self,
            name="arm",
            side=None,
            jointNames=["clavicle", "shoulder", "elbow", "wrist"],
            size=1.0,
            ikSpaces=dict(),
            pvSpaces=dict(),
            addScale=True,
            addProxyAttrs=True,
            addTwistJoints=True,
            addBendies=True,
            rigParent=None):

        """
        create a limb component.
        Note: x should be the aim axis (-x on right side). z should be down (-z for right side)
        """

        super(ComponentGuide, self).__init__(name=name, side=side,jointNames=jointNames, size=size, rigParent=rigParent)

        self.addParameter("ikSpaces", ikSpaces, "dict")
        self.addParameter("pvSpaces", pvSpaces, "dict")
        self.addParameter("addScale", addScale, "bool")
        self.addParameter("addProxyAttrs", addProxyAttrs, "bool")
        self.addParameter("addTwistJoints", addTwistJoints, "bool")
        self.addParameter("addBendies", addBendies, "bool")

    def createGuides(self):
        """
        Create the guides for the limb component
        :return:
        """
        guidesHrc = cmds.createNode("transform", name="{}_guide".format(self.name))

        baseGuide = control.createGuide(self.jointNames[0], side=self.side, joint=True, parent=guidesHrc,
                                        hideAttrs=["v"])
        upperGuide = control.createGuide(self.jointNames[1], side=self.side, joint=True, parent=baseGuide,
                                         hideAttrs=["v"])
        lowerGuide = control.createGuide(self.jointNames[2], side=self.side, joint=True, parent=upperGuide,
                                         hideAttrs=["v"])
        tipGuide = control.createGuide(self.jointNames[3], side=self.side, joint=True, parent=lowerGuide,
                                       hideAttrs=["v"])
        guides = [baseGuide, upperGuide, lowerGuide, tipGuide]

        # For each guide use the guide position dictionary to position the guides.
        # If the side is on the right then flip the default positions.
        #
        for guide, key in zip(guides, ["clavicle", "shoulder", "elbow", "wrist"]):
            position = GUIDE_POSITIONS[key]

            # if the joints are on the right side mirror them
            if self.side == "r":
                position = (position[0] * -1, position[1], position[2])

            cmds.xform(guide, r=True, translation=position)

        # Give the joints a default orientation.
        aimAxis = 'x'
        upAxis = 'z'
        if self.side == 'r':
            aimAxis = '-x'
            upAxis = '-z'
        joint.orientJoints(guides, aimAxis=aimAxis, upAxis=upAxis, )

        # Setup the polevector control and two display lines to help visualise the component.
        guidePv = live.createlivePoleVector([upperGuide, lowerGuide, tipGuide])
        cmds.parent(guidePv, guidesHrc)
        control.createDisplayLine(lowerGuide, guidePv, "{}_pvLine".format(self.name), guidesHrc, 'temp')
        control.createDisplayLine(upperGuide, tipGuide, "{}_ikLine".format(self.name), guidesHrc, "temp")


if __name__ == '__main__':
    import rigamajig2

    rigamajig2.reloadModule()

    cmds.file(new=True, f=True)

    g = Guide("limb_l", side='l', size=1, rigParent="yourMom")
    g.initalize()

    g = Guide("limb_r", side='r', size=1, rigParent="yourMom")
    g.initalize()
