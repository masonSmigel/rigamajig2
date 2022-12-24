#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: chainSpline.py
    author: masonsmigel
    date: 11/2022
    discription: 

"""

"""
chain component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.joint as joint
from rigamajig2.maya import curve
from rigamajig2.maya import node
from rigamajig2.maya import attr

import rigamajig2.shared.common as common
import rigamajig2.maya.node
import rigamajig2.maya.joint

import logging

logger = logging.getLogger(__name__)


class ChainSpline(rigamajig2.maya.cmpts.base.Base):
    """
    Spline chain component.
    This is an ik spline that controls a bunch of joints.

    The joint orient of the chain will be used on the subcontrols.
    They dont nessessarily need to be oriented to aim at their child
    and may behave better when oriented manually.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, numberMainControls=4, closed=True, aimVector=None, upVector=None, rigParent=str()):
        """"
        :param str name: name of the components
        :param list input: list of two joints. A start and an end joint
        :param float int size: default size of the controls:
        :param int numberMainControls: The amout of main controls we want to add
        :param bool closed: closed curve
        :param aimVector: aim vector used in the tanget control to keep subcontrols properly oriented.
        :param upVector: up vector used in the tanget control to keep subcontrols properly oriented.
        :param str rigParent: node to parent to connect the component to in the heirarchy
        """

        super(ChainSpline, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['component_side'] = self.side
        # initalize cmpt settings.
        self.cmptSettings['numberMainControls'] = numberMainControls
        self.cmptSettings['closed'] = closed

        self.cmptSettings['aimVector'] = aimVector or [1, 0, 0]
        self.cmptSettings['upVector'] = aimVector or [0, 1, 0]

        if not closed:
            raise NotImplemented("This has yet to be implemented into rigamajig.")

        # noinspection PyTypeChecker
        if len(self.input) != 2:
            raise RuntimeError('Input list must have a length of 2')

    def setInitalData(self):

        # setup a list of main controller names
        self._loadComponentParametersToClass()
        self.controlNameList = list()
        for i in range(self.numberMainControls):
            controlName = ("mainControl{}Name".format(i))
            self.controlNameList.append(controlName)
            self.cmptSettings[controlName] = "{}Driver_{}".format(self.name, i)

    def createBuildGuides(self):
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self.upVectorGuide = rig_control.createGuide("{}_upVec".format(self.name), parent=self.guidesHierarchy)

        self.mainGuidesList = list()
        for i in range(self.numberMainControls):
            guideName = "mainDriver_{}".format(i)
            guide = rig_control.createGuide(guideName, parent=self.guidesHierarchy)
            self.mainGuidesList.append(guide)

    def initialHierachy(self):
        """Build the initial hirarchy"""
        super(ChainSpline, self).initialHierachy()

        self.mainControls = list()
        self.mainDriverJoints = list()

        for i in range(self.numberMainControls):
            mainControlName = getattr(self, self.controlNameList[i])
            mainControl = rig_control.createAtObject(mainControlName,
                                                     side=self.side,
                                                     xformObj=self.mainGuidesList[i],
                                                     size=self.size * 1.5,
                                                     shape="sphere",
                                                     parent=self.controlHierarchy)
            driverJoint = cmds.createNode("joint", name="{}_drvrTrs".format(mainControlName), parent=mainControl.name)
            joint.hideJoints(driverJoint)

            self.mainControls.append(mainControl)
            self.mainDriverJoints.append(driverJoint)

        # setup controllers for the subjoints
        self.inputList = rigamajig2.maya.joint.getInbetweenJoints(self.input[0], self.input[1])
        inputBaseNames = [x.split("_")[0] for x in self.inputList]

        self.subControlers = list()
        for i, jnt in enumerate(self.inputList):
            subControl = rig_control.createAtObject("{}_0_ik".format(inputBaseNames[i]),
                                                    side=self.side,
                                                    spaces=False,
                                                    trs=True,
                                                    size=self.size,
                                                    color="blue",
                                                    shape='cube',
                                                    xformObj=jnt,
                                                    parent=self.controlHierarchy)

            self.subControlers.append(subControl)

    def rigSetup(self):
        """ Do the rig setup"""

        # TODO: make this closed?
        ikHierarchy = cmds.createNode("transform", name="{}_ik".format(self.name), parent=self.rootHierarchy)
        ikCurve = curve.createCurveFromTransform(self.inputList, degree=3, name="{}_ikCrv".format(self.name),
                                                 form="Closed")
        cmds.setAttr("{}.{}".format(ikCurve, "inheritsTransform"), 0)
        cmds.setAttr("{}.{}".format(ikCurve, "v"), 0)
        ikCurveShape = cmds.listRelatives(ikCurve, s=True)[0]
        cmds.parent(ikCurve, ikHierarchy)

        # make the upVector for the tanget control
        self.upVectorTrs = cmds.createNode("transform", name="{}_upVec".format(self.name), parent=ikHierarchy)
        rig_transform.matchTranslate(self.upVectorGuide, self.upVectorTrs)

        # connect drivercontrols to the ikCurve
        cmds.skinCluster(ikCurve, self.mainDriverJoints, dr=1.0, mi=2, name="{}_skinCluster".format(ikCurve))

        for subControl in self.subControlers:
            closestParameter = curve.getClosestParameter(ikCurve, subControl.name)

            slideAttr = attr.createAttr(subControl.name, "slide", attributeType="float", value=0)

            # create the locators to ride along the curve
            pointOnCurveResult = cmds.createNode("transform", name="{}_pocResult".format(subControl.name))
            cmds.setAttr("{}.{}".format(pointOnCurveResult, "inheritsTransform"), 0)
            cmds.parent(pointOnCurveResult, ikHierarchy)

            # connect the subcontrols to the curve
            slideAdl = node.addDoubleLinear(slideAttr, closestParameter, name="{}_slide".format(subControl.name))

            pointOnCurveInfo = cmds.createNode("pointOnCurveInfo", name="{}_pointOnCurveInfo".format(subControl.name))
            cmds.connectAttr("{}.{}".format(ikCurveShape, "worldSpace[0]"),
                             "{}.{}".format(pointOnCurveInfo, "inputCurve"))
            cmds.connectAttr("{}.{}".format(slideAdl, "output"), "{}.{}".format(pointOnCurveInfo, "parameter"))
            cmds.connectAttr("{}.{}".format(pointOnCurveInfo, "result.position"),
                             "{}.{}".format(pointOnCurveResult, "translate"))

            cmds.tangentConstraint(ikCurve, pointOnCurveResult, aim=self.aimVector, upVector=self.upVector, worldUpType='object',
                                   worldUpObject=self.upVectorTrs)
            # finally connect the point on curve result to the control
            rig_transform.connectOffsetParentMatrix(pointOnCurveResult, subControl.name,
                                                    t=True, r=True, s=False, sh=False, mo=True)

        # connect the controls to the bind joints
        controls = [c.name for c in self.subControlers]
        joint.connectChains(controls, self.inputList)

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            for control in self.mainControls:
                rig_transform.connectOffsetParentMatrix(self.rigParent, control.orig, mo=True)

            rig_transform.connectOffsetParentMatrix(self.rigParent, self.upVectorTrs, mo=True)
