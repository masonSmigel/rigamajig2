#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: splineSquash.py
    author: masonsmigel
    date: 10/2022
    description: spline based squash component

"""

import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import joint
from rigamajig2.maya import mathUtils
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import spline
from rigamajig2.shared import common


class SplineSquash(base.BaseComponent):
    """
    Squash component.
    This is a simple squash component made of a single joint that will scale
    based on the distance between the two end controls.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (39, 189, 46)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: name of the components
        :param list input:  A start and end joint (similar to the chain component)
        :param float int size: default size of the controls:
        :param str rigParent: node to parent to connect the component to in the heirarchy
        :param createBpm: create a duplicate bind pre matrix setup to ensure proper layered skinning
        """
        super(SplineSquash, self).__init__(
            name, input=input, size=size, rigParent=rigParent, componentTag=componentTag
        )
        self.side = common.getSide(self.name)

        self.addBpm = True
        self.topControlName = f"{self.name}Top"
        self.midControlName = f"{self.name}Mid"
        self.botControlName = f"{self.name}Bot"

        self.defineParameter(parameter="addBpm", value=self.addBpm, dataType="bool")
        self.defineParameter(
            parameter="topControlName", value=self.topControlName, dataType="string"
        )
        self.defineParameter(
            parameter="midControlName", value=self.midControlName, dataType="string"
        )
        self.defineParameter(
            parameter="botControlName", value=self.botControlName, dataType="string"
        )

    def _createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode(
            "transform", name="{}_guide".format(self.name)
        )

        botPos = transform.getTranslate(self.input[0])
        topPos = transform.getTranslate(self.input[-1])

        # get the average postion of the top and bottom positions
        averagePos = mathUtils.scalarMult(mathUtils.addVector(botPos, topPos), 0.5)

        self.botGuide = control.createGuide(
            self.name + "_bot",
            side=self.side,
            parent=self.guidesHierarchy,
            position=botPos,
        )

        self.midGuide = control.createGuide(
            self.name + "_mid",
            side=self.side,
            parent=self.guidesHierarchy,
            position=averagePos,
        )
        self.topGuide = control.createGuide(
            self.name + "_end",
            side=self.side,
            parent=self.guidesHierarchy,
            position=topPos,
        )

    def _initialHierarchy(self):
        """Build the initial heirarchy"""
        super(SplineSquash, self)._initialHierarchy()
        self.botControl = control.createAtObject(
            self.botControlName,
            side=self.side,
            hideAttrs=["s", "v"],
            size=self.size,
            color="yellow",
            parent=self.controlHierarchy,
            shape="pyramid",
            shapeAim="x",
            xformObj=self.botGuide,
        )

        self.midControl = control.createAtObject(
            self.midControlName,
            side=self.side,
            hideAttrs=["r", "s", "v"],
            size=self.size,
            color="yellow",
            parent=self.controlHierarchy,
            shape="diamond",
            shapeAim="x",
            xformObj=self.midGuide,
        )

        self.topControl = control.createAtObject(
            self.topControlName,
            side=self.side,
            hideAttrs=["s", "v"],
            size=self.size,
            color="yellow",
            parent=self.controlHierarchy,
            shape="pyramid",
            shapeAim="x",
            xformObj=self.topGuide,
        )

    def _rigSetup(self):
        """build the rig setup"""

        fullJointList = joint.getInbetweenJoints(self.input[0], self.input[-1])
        self.spline = spline.SplineBase(fullJointList, name=self.name + "splineIk")
        self.spline.create(clusters=4, params=self.paramsHierarchy)
        cmds.parent(self.spline.getGroup(), self.rootHierarchy)

        # connect the clusters to the main group
        cmds.parent(self.spline.getClusters()[0], self.botControl.name)
        cmds.parent(self.spline.getClusters()[1], self.midControl.name)
        cmds.parent(self.spline.getClusters()[2], self.midControl.name)
        cmds.parent(self.spline.getClusters()[3], self.topControl.name)

        # connect the twists with an orient constraint
        # this seems to break the whole thing so for now im just going to turn this off. its not a huge benifit either way.
        cmds.orientConstraint(self.botControl.name, self.spline._startTwist, mo=True)
        cmds.orientConstraint(self.topControl.name, self.spline._endTwist, mo=True)

        # connect the volume scale attribute to the top control
        attr.createAttr(
            self.topControl.name,
            "volumeFactor",
            attributeType="float",
            value=1,
            minValue=0,
            maxValue=10,
        )
        cmds.connectAttr(
            "{}.volumeFactor".format(self.topControl.name),
            "{}.volumeFactor".format(self.paramsHierarchy),
        )

        if self.addBpm:
            self.bpmHierarchy = cmds.createNode(
                "transform",
                name="{}_bpm_hrc".format(self.name),
                parent=self.rootHierarchy,
            )

            jointNameList = [x.rsplit("_", 1)[0] + "_bpm" for x in fullJointList]
            self.bpmJointList = joint.duplicateChain(
                fullJointList, parent=self.bpmHierarchy, names=jointNameList
            )

            joint.hideJoints(self.bpmJointList)

    def _connect(self):
        """
        Connect the spline to the rig parent
        :return:
        """
        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(
                self.rigParent, self.botControl.orig, mo=True
            )
            transform.connectOffsetParentMatrix(
                self.rigParent, self.midControl.orig, mo=True
            )
            transform.connectOffsetParentMatrix(
                self.rigParent, self.topControl.orig, mo=True
            )

            if self.addBpm:
                transform.connectOffsetParentMatrix(
                    self.rigParent, self.bpmJointList[0], mo=True
                )
