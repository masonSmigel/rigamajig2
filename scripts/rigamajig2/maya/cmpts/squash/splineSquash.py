#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: splineSquash.py
    author: masonsmigel
    date: 10/2022
    discription: spline based squash component

"""

import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.joint as joint
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.node as node
import rigamajig2.maya.rig.spline as spline
import rigamajig2.maya.mathUtils as mathUtils


class SplineSquash(rigamajig2.maya.cmpts.base.Base):
    """
    Squash component.
    This is a simple squash component made of a single joint that will scale
    based on the distance between the two end controls.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    UI_COLOR = (39, 189, 46)

    def __init__(self, name, input, size=1, rigParent=str(), createBpm=True):
        """
        :param str name: name of the components
        :param list input:  A start and end joint (similar to the chain component)
        :param float int size: default size of the controls:
        :param str rigParent: node to parent to connect the component to in the heirarchy
        :param createBpm: create a duplicate bind pre matrix setup to ensure proper layered skinning
        """
        super(SplineSquash, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)
        self.cmptSettings['component_side'] = self.side

        self.cmptSettings['createBpm'] = createBpm
        self.cmptSettings['topControlName'] = "{}Top".format(self.name)
        self.cmptSettings['midControlName'] = "{}Mid".format(self.name)
        self.cmptSettings['botControlName'] = "{}Bot".format(self.name)

    def createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        botPos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        topPos = cmds.xform(self.input[-1], q=True, ws=True, t=True)

        # get the average postion of the top and bottom positions
        averagePos = mathUtils.scalarMult(mathUtils.addVector(botPos, topPos), 0.5)

        self.botGuide = rig_control.createGuide(self.name + "_bot",
                                                side=self.side,
                                                parent=self.guidesHierarchy,
                                                position=botPos,
                                                )

        self.midGuide = rig_control.createGuide(self.name + "_mid",
                                                side=self.side,
                                                parent=self.guidesHierarchy,
                                                position=averagePos,
                                                )
        self.topGuide = rig_control.createGuide(self.name + "_end",
                                                side=self.side,
                                                parent=self.guidesHierarchy,
                                                position=topPos,
                                                )

    def initialHierarchy(self):
        """ Build the initial heirarchy"""
        super(SplineSquash, self).initialHierarchy()
        self.botControl = rig_control.createAtObject(self.botControlName, side=self.side,
                                                     hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                                     parent=self.controlHierarchy, shape='pyramid', shapeAim='x',
                                                     xformObj=self.botGuide)

        self.midControl = rig_control.createAtObject(self.midControlName, side=self.side,
                                                     hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                                     parent=self.controlHierarchy, shape='diamond', shapeAim='x',
                                                     xformObj=self.midGuide)

        self.topControl = rig_control.createAtObject(self.topControlName, side=self.side,
                                                     hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                                     parent=self.controlHierarchy, shape='pyramid', shapeAim='x',
                                                     xformObj=self.topGuide)

    def rigSetup(self):
        """ build the rig setup"""

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
        rig_attr.createAttr(self.topControl.name, 'volumeFactor', attributeType='float', value=1, minValue=0, maxValue=10)
        cmds.connectAttr("{}.volumeFactor".format(self.topControl.name), "{}.volumeFactor".format(self.paramsHierarchy))

        if self.createBpm:
            self.bpmHierarchy = cmds.createNode("transform", name="{}_bpm_hrc".format(self.name), parent=self.rootHierarchy)

            jointNameList = [x.rsplit("_", 1)[0] + "_bpm" for x in fullJointList]
            self.bpmJointList = joint.duplicateChain(fullJointList, parent=self.bpmHierarchy, names=jointNameList)

            joint.hideJoints(self.bpmJointList)

    def connect(self):
        """
        Connect the spline to the rig parent
        :return:
        """
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.botControl.orig, mo=True)
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.midControl.orig, mo=True)
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.topControl.orig, mo=True)

            if self.createBpm:
                rig_transform.connectOffsetParentMatrix(self.rigParent, self.bpmJointList[0], mo=True)


