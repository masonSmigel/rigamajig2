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

from rigamajig2.maya import attr
from rigamajig2.maya import constrain
from rigamajig2.maya import curve
from rigamajig2.maya import joint
from rigamajig2.maya import mathUtils
from rigamajig2.maya import meta
from rigamajig2.maya import node
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import live
from rigamajig2.shared import common

GUIDE_SCALE = 0.2

WIRE_DROPOFF = 1000


class Brow(base.BaseComponent):
    """
    A brow component.

    The brow setup is designed to mimic the muscles of the eyebrow.

    When placing guides start from the inner brow and move to the outside.
    Each brow should have a different eyebrow component.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
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

        self.browSpans = 8
        self.addSdk = False
        self.browAllName = [x.split("_")[0] for x in self.input][0]

        self.defineParameter(parameter="addSdk", value=self.addSdk, dataType="bool")
        self.defineParameter(parameter="browSpans", value=self.browSpans, dataType="int")
        self.defineParameter(parameter="browAllName", value=self.browAllName, dataType="string")

    def _createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name="{}_guide".format(self.name))

        basePos = cmds.xform(self.input[0], query=True, worldSpace=True, translation=True)

        # create the curve guides

        sideMultiplier = -1 if self.side == "r" else 1
        midpoint = (float(self.browSpans - 1) * 0.5) * (GUIDE_SCALE * 2)
        guideSize = self.size * GUIDE_SCALE

        parent = cmds.createNode("transform", name="{}_spans".format(self.name), parent=self.guidesHierarchy)

        self.browGuideList = list()
        for i in range(self.browSpans):
            # first we can calculate the position of the guides at the origin
            # then multiply them by the position of the socket joint to position them around the eyeball.
            translateX = float(-midpoint + (i * (GUIDE_SCALE * 2))) * sideMultiplier
            translateY = 0
            localPos = (translateX, translateY, 0)
            guidePos = mathUtils.addVector(localPos, basePos)

            guide = control.createGuide(
                name="{}_{}".format(self.name, i),
                parent=parent,
                hideAttrs=["s"],
                position=guidePos,
                size=guideSize,
            )

            self.browGuideList.append(guide)

        # create the brow control guides
        controlsParent = cmds.createNode(
            "transform",
            name="{}_controls".format(self.name),
            parent=self.guidesHierarchy,
        )

        self.browControlGuides = list()
        curveName = "{}_guideCrv".format(self.name)
        browGuideCurve = live.createLiveCurve(self.browGuideList, curveName=curveName, parent=self.guidesHierarchy)

        browControlNames = ["inn", "furrow", "mid", "arch", "out"]
        browControlParams = [0, 0.05, 0.37, 0.75, 1]
        for i in range(len(browControlNames)):
            suffix = browControlNames[i]
            guide = control.createGuide(
                "{}_{}".format(self.name, suffix),
                # side=self.side,
                shape="sphere",
                size=GUIDE_SCALE,
                parent=controlsParent,
                hideAttrs=["s"],
                color="salmon",
            )

            minParam, maxParam = curve.getRange(browGuideCurve)
            param = maxParam * browControlParams[i]
            pointOnCurveInfo = curve.attatchToCurve(guide, browGuideCurve, toClosestParam=False, parameter=param)

            # create a slide attribute, so we can easily slide the controls along the shape of the eyelid
            slideAttr = attr.createAttr(
                guide,
                "param",
                "float",
                value=param,
                minValue=minParam,
                maxValue=maxParam,
            )
            cmds.connectAttr(slideAttr, "{}.{}".format(pointOnCurveInfo, "parameter"))

            attr.lock(guide, attr.TRANSLATE)
            # also if the joint is on the right side we should mirror the translation
            if self.side == "r":
                cmds.setAttr("{}.rotateY".format(guide), 180)

            self.browControlGuides.append(guide)

    def _initialHierarchy(self):
        """Build the initial rig hierarchy"""
        super(Brow, self)._initialHierarchy()

        self.browAll = control.createAtObject(
            name=self.browAllName,
            side=self.side,
            shape="square",
            orig=True,
            sdk=self.addSdk,
            xformObj=self.input[0],
            parent=self.controlHierarchy,
        )

        self.browControls = list()
        for guide in self.browControlGuides:
            guideName = guide.split("_guide")[0]
            ctl = control.createAtObject(
                name=guideName,
                shape="square",
                orig=True,
                trs=True,
                sdk=self.addSdk,
                parent=self.browAll.name,
                shapeAim="z",
                xformObj=guide,
                size=GUIDE_SCALE,
                hideAttrs=["s", "v"],
            )
            self.browControls.append(ctl)

        # create an offset for the tilt
        self.tiltTrs = cmds.createNode(
            "transform",
            name="{}_tilt_trs".format(self.browControls[0].name),
            parent=self.browControls[0].name,
        )
        transform.matchTransform(self.browControls[0].name, self.tiltTrs)

    def _preRigSetup(self):
        """Setup the joints and curves needed for the brow setup"""

        self.curvesHierarchy = cmds.createNode(
            "transform", name="{}_curves".format(self.name), parent=self.rootHierarchy
        )
        cmds.setAttr("{}.inheritsTransform".format(self.curvesHierarchy), False)

        highCurve = "{}_brows_high".format(self.name)
        lowCurve = "{}_brows_low".format(self.name)

        # create the high curve
        self.driverCurve = curve.createCurveFromTransform(
            self.browGuideList, degree=1, name=highCurve, parent=self.curvesHierarchy
        )

        # create the low curve
        self.lowCurve = cmds.duplicate(self.driverCurve, name=lowCurve)[0]
        cmds.rebuildCurve(self.lowCurve, spans=4, degree=3, fitRebuild=True)

        # create joints to ride on the curve
        self.targetHierarchy = cmds.createNode(
            "transform", name="{}_targets".format(self.name), parent=self.rootHierarchy
        )
        cmds.setAttr("{}.inheritsTransform".format(self.targetHierarchy), False)

        for i, guide in enumerate(self.browGuideList):
            guideName = guide.split("_guide")[0]

            endJoint = cmds.createNode("joint", name="{}_bind".format(guideName), parent=self.input[0])
            transform.matchTranslate(guide, endJoint)
            joint.setRadius([endJoint], GUIDE_SCALE)
            meta.tag(endJoint, "bind")

            targetLoc = cmds.createNode(
                "transform",
                name="{}_trsTarget".format(guideName),
                parent=self.targetHierarchy,
            )
            transform.matchTranslate(guide, targetLoc)

            curve.attatchToCurve(targetLoc, curve=self.driverCurve, toClosestParam=True)
            # cmds.tangentConstraint(self.driverCurve, targetLoc, aim=(1, 0, 0), u=(0,1,0))
            constrain.orientConstraint(self.browAll.name, targetLoc)

            joint.connectChains([targetLoc], [endJoint], connectScale=False)

            # we also want to create a tilt joint if this is the first joint
            if i == 0:
                tiltJoint = cmds.createNode("joint", name="{}_tilt_bind".format(guideName), parent=self.input[0])
                transform.matchTranslate(guide, tiltJoint)
                joint.setRadius([tiltJoint], GUIDE_SCALE)
                meta.tag(tiltJoint, "bind")

                cmds.parent(tiltJoint, endJoint)
                # offset it just a tiny but in Z, so it has a different place in space
                cmds.setAttr("{}.tz".format(tiltJoint), 0.01)

                cmds.orientConstraint(self.tiltTrs, tiltJoint, maintainOffset=True)

    def _rigSetup(self):
        """create the main rig setup"""
        joint.connectChains([self.browAll.name], [self.input[0]])

        # setup the main wire
        wire1, _ = cmds.wire(
            self.driverCurve,
            wire=self.lowCurve,
            dropoffDistance=(0, WIRE_DROPOFF),
            name="{}_wire".format(self.driverCurve),
        )
        cmds.setAttr("{}.scale[0]".format(wire1), 0)

        # setup the main brow transformations
        self.jntHierarchy = cmds.createNode("transform", name="{}_joints".format(self.name), parent=self.rootHierarchy)
        self.setupDriverCurve()

        # setup the tilt trs connections
        attr.addSeparator(self.browControls[0].name, "----")
        tiltAttr = attr.createAttr(self.browControls[0].name, "tilt", "float")
        cmds.connectAttr(tiltAttr, "{}.rz".format(self.tiltTrs))

    def setupDriverCurve(self):
        """Setup the driver curve"""

        driverJoints = list()
        for ctl in self.browControls:
            jnt = cmds.createNode("joint", name=ctl.name + "_driver", parent=self.jntHierarchy)
            transform.matchTransform(ctl.name, jnt)
            transform.connectOffsetParentMatrix(ctl.name, jnt)

            driverJoints.append(jnt)

        cmds.skinCluster(
            driverJoints,
            self.lowCurve,
            dropoffRate=1,
            maximumInfluences=2,
            bindMethod=0,
            name="{}_skinCluster".format(self.driverCurve),
        )

        # hide the joints
        joint.hideJoints(driverJoints)

        midFollow = attr.createAttr(
            self.paramsHierarchy,
            "midFollow",
            "float",
            minValue=0,
            maxValue=1,
            value=0.5,
        )
        furrowFollow = attr.createAttr(
            self.paramsHierarchy,
            "furrowFollow",
            "float",
            minValue=0,
            maxValue=1,
            value=0.9,
        )

        browMidReverse = node.reverse(midFollow, name="{}_browMidFollow".format(self.name))
        browFurrowReverse = node.reverse(furrowFollow, name="{}_browFurrowFollow".format(self.name))

        # connect the constraints
        const1 = cmds.parentConstraint(
            self.browControls[0].name,
            self.browControls[3].name,
            self.browControls[2].orig,
            maintainOffset=True,
        )
        const2 = cmds.parentConstraint(
            self.browControls[0].name,
            self.browControls[2].name,
            self.browControls[1].orig,
            maintainOffset=True,
        )

        # connect the mid-follow
        cmds.connectAttr(midFollow, "{}.w0".format(const1[0]))
        cmds.connectAttr("{}.outputX".format(browMidReverse), "{}.w1".format(const1[0]))

        # connect the furrow follow
        cmds.connectAttr(furrowFollow, "{}.w0".format(const2[0]))
        cmds.connectAttr("{}.outputX".format(browFurrowReverse), "{}.w1".format(const2[0]))

    def _connect(self):
        """connect to the rig parent"""

        if cmds.objExists(self.rigParent):
            # connect the browAll
            transform.connectOffsetParentMatrix(self.rigParent, self.browAll.orig, mo=True)

    def _finalize(self):
        """Finalize the rig setup"""
        # hide the curves group
        cmds.setAttr("{}.v".format(self.curvesHierarchy), 0)
        attr.lock(self.curvesHierarchy, attr.TRANSFORMS)
