#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: splineFk.py
    author: masonsmigel
    date: 07/2022
    description: 

"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import spaces
from rigamajig2.maya.rig import spline
from rigamajig2.shared import common


class SplineFK(base.BaseComponent):
    """
    Spline fk chain  component.
    This component is made of a longer chain of joints connected through a spline ik handle
    uses fk controls to control the clusters of the spline.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (149, 228, 189)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: name of the components
        :param list input: list of two joints. A start and an end joint
        :param float int size: default size of the controls:
        :param int numControls: number of controls to add along the spline
        :param bool addFKSpace: add a world/local space switch to the fk chain
        """
        super(SplineFK, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        self.numControls = 4
        self.fkControlName = f"{self.name}_fk_0"
        self.ikControlName = f"{self.name}_ik_0"
        self.addFkSpace = False

        self.defineParameter(parameter="numControls", value=self.numControls, dataType="int")

        self.defineParameter(parameter="fkControlName", value=self.fkControlName, dataType="string")
        self.defineParameter(parameter="ikControlName", value=self.ikControlName, dataType="string")
        self.defineParameter(parameter="addFKSpace", value=self.addFkSpace, dataType="bool")

        self.inputList = rigamajig2.maya.joint.getInbetweenJoints(self.input[0], self.input[1])

        if len(self.input) != 2:
            raise RuntimeError("Input list must have a length of 2")

    def _createBuildGuides(self):
        """Create the build guides"""

        self.guidesHierarchy = cmds.createNode("transform", name="{}_guide".format(self.name))

        pos = transform.getTranslate(self.inputList[0], worldSpace=True)
        self.upVectorGuide = control.createGuide(self.name + "_upVector", parent=self.guidesHierarchy, position=pos)

    def _initialHierarchy(self):
        """Build the initial hierarchy"""
        super(SplineFK, self)._initialHierarchy()

        self.fkControlList = list()
        self.ikControlList = list()

        hideAttrs = ["v", "s"]
        for i in range(self.numControls):
            parent = self.controlHierarchy
            addSpaces = True
            if i > 0:
                parent = self.fkControlList[i - 1].name
                addSpaces = False
            fkControl = control.create(
                self.fkControlName,
                spaces=addSpaces,
                hideAttrs=hideAttrs,
                size=self.size,
                color="blue",
                parent=parent,
                shapeAim="x",
                shape="square",
            )
            ikControl = control.create(
                self.ikControlName,
                hideAttrs=hideAttrs,
                size=self.size * 0.5,
                color="blue",
                parent=fkControl.name,
                shapeAim="x",
                shape="circle",
            )
            self.fkControlList.append(fkControl)
            self.ikControlList.append(ikControl)

        self.fkControls = [ctl.name for ctl in self.fkControlList]
        self.ikControls = [ctl.name for ctl in self.ikControlList]

    def _rigSetup(self):
        self.ikSpline = spline.SplineBase(self.inputList, name=self.name)
        self.ikSpline.setGroup(self.name + "_ik")
        self.ikSpline.create(clusters=self.numControls, params=self.paramsHierarchy)
        cmds.parent(self.ikSpline.getGroup(), self.rootHierarchy)

        aimAxis = transform.getAimAxis(self.inputList[0])
        upAxis = transform.getClosestAxis(self.inputList[0], self.upVectorGuide)

        aimVector = transform.getVectorFromAxis(aimAxis)
        upVector = transform.getVectorFromAxis(upAxis)

        # setup the controls
        for i in range(len(self.ikSpline.getClusters())):
            tempObject = cmds.createNode("transform", name="{}_temp_trs".format(self.name))
            transform.matchTransform(self.ikSpline.getClusters()[i], tempObject)

            if i == len(self.ikSpline.getClusters()) - 1:
                target = self.ikSpline.getClusters()[i - 1]
                # flip the anim vector
                aimVector = [v * -1 for v in aimVector]
            else:
                target = self.ikSpline.getClusters()[i + 1]

            const = cmds.aimConstraint(
                target,
                tempObject,
                aimVector=aimVector,
                upVector=upVector,
                worldUpType="object",
                worldUpObject=self.upVectorGuide,
                maintainOffset=False,
                weight=1,
            )
            cmds.delete(const)

            # setup the rig connections
            transform.matchTransform(tempObject, self.fkControlList[i].orig)
            cmds.parent(self.ikSpline.getClusters()[i], self.ikControlList[i].name)

            cmds.orientConstraint(self.fkControlList[-1].name, self.ikSpline.getIkJointList()[-1])
            cmds.delete(tempObject)

        # connect the orientation of the controls to the rig
        cmds.orientConstraint(self.fkControlList[0].name, self.ikSpline._startTwist, maintainOffset=True)
        cmds.orientConstraint(self.fkControlList[-1].name, self.ikSpline._endTwist, maintainOffset=True)

        # setup the ik visibility attribute
        attr.createAttr(self.fkControlList[0].name, "ikVis", "bool", value=0, keyable=False, channelBox=True)

        for control in self.ikControls:
            control.connectControlVisiblity(self.fkControls[0], "ikVis", control)

        # delete the guides
        cmds.delete(self.guidesHierarchy)

    def _connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(
                self.rigParent, self.fkControlList[0].orig, s=False, sh=False, mo=True
            )

        if self.addFKSpace:
            spaces.create(self.fkControlList[0].spaces, self.fkControlList[0].name, parent=self.spacesHierarchy)

            # if the main control exists connect the world space
            if cmds.objExists("trs_motion"):
                spaces.addSpace(
                    self.fkControlList[0].spaces, ["trs_motion"], nameList=["world"], constraintType="orient"
                )
