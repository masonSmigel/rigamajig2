#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: brows.py
    author: masonsmigel
    date: 12/2022
    description: brow component module

"""
import maya.cmds as cmds

import rigamajig2.maya.cmpts.base
from rigamajig2.maya import attr
from rigamajig2.maya import constrain
from rigamajig2.maya import curve
from rigamajig2.maya import joint
from rigamajig2.maya import mathUtils
from rigamajig2.maya import meta
from rigamajig2.maya import node
from rigamajig2.maya import transform
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import live
from rigamajig2.shared import common

GUIDE_SCALE = 0.2

WIRE_DROPOFF = 1000


class Brow(rigamajig2.maya.cmpts.base.Base):
    """
    A brow component.

    The brow setup is designed to mimic the muscles of the eyebrow.

    When placing guides start from the inner brow and move to the outside.
    Each brow should have a different eyebrow component.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    UI_COLOR = (151, 219, 175)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param name: Component Name
        :param input: a single joint that will be used to move the whole eyebrow around
        :param size: default size of the controls
        :param rigParent: connect the component to a rigParent
        :param browSpans: The number of spans from the inner brow to the outer brow.
        """
        super(Brow, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        self.defineParameter(parameter="browSpans", value=8, dataType="int")

        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.defineParameter(parameter="browAllName", value=inputBaseNames[0], dataType="string")

    def createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        basePos = cmds.xform(self.input[0], q=True, ws=True, t=True)

        # create the curve guides

        sideMultiplier = -1 if self.side == 'r' else 1
        midpoint = (float(self.browSpans - 1) * 0.5) * (GUIDE_SCALE * 2)
        guideSize = self.size * GUIDE_SCALE

        parent = cmds.createNode("transform", name='{}_spans'.format(self.name), parent=self.guidesHierarchy)

        self.browGuideList = list()
        for x in range(self.browSpans):
            # first we can caluclate the position of the guides at the origin
            # then multiply them by the postion of the socket joint to position them around the eyeball.
            translateX = float(-midpoint + (x * (GUIDE_SCALE * 2))) * sideMultiplier
            translateY = 0
            localPos = (translateX, translateY, 0)
            guidePos = mathUtils.addVector(localPos, basePos)

            guide = control.createGuide(
                name="{}_{}".format(self.name, x),
                parent=parent,
                hideAttrs=['s'],
                position=guidePos,
                size=guideSize)

            self.browGuideList.append(guide)

        # create the brow control guides
        controlsParent = cmds.createNode("transform", name='{}_controls'.format(self.name), parent=self.guidesHierarchy)

        self.browControlGuides = list()
        curveName = "{}_guideCrv".format(self.name)
        browGuideCurve = live.createLiveCurve(self.browGuideList,
                                              curveName=curveName,
                                              parent=self.guidesHierarchy)

        browControlNames = ['inn', 'furrow', 'mid', 'arch', 'out']
        browControlParams = [0, 0.05, 0.37, 0.75, 1]
        for i in range(len(browControlNames)):
            suffix = browControlNames[i]
            guide = control.createGuide("{}_{}".format(self.name, suffix),
                                        # side=self.side,
                                        shape='sphere',
                                        size=GUIDE_SCALE,
                                        parent=controlsParent,
                                        hideAttrs=['s'],
                                        color='salmon')

            minParam, maxParam = curve.getRange(browGuideCurve)
            param = maxParam * browControlParams[i]
            pointOnCurveInfo = curve.attatchToCurve(guide, browGuideCurve, toClosestParam=False, parameter=param)

            # create a slide attribute so we can easily slide the controls along the shape of the eyelid
            slideAttr = attr.createAttr(guide, "param", "float", value=param, minValue=minParam, maxValue=maxParam)
            cmds.connectAttr(slideAttr, "{}.{}".format(pointOnCurveInfo, "parameter"))

            attr.lock(guide, attr.TRANSLATE)
            # also if the joint is on the right side we should mirror the translation
            if self.side == 'r':
                cmds.setAttr("{}.rotateY".format(guide), 180)

            self.browControlGuides.append(guide)

    def initialHierarchy(self):
        """Build the inital rig hierarchy"""
        super(Brow, self).initialHierarchy()

        self.browAll = control.createAtObject(name=self.browAllName,
                                              side=self.side,
                                              shape='square',
                                              orig=True,
                                              xformObj=self.input[0],
                                              parent=self.controlHierarchy)

        self.browControls = list()
        for guide in self.browControlGuides:
            guideName = guide.split("_guide")[0]
            ctl = control.createAtObject(name=guideName,
                                         shape='square',
                                         orig=True,
                                         trs=True,
                                         parent=self.browAll.name,
                                         shapeAim='z',
                                         xformObj=guide,
                                         size=GUIDE_SCALE,
                                         hideAttrs=['s', 'v'])
            self.browControls.append(ctl)

        # create an offset for the tilt
        self.tiltTrs = cmds.createNode('transform',
                                       name="{}_tilt_trs".format(self.browControls[0].name),
                                       parent=self.browControls[0].name)
        transform.matchTransform(self.browControls[0].name, self.tiltTrs)

    def preRigSetup(self):
        """ Setup the joints and curves needed for the brow setup"""

        self.curvesHierarchy = cmds.createNode("transform", name="{}_curves".format(self.name), p=self.rootHierarchy)
        cmds.setAttr("{}.inheritsTransform".format(self.curvesHierarchy), False)

        highCurve = "{}_brows_high".format(self.name)
        lowCurve = "{}_brows_low".format(self.name)

        # create the high curve
        self.driverCurve = curve.createCurveFromTransform(self.browGuideList, degree=1, name=highCurve,
                                                          parent=self.curvesHierarchy)

        # create the low curve
        self.lowCurve = cmds.duplicate(self.driverCurve, name=lowCurve)[0]
        cmds.rebuildCurve(self.lowCurve, spans=4, degree=3, fitRebuild=True)

        # create joints to ride on the curve
        self.targetHierarchy = cmds.createNode("transform", name="{}_tgts".format(self.name), p=self.rootHierarchy)
        cmds.setAttr("{}.inheritsTransform".format(self.targetHierarchy), False)

        for i, guide in enumerate(self.browGuideList):
            guideName = guide.split("_guide")[0]

            endJoint = cmds.createNode("joint", name="{}_bind".format(guideName), p=self.input[0])
            transform.matchTranslate(guide, endJoint)
            joint.setRadius([endJoint], GUIDE_SCALE)
            meta.tag(endJoint, "bind")

            targetLoc = cmds.createNode("transform", name="{}_trsTarget".format(guideName), p=self.targetHierarchy)
            transform.matchTranslate(guide, targetLoc)

            curve.attatchToCurve(targetLoc, curve=self.driverCurve, toClosestParam=True)
            # cmds.tangentConstraint(self.driverCurve, targetLoc, aim=(1, 0, 0), u=(0,1,0))
            constrain.orientConstraint(self.browAll.name, targetLoc)

            joint.connectChains([targetLoc], [endJoint], connectScale=False)

            # we also want to create a tilt joint if this is the first joint
            if i == 0:
                tiltJoint = cmds.createNode("joint", name="{}_tilt_bind".format(guideName), p=self.input[0])
                transform.matchTranslate(guide, tiltJoint)
                joint.setRadius([tiltJoint], GUIDE_SCALE)
                meta.tag(tiltJoint, "bind")

                cmds.parent(tiltJoint, endJoint)
                # offset it just a tiny but in Z so it has a different place in space
                cmds.setAttr("{}.tz".format(tiltJoint), 0.01)

                cmds.orientConstraint(self.tiltTrs, tiltJoint, mo=True)

    def rigSetup(self):
        """ create the main rig setup """
        joint.connectChains([self.browAll.name], [self.input[0]])

        # setup the main wire
        wire1, _ = cmds.wire(self.driverCurve, wire=self.lowCurve,
                             dds=[0, WIRE_DROPOFF], name="{}_wire".format(self.driverCurve))
        cmds.setAttr("{}.scale[0]".format(wire1), 0)

        # setup the main brow transformations
        self.jntHierarchy = cmds.createNode("transform", name="{}_joints".format(self.name), parent=self.rootHierarchy)
        self.setupDriverCurve()

        # setup the tilt trs connections
        attr.addSeparator(self.browControls[0].name, "----")
        tiltAttr = attr.createAttr(self.browControls[0].name, "tilt", "float")
        cmds.connectAttr(tiltAttr, "{}.rz".format(self.tiltTrs))

    def setupDriverCurve(self):
        """ Setup the driver curve"""

        driverJoints = list()
        for ctl in self.browControls:
            jnt = cmds.createNode("joint", name=ctl.name + "_driver", parent=self.jntHierarchy)
            transform.matchTransform(ctl.name, jnt)
            transform.connectOffsetParentMatrix(ctl.name, jnt)

            driverJoints.append(jnt)

        cmds.skinCluster(driverJoints, self.lowCurve, dr=1, mi=2, bm=0, name="{}_skinCluster".format(self.driverCurve))

        # hide the joints
        joint.hideJoints(driverJoints)

        midFollow = attr.createAttr(self.paramsHierarchy, "midFollow", "float", minValue=0,
                                    maxValue=1, value=0.5)
        furrowFollow = attr.createAttr(self.paramsHierarchy, "furrowFollow", "float", minValue=0,
                                       maxValue=1, value=0.9)

        browMidReverse = node.reverse(midFollow, name="{}_browMidFollow".format(self.name))
        browFurrowReverse = node.reverse(furrowFollow, name="{}_browFurrowFollow".format(self.name))

        # connect the constraints
        const1 = cmds.parentConstraint(self.browControls[0].name, self.browControls[3].name, self.browControls[2].orig,
                                       mo=True)
        const2 = cmds.parentConstraint(self.browControls[0].name, self.browControls[2].name, self.browControls[1].orig,
                                       mo=True)

        # connect the mid follow
        cmds.connectAttr(midFollow, "{}.w0".format(const1[0]))
        cmds.connectAttr("{}.outputX".format(browMidReverse), "{}.w1".format(const1[0]))

        # connect the furrow follow
        cmds.connectAttr(furrowFollow, "{}.w0".format(const2[0]))
        cmds.connectAttr("{}.outputX".format(browFurrowReverse), "{}.w1".format(const2[0]))

    def connect(self):
        """connect to the rig parent"""

        if cmds.objExists(self.rigParent):
            # connect the browAll
            transform.connectOffsetParentMatrix(self.rigParent, self.browAll.orig, mo=True)

    def finalize(self):
        """ Finalize the rig setup """
        # hide the curves group
        cmds.setAttr("{}.v".format(self.curvesHierarchy), 0)
        attr.lock(self.curvesHierarchy, attr.TRANSFORMS)
