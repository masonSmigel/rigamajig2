#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: splineFk.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spline as spline
import rigamajig2.maya.rig.spaces as spaces
from rigamajig2.shared import common as common


class SplineFK(rigamajig2.maya.cmpts.base.Base):
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

    def __init__(self, name, input, size=1, rigParent=str(), numControls=4, addFKSpace=False):
        """
        :param str name: name of the components
        :param list input: list of two joints. A start and an end joint
        :param float int size: default size of the controls:
        :param int numControls: number of controls to add along the spline
        :param bool addFKSpace: add a world/local space switch to the fk chain
        """
        super(SplineFK, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)
        self.cmptSettings['component_side'] = self.side

        # initalize cmpt settings
        self.cmptSettings['numControls'] = numControls

        self.cmptSettings['fkControlName'] = "{}_fk_0".format(self.name)
        self.cmptSettings['ikControlName'] = "{}_ik_0".format(self.name)

        self.cmptSettings['addFKSpace'] = addFKSpace

        self.inputList = rigamajig2.maya.joint.getInbetweenJoints(self.input[0], self.input[1])

        # noinspection PyTypeChecker
        if len(self.input) != 2:
            raise RuntimeError('Input list must have a length of 2')

    def createBuildGuides(self):
        """Create the build guides"""

        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        pos = cmds.xform(self.inputList[0], q=True, ws=True, t=True)
        self.upVectorGuide = rig_control.createGuide(self.name + "_upVector", parent=self.guidesHierarchy,
                                                     position=pos)

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(SplineFK, self).initalHierachy()

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

    def rigSetup(self):
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

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.fkControlList[0].orig, s=False, sh=False, mo=True)

        if self.addFKSpace:
            spaces.create(self.fkControlList[0].spaces, self.fkControlList[0].name, parent=self.spacesHierarchy)

            # if the main control exists connect the world space
            if cmds.objExists('trs_motion'):
                spaces.addSpace(self.fkControlList[0].spaces, ['trs_motion'], nameList=['world'], constraintType='orient')

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=4):
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        joints = list()

        parent = None
        for i in range(numJoints):
            name = name or 'splineFk'
            jointName  = naming.getUniqueName("{}_0".format(name))
            jnt = cmds.createNode("joint", name=jointName)

            if parent:
                cmds.parent(jnt, parent)
            if i > 0:
                cmds.xform(jnt, objectSpace=True, t=(0, 5, 0))

            joints.append(jnt)
            parent = jnt

        joint .orientJoints(joints, aimAxis='x', upAxis='y')
        cmds.setAttr("{}.jox".format(joints[0]), -90)
        return [joints[0], joints[-1]]