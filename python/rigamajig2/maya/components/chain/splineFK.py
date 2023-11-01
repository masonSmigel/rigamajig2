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

import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.components.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.spline as spline
import rigamajig2.maya.transform as rig_transform
from rigamajig2.shared import common as common


class SplineFK(rigamajig2.maya.components.base.Base):
    """
    Spline fk chain  component.
    This component is made of a longer chain of joints connected through a spline ik handle
    uses fk controls to control the clusters of the spline.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
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

        # initialize cmpt settings
        self.defineParameter(parameter="numControls", value=4, dataType="int")

        self.defineParameter(parameter="fkControlName", value=f"{self.name}_fk_0", dataType="string")
        self.defineParameter(parameter="ikControlName", value=f"{self.name}_ik_0", dataType="string")
        self.defineParameter(parameter="addFKSpace", value=False, dataType="bool")

        self.inputList = rigamajig2.maya.joint.getInbetweenJoints(self.input[0], self.input[1])

        # noinspection PyTypeChecker
        if len(self.input) != 2:
            raise RuntimeError('Input list must have a length of 2')

    def _createBuildGuides(self):
        """Create the build guides"""

        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        pos = cmds.xform(self.inputList[0], q=True, ws=True, t=True)
        self.upVectorGuide = rig_control.createGuide(self.name + "_upVector", parent=self.guidesHierarchy,
                                                     position=pos)

    def _initialHierarchy(self):
        """Build the initial hirarchy"""
        super(SplineFK, self)._initialHierarchy()

        self.fkControlList = list()
        self.ikControlList = list()

        hideAttrs = ['v', 's']
        for i in range(self.numControls):
            parent = self.controlHierarchy
            addSpaces = True
            if i > 0:
                parent = self.fkControlList[i - 1].name
                addSpaces = False
            fkControl = rig_control.create(self.fkControlName, spaces=addSpaces, hideAttrs=hideAttrs,
                                            size=self.size, color='blue', parent=parent, shapeAim='x',
                                            shape='square')
            ikControl = rig_control.create(self.ikControlName, hideAttrs=hideAttrs,
                                            size=self.size * 0.5, color='blue', parent=fkControl.name, shapeAim='x',
                                            shape='circle')
            self.fkControlList.append(fkControl)
            self.ikControlList.append(ikControl)

        self.fkControls = [ctl.name for ctl in self.fkControlList]
        self.ikControls = [ctl.name for ctl in self.ikControlList]

    def _rigSetup(self):
        self.ikspline = spline.SplineBase(self.inputList, name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=self.numControls, params=self.paramsHierarchy)
        cmds.parent(self.ikspline.getGroup(), self.rootHierarchy)

        aimAxis = rig_transform.getAimAxis(self.inputList[0])
        upAxis = rig_transform.getClosestAxis(self.inputList[0], self.upVectorGuide)

        aimVector = rig_transform.getVectorFromAxis(aimAxis)
        upVector = rig_transform.getVectorFromAxis(upAxis)

        # setup the controls
        for i in range(len(self.ikspline.getClusters())):
            tempObject = cmds.createNode("transform", n="{}_temp_trs".format(self.name))
            rig_transform.matchTransform(self.ikspline.getClusters()[i], tempObject)

            if i == len(self.ikspline.getClusters()) - 1:
                target = self.ikspline.getClusters()[i - 1]
                # flip the anim vector
                aimVector = [v * -1 for v in aimVector]
            else:
                target = self.ikspline.getClusters()[i + 1]

            const = cmds.aimConstraint(target, tempObject, aimVector=aimVector, upVector=upVector,
                                       worldUpType='object', worldUpObject=self.upVectorGuide, mo=False, w=1)
            cmds.delete(const)

            # setup the rig connections
            rig_transform.matchTransform(tempObject, self.fkControlList[i].orig)
            cmds.parent(self.ikspline.getClusters()[i], self.ikControlList[i].name)

            # orient contstrain the last joint
            cmds.orientConstraint(self.fkControlList[-1].name, self.ikspline.getIkJointList()[-1])

            # delete temp objects
            cmds.delete(tempObject)

        # connect the orientation of the controls to the rig
        cmds.orientConstraint(self.fkControlList[0].name, self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.fkControlList[-1].name, self.ikspline._endTwist, mo=True)

        # setup the ik visablity attribute
        rig_attr.createAttr(self.fkControlList[0].name, "ikVis", "bool", value=0, keyable=False, channelBox=True)

        for control in self.ikControls:
            rig_control.connectControlVisiblity(self.fkControls[0], "ikVis", control)

        # delete the guides
        cmds.delete(self.guidesHierarchy)

    def _connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.fkControlList[0].orig, s=False, sh=False, mo=True)

        if self.addFKSpace:
            spaces.create(self.fkControlList[0].spaces, self.fkControlList[0].name, parent=self.spacesHierarchy)

            # if the main control exists connect the world space
            if cmds.objExists('trs_motion'):
                spaces.addSpace(self.fkControlList[0].spaces, ['trs_motion'], nameList=['world'], constraintType='orient')
