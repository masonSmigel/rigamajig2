#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: realisticEyelid.py.py
    author: masonsmigel
    date: 11/2022
    discription: 

"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
from rigamajig2.shared import common
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import spaces
from rigamajig2.maya.rig import live
from rigamajig2.maya import attr
from rigamajig2.maya import transform
from rigamajig2.maya import joint
from rigamajig2.maya import meta
from rigamajig2.maya import node
from rigamajig2.maya import curve
from rigamajig2.maya import hierarchy
from rigamajig2.maya import mathUtils
from rigamajig2.maya import blendshape

GUIDE_SCALE = 0.2


class RealisticEyelid(rigamajig2.maya.cmpts.base.Base):
    """
    A realistic eyelid component.

    This is a realistic eyelid because it is based on a sphereical eyeball.
    Cartoony or non-sphereical eyes are a spearate component.

    NOTE: It is important that the model has an equal number of spans on the top and bottom lids.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str(), eyelidSpans=8, addCrease=True):
        """
        :param name: Component Name
        :param input: A single joint located at the center of the eyeball. This will become the eyeRoot.
        :param size: default size of the controls
        :param rigParent: connect the component to a rigParent
        :param eyelidSpans: The number of spans from the inner corner to the outer corner.
                            This will be used to create joints on each span of the lid
        :param addCrease: if True a second set of joints around the crease of the eyelid will be created.
        """
        super(RealisticEyelid, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['eyelidSpans'] = eyelidSpans
        self.cmptSettings['addCrease'] = addCrease

        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.cmptSettings['eyeSocketName'] = inputBaseNames[0]

    def createBuildGuides(self):
        """Create all build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        socketPos = cmds.xform(self.input[0], q=True, ws=True, t=True)

        # create the up vector
        self.upVectorGuide = control.createGuide("{}_upVecTgt".format(self.name),
                                                 parent=self.guidesHierarchy,
                                                 position=socketPos)

        # create the eyelid guides
        self.upperLidGuidesList = list()
        self.lowerLidGuidesList = list()

        sideMultipler = -1 if self.side == 'r' else 1
        midpoint = (float(self.eyelidSpans - 1) * 0.5) * GUIDE_SCALE
        guideSize = self.size * GUIDE_SCALE

        self.lidGuideHierarchy = cmds.createNode("transform", name='{}_Eyelid_guide'.format(self.name),
                                               parent=self.guidesHierarchy)
        for part in ['upper', 'lower']:
            for x in range(self.eyelidSpans):
                # first we can caluclate the position of the guides at the origin
                # then multiply them by the postion of the socket joint to position them around the eyeball.
                translateX = float(-midpoint + (x * GUIDE_SCALE)) * sideMultipler
                translateY = 1 if part == 'upper' else -1
                localPos = (translateX, translateY, 0)
                guidePos = mathUtils.addVector(localPos, socketPos)

                guide = control.createGuide(
                    name="{}_{}_{}".format(self.name, part, x),
                    parent=self.lidGuideHierarchy,
                    position=guidePos,
                    size=guideSize)

                # add the guide to the upper or lower guide list
                if part == 'upper':
                    self.upperLidGuidesList.append(guide)
                elif part == 'lower':
                    self.lowerLidGuidesList.append(guide)

        # Create the inner and outer guides.
        # Once again we add the midpointScale to the socket position.
        self.innCornerGuide = control.createGuide(
            "{}_inn_corner".format(self.name),
            parent=self.lidGuideHierarchy,
            position=mathUtils.addVector(((-midpoint - GUIDE_SCALE) * sideMultipler, 0, 0), socketPos),
            size=guideSize)
        self.outCornerGuide = control.createGuide(
            "{}_out_corner".format(self.name),
            parent=self.lidGuideHierarchy,
            position=mathUtils.addVector(((midpoint + GUIDE_SCALE) * sideMultipler, 0, 0), socketPos),
            size=guideSize)

        # create a curve through the guide points so we can attatch the eyelid control guides to them!
        self.upperCurveGuideList = [self.innCornerGuide] + self.upperLidGuidesList + [self.outCornerGuide]
        self.lowerCurveGuideList = [self.innCornerGuide] + self.lowerLidGuidesList + [self.outCornerGuide]

        # add a separate set of guides for the eye crease
        if self.addCrease:
            self.creaseHierarchy = cmds.createNode("transform", name='{}Crease_guide'.format(self.name),
                                                   parent=self.guidesHierarchy)

            self.upperCreaseGuidesList = list()
            self.lowerCreaseGuidesList = list()

            for part in ['upper', 'lower']:
                for x in range(self.eyelidSpans):

                    # first we can caluclate the position of the guides at the origin
                    # then multiply them by the postion of the socket joint to position them around the eyeball.
                    translateX = float(-midpoint + (x * GUIDE_SCALE)) * sideMultipler
                    translateY = 1.5 if part == 'upper' else -1.5
                    localPos = (translateX, translateY, 0)
                    guidePos = mathUtils.addVector(localPos, socketPos)

                    guide = control.createGuide(
                        name="{}_{}Crease_{}".format(self.name, part, x),
                        parent=self.creaseHierarchy,
                        position=guidePos,
                        size=guideSize,
                        color='lightorange')

                    # add the guide to the upper or lower guide list
                    if part == 'upper':
                        self.upperCreaseGuidesList.append(guide)
                    elif part == 'lower':
                        self.lowerCreaseGuidesList.append(guide)

            # Create the inner and outer guides.
            # Once again we add the midpointScale to the socket position.
            self.innCreaseCornerGuide = control.createGuide(
                "{}_innCrease_corner".format(self.name),
                parent=self.creaseHierarchy,
                position=mathUtils.addVector(((-midpoint - GUIDE_SCALE * 1.5) * sideMultipler, 0, 0), socketPos),
                size=guideSize,
                color='lightorange')
            self.outCreaseCornerGuide = control.createGuide(
                "{}_outCrease_corner".format(self.name),
                parent=self.creaseHierarchy,
                position=mathUtils.addVector(((midpoint + GUIDE_SCALE * 1.5) * sideMultipler, 0, 0), socketPos),
                size=guideSize,
                color='lightorange')

        # now add in the eyelid controls
        uppCurveName = "{}_upper_guideCrv".format(self.name)
        uppGuideCurve = live.createLiveCurve(self.upperCurveGuideList, curveName=uppCurveName,
                                             parent=self.guidesHierarchy)

        lowCurveName = "{}_lower_guideCrv".format(self.name)
        lowGuideCurve = live.createLiveCurve(self.lowerCurveGuideList, curveName=lowCurveName,
                                             parent=self.guidesHierarchy)

        self.eyelidControllerGuides = list()
        eyelidControlNames = ['innCorner', 'uppInn', 'upp', 'uppOut', 'outCorner', 'lowInn', 'low', 'lowOut']
        eyelidControlParams = [0, 0.25, 0.5, 0.75, 1, 0.25, 0.5, 0.75]

        for i in range(len(eyelidControlNames)):
            suffix = eyelidControlNames[i]
            guide = control.createGuide("{}_{}".format(self.name, suffix),
                                        # side=self.side,
                                        shape='sphere',
                                        size=GUIDE_SCALE,
                                        parent=self.guidesHierarchy,
                                        color='salmon')

            targetCurve = lowGuideCurve if i > 4 else uppGuideCurve

            minParam, maxParam = curve.getRange(targetCurve)
            param = maxParam * eyelidControlParams[i]
            pointOnCurveInfo = curve.attatchToCurve(guide, targetCurve, toClosestParam=False, parameter=param)

            # create a slide attribute so we can easily slide the controls along the shape of the eyelid
            slideAttr = attr.createAttr(guide, "param", "float", value=param, minValue=minParam, maxValue=maxParam)
            cmds.connectAttr(slideAttr, "{}.{}".format(pointOnCurveInfo, "parameter"))

            attr.lock(guide, attr.TRANSLATE)
            # also if the joint is on the right side we should mirror the translation
            if self.side == 'r':
                cmds.setAttr("{}.jointOrientY".format(guide), 180)

            self.eyelidControllerGuides.append(guide)

    def initalHierachy(self):
        """Build the inital rig hierarchy"""
        super(RealisticEyelid, self).initalHierachy()

        self.eyeSocket = control.createAtObject(name=self.eyeSocketName,
                                                side=self.side,
                                                shape='eye',
                                                orig=True,
                                                xformObj=self.input[0],
                                                parent=self.controlHierarchy)

        self.eyelidControls = list()
        for guide in self.eyelidControllerGuides:
            guideName = guide.split("_guide")[0]
            ctl = control.createAtObject(name=guideName,
                                         shape='triangle',
                                         orig=True,
                                         trs=True,
                                         parent=self.controlHierarchy,
                                         shapeAim='y',
                                         xformObj=guide,
                                         size=GUIDE_SCALE,
                                         hideAttrs=['s', 'v'])

    def preRigSetup(self):
        """ Setup the joints and curves neeeded for this eyelid setup"""
        # create the upVector
        self.upVector = cmds.createNode("transform", name="{}_upVec".format(self.name), p=self.spacesHierarchy)
        transform.matchTranslate(self.upVectorGuide, self.upVector)

        # setup the base curves
        self.curvesHierarchy = cmds.createNode("transform", name="{}_curves".format(self.name), p=self.rootHierarchy)

        upperCurveTrsList = [self.innCornerGuide] + self.upperLidGuidesList + [self.outCornerGuide]
        lowerCurveTrsList = [self.innCornerGuide] + self.lowerLidGuidesList + [self.outCornerGuide]
        upperCurveName = "{}_upperLid_high".format(self.name)
        lowerCurveName = "{}_lowerLid_high".format(self.name)
        upperControlCurveName = "{}_upperLid_low".format(self.name)
        lowerControlCurveName = "{}_lowerLid_low".format(self.name)

        blinkLowCurveName = "{}_blink_low".format(self.name)
        upperBlinkCurveName = "{}_upperLid_blink".format(self.name)
        lowerBlinkCurveName = "{}_lowerLid_blink".format(self.name)

        self.uppDriverCurve = curve.createCurveFromTransform(
            upperCurveTrsList,
            degree=1,
            name=upperCurveName,
            parent=self.curvesHierarchy)
        self.lowDriverCurve = curve.createCurveFromTransform(
            lowerCurveTrsList,
            degree=1,
            name=lowerCurveName,
            parent=self.curvesHierarchy)

        # create the low-res curves
        self.uppControlCurve = cmds.duplicate(self.uppDriverCurve, name=upperControlCurveName)[0]
        cmds.rebuildCurve(self.uppControlCurve, spans=4, degree=3, fitRebuild=True)

        self.lowControlCurve = cmds.duplicate(self.lowDriverCurve, name=lowerControlCurveName)[0]
        cmds.rebuildCurve(self.lowControlCurve, spans=4, degree=3, fitRebuild=True)

        # create the blink curves


        # create the upper and lower blink curves then parent them
        # self.blinkControlCurve = cmds.rebuildCurve(tempBlinkCurve, spans=4, degree=3, rpo=False, name=blinkLowCurveName)[0]
        # self.uppBlinkTgtCurve = cmds.rebuildCurve(tempBlinkCurve, kcp=True, degree=1, rpo=False, name=upperBlinkCurveName)[0]
        # self.lowBlinkTgtCurve = cmds.rebuildCurve(tempBlinkCurve, kcp=True, degree=1, rpo=False, name=lowerBlinkCurveName)[0]
        # cmds.parent(self.blinkControlCurve, self.uppBlinkCurve, self.lowBlinkCurve, self.curvesHierarchy)

        # at this point we no longer need to tempBlinkCurve
        # cmds.delete(tempBlinkCurve)

        # self.blinkControlCurve = cmds.duplicate(self.uppControlCurve, name=blinkLowCurveName)[0]
        self.uppBlinkCurve = cmds.duplicate(self.lowDriverCurve, name=upperBlinkCurveName)[0]
        self.lowBlinkCurve = cmds.duplicate(self.uppDriverCurve, name=lowerBlinkCurveName)[0]

        # When using the point on curve info node to drive the translation of transforms
        # its easier to ensure they dont inherit any transforms than to negate the parent transform.
        # For this case we will use a series of locators to drive the rotation of the eyelid joints.
        self.aimLocHierarchy = cmds.createNode("transform", name="{}_aimTgts".format(self.name), p=self.rootHierarchy)
        cmds.setAttr("{}.inheritsTransform".format(self.aimLocHierarchy), False)

        # setup the joints for the eyelid
        for guide in [self.innCornerGuide] + self.upperLidGuidesList + [self.outCornerGuide] + self.lowerLidGuidesList:
            guideName = guide.split("_guide")[0]

            # create joints... they need to be parented into the bind hierarchy.
            baseJoint = cmds.createNode("joint", name="{}_baseTrs".format(guideName), p=self.input[0])
            transform.matchTranslate(self.input[0], baseJoint)

            endJoint = cmds.createNode("joint", name="{}_bind".format(guideName), p=baseJoint)
            transform.matchTranslate(guide, endJoint)
            joint.setRadius([baseJoint, endJoint], GUIDE_SCALE)
            meta.tag(endJoint, "bind")

            # Orient the joints so that x faces down the chain and y is up. This will be the same on the left AND right side.
            # its not important that the orientation isnt mirrored since the rotation doesnt drive anything
            joint.orientJoints([baseJoint, endJoint], aimAxis='x', upAxis='y', autoUpVector=False)

            # connect the joints to the driver curves
            aimLoc = cmds.createNode("transform", name="{}_trsAimTarget".format(guideName), p=self.aimLocHierarchy)
            transform.matchTranslate(guide, aimLoc)

            targetCurve = self.lowDriverCurve if 'lower' in guideName else self.uppDriverCurve
            curve.attatchToCurve(aimLoc, curve=targetCurve, toClosestParam=True)

            # aim the joint to the targetloc
            cmds.aimConstraint(aimLoc, baseJoint, aimVector=(1, 0, 0), upVector=(0, 1, 0),
                               worldUpType='object', worldUpObject=self.upVector)

    def rigSetup(self):
        """ create the main rig setup """
        # add the inbetweens
        # # to build a better blink system we will make a nuteral blink curve to use as a base.
        tempBlinkCurve = cmds.duplicate(self.uppDriverCurve, name="tmpBlinkCurve")[0]
        cmds.rebuildCurve(tempBlinkCurve, kcp=True, degree=3)
        tempBshp = blendshape.create(tempBlinkCurve, targets=[self.uppBlinkCurve, self.lowBlinkCurve])

        for target in blendshape.getTargetList(tempBshp):
            cmds.setAttr("{}.{}".format(tempBshp, target), 0.5)
        # cmds.delete(tempBlinkCurve, ch=True)
        # smooth out this curve. we can use it add an inbetween to the blendshape targets!
        cmds.smoothCurve("{}.cv[*]".format(tempBlinkCurve), smoothness=15, ch=True)

        # setup the blink wires
        cmds.wire(self.uppDriverCurve, wire=self.uppControlCurve, name="{}_wire".format(self.uppDriverCurve))
        cmds.wire(self.lowDriverCurve, wire=self.lowControlCurve, name="{}_wire".format(self.lowDriverCurve))

        cmds.wire(self.uppBlinkCurve, wire=self.lowControlCurve, name="{}_wire".format(self.uppDriverCurve))
        cmds.wire(self.lowBlinkCurve, wire=self.uppControlCurve, name="{}_wire".format(self.lowDriverCurve))

        # create the upper and lower blink blendshapes
        self.uppBlinkBshp = blendshape.create(self.uppDriverCurve, name="{}_blink".format(self.uppDriverCurve))
        self.lowBlinkBshp = blendshape.create(self.lowDriverCurve, name="{}_blink".format(self.lowDriverCurve))

        # in order to get a proper blend between the two curves we need both blink curves to drive the blendshape.
        for bshp in [self.uppBlinkBshp, self.lowBlinkBshp]:
            blendshape.addTarget(bshp, self.uppBlinkCurve)
            blendshape.addTarget(bshp, self.lowBlinkCurve)
            # blendshape.addInbetween(bshp, tempBlinkCurve, self.uppBlinkCurve)
            blendshape.addInbetween(bshp, tempBlinkCurve, self.lowBlinkCurve)

        # once we have created out inbetweens we can delete the inbetween curve.
        # cmds.delete(tempBlinkCurve)

        # Finally we can build the blink system. the
        blinkAttr = attr.createAttr(self.paramsHierarchy, "blink", "float", value=0, minValue=0, maxValue=1)
        blinkHeightAttr = attr.createAttr(self.paramsHierarchy, "blinkHeight", "float", value=0.15, minValue=0, maxValue=1)

        # create the nodes needed for the blink setup
        lowBlinkMdl = node.multDoubleLinear(blinkHeightAttr, -1, name="{}_blinkHeightReverse".format(self.name))
        lowBlinkAdl = node.addDoubleLinear("{}.{}".format(lowBlinkMdl, "output"), 1, name="{}_lowHeight".format(self.name))

        # connect the blink height into the targets of the blendshape curve
        for bshp in [self.uppBlinkBshp, self.lowBlinkBshp]:
            upperLidAdlAttr = "{}.{}".format(lowBlinkAdl, "output")
            cmds.connectAttr(upperLidAdlAttr, "{}.{}".format(bshp, blendshape.getTargetList(bshp)[0]))
            cmds.connectAttr(blinkHeightAttr, "{}.{}".format(bshp, blendshape.getTargetList(bshp)[1]))



        # connect the blink amount into the evelope for both targets
        cmds.connectAttr(blinkAttr, "{}.{}".format(self.uppBlinkBshp, "envelope"))
        cmds.connectAttr(blinkAttr, "{}.{}".format(self.lowBlinkBshp, "envelope"))

    def setupAnimAttrs(self):
        """Setup animation attributes."""
        attr.addSeparator(self.eyeSocket.name, "----")
        attr.driveAttribute("blink", self.paramsHierarchy, self.eyeSocket.name)
        attr.driveAttribute("blinkHeight", self.paramsHierarchy, self.eyeSocket.name)


    def connect(self):
        """connect to the rig parent"""

        # connect the eyesocket
        # connect the up vector

        pass
