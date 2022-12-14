#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: lips.py
    author: masonsmigel
    date: 12/2022
    discription: component to build the lips

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
from rigamajig2.maya import constrain
from rigamajig2.maya import skinCluster
from rigamajig2.maya import sdk
from rigamajig2.maya import connection
from rigamajig2.maya.cmpts.lips import lipsUtil

GUIDE_SCALE = 0.2


class Lips(rigamajig2.maya.cmpts.base.Base):
    """
    Lips component

    NOTE: It is important that the model has an equal number of spans on the top and bottom lips.
    The number of spans should also be an ODD number to include the middle loop

    NOTE: As of right now it is also VITAL for the auto animation features that the controls are oriented as follows:
        X - to the side
        Y - up
        Z- forward
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str(), lipSpans=17, useJaw=False, jawJoints=None,
                 addZipperLips=True):
        """
        :param name: Component Name
        :param input: a single joint this will be the pivot where the lips rotate around
        :param size: default size of the controls
        :param rigParent: connect the component to a rigParent
        :param lipSpans: The number of spans from the right corner to the left corner.
        :param useJaw: If true connect the setup to the jaw
        :param jawJoints:  If useJaw then provide the following joints to the jaw:
                            [lipsTop, lipsBot, lips_l, lips_r]
        :param addZipperLips: add the setup to do zipper lips
        """
        super(Lips, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['lipSpans'] = lipSpans
        self.cmptSettings['useJaw'] = useJaw
        self.cmptSettings['jawJoints'] = jawJoints or list()
        self.cmptSettings['addZipperLips'] = addZipperLips

        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.cmptSettings['lipsAllName'] = inputBaseNames[0]

    def createBuildGuides(self):
        """ create all build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        lipsPos = cmds.xform(self.input[0], q=True, ws=True, t=True)

        # create the up vector
        self.upVectorGuide = control.createGuide(
            "{}_upVecTgt".format(self.name),
            parent=self.guidesHierarchy,
            position=lipsPos)

        self.upperLipGuide = control.createGuide(name="{}_uppLipAll".format(self.name),
                                                 parent=self.guidesHierarchy,
                                                 hideAttrs=['s'],
                                                 position=lipsPos,
                                                 size=self.size * (GUIDE_SCALE * 2),
                                                 )
        self.lowerLipGuide = control.createGuide(name="{}_lowLipAll".format(self.name),
                                                 parent=self.guidesHierarchy,
                                                 hideAttrs=['s'],
                                                 position=lipsPos,
                                                 size=self.size * (GUIDE_SCALE * 2),
                                                 )

        # build the lip guides
        self.upperGuideList, self.lowerGuideList = self.createLipGuides()

        uppGuideCurve = live.createLiveCurve(self.upperGuideList,
                                             curveName="{}_upper_guideCrv".format(self.name),
                                             parent=self.guidesHierarchy)
        lowGuideCurve = live.createLiveCurve(self.lowerGuideList,
                                             curveName="{}_lower_guideCrv".format(self.name),
                                             parent=self.guidesHierarchy)
        # build the lip controls
        hierarchyName = "{}_Control_guides".format(self.name)
        controlHierarchy = cmds.createNode("transform", name=hierarchyName, p=self.guidesHierarchy)

        mainControlNames = ['r_corner', 'r_upp', 'upp', 'l_upp', 'l_corner', 'r_low', 'low', 'l_low']
        mainControlParams = [0, 0.25, 0.5, 0.75, 1, 0.25, 0.5, 0.75]

        # create the main controls
        upperLipMain = self.createControlGuides(uppGuideCurve, mainControlNames[:5], mainControlParams[:5],
                                                controlHierarchy)
        lowerLipMain = self.createControlGuides(lowGuideCurve, mainControlNames[5:], mainControlParams[5:],
                                                controlHierarchy)
        self.mainControlGuides = upperLipMain + lowerLipMain

        # create the sub controls
        hierarchyName = "{}_subControl_guides".format(self.name)
        subControlHierarchy = cmds.createNode("transform", name=hierarchyName, p=self.guidesHierarchy)

        uppSubControlNames = ['r_uppOut', 'r_uppInn', 'l_uppInn', 'l_uppOut']

        lowSubControlNames = ['r_lowOut', 'r_lowInn', 'l_lowInn', 'l_lowOut']

        subControlParams = [0.125, 0.375, 0.625, 0.875]

        # create the upperControlGuides
        upperSubControls = self.createControlGuides(uppGuideCurve, uppSubControlNames, subControlParams,
                                                    parent=subControlHierarchy, color='lightorange', size=0.5)
        lowerSubControls = self.createControlGuides(lowGuideCurve, lowSubControlNames, subControlParams,
                                                    parent=subControlHierarchy, color='lightorange', size=0.5)

        self.subControlGuides = [upperLipMain[0]] + upperSubControls + [upperLipMain[-1]] + lowerSubControls

    def createLipGuides(self):
        """ Create the guides around the lips"""

        lipsPos = cmds.xform(self.input[0], q=True, ws=True, t=True)

        parent = cmds.createNode("transform", name='{}_lip_guide'.format(self.name), parent=self.guidesHierarchy)

        upperList = list()
        lowerList = list()

        # to get the proper number of spans we need to subtract 3 (one for the middle then the two corners)
        # next we can divide by 2 to get half of that
        numberSpans = (self.lipSpans - 2)

        midpoint = int(numberSpans * 0.5)

        for section in ['upper', 'lower']:
            for x in range(numberSpans):

                # setup the side and index for the guide names
                if x < midpoint:
                    side = 'r'
                    index = midpoint - x
                if x > midpoint:
                    side = 'l'
                    index = x - midpoint
                if x == midpoint:
                    side = 'c'
                    index = 0

                # build a position array for the guides
                translateX = (-midpoint + x) * (GUIDE_SCALE * 2)
                translateY = 1 if section == 'upper' else -1
                guideSize = self.size * GUIDE_SCALE
                localPos = (translateX, translateY, 0)
                guidePos = mathUtils.addVector(localPos, lipsPos)

                guide = control.createGuide(
                    name="{}_{}_{}_{}".format(self.name, side, section, index),
                    parent=parent,
                    hideAttrs=['s'],
                    position=guidePos,
                    size=guideSize,
                    )

                # add the guide to the upper or lower guide list
                if section == 'upper':
                    upperList.append(guide)
                elif section == 'lower':
                    lowerList.append(guide)

        cornerL = control.createGuide(
            "{}_lCorner".format(self.name),
            parent=parent,
            hideAttrs=['s'],
            position=mathUtils.addVector((((midpoint + 1) * (GUIDE_SCALE * 2)), 0, 0), lipsPos),
            size=guideSize,
            )
        cornerR = control.createGuide(
            "{}_rCorner".format(self.name),
            parent=parent,
            hideAttrs=['s'],
            position=mathUtils.addVector((((-midpoint - 1) * (GUIDE_SCALE * 2)), 0, 0), lipsPos),
            size=guideSize,
            )

        uppGuideList = [cornerR] + upperList + [cornerL]
        lowGuideList = [cornerR] + lowerList + [cornerL]

        return uppGuideList, lowGuideList

    def createControlGuides(self, targetCurve, nameList, paramList, parent, color='salmon', size=1.0):
        """ Create the control guides"""

        returnList = list()

        for i in range(len(nameList)):
            suffix = nameList[i]

            guide = control.createGuide("{}_{}".format(self.name, suffix),
                                        shape='sphere',
                                        size=GUIDE_SCALE * size,
                                        parent=parent,
                                        color=color)
            # find the appropriate parameters
            minParam, maxParam = curve.getRange(targetCurve)
            param = maxParam * paramList[i]
            pointOnCurveInfo = curve.attatchToCurve(guide, targetCurve, toClosestParam=False, parameter=param)

            # create a slide attribute so we can easily slide the controls along the shape of the eyelid
            slideAttr = attr.createAttr(guide, "param", "float", value=param, minValue=minParam, maxValue=maxParam)
            cmds.connectAttr(slideAttr, "{}.{}".format(pointOnCurveInfo, "parameter"))

            attr.lock(guide, attr.TRANSLATE)

            returnList.append(guide)

        return returnList

    def initalHierachy(self):
        """ Build the initial rig hierarchy"""
        super(Lips, self).initalHierachy()

        # create the lips all control
        self.lipsAll = control.createAtObject(name=self.lipsAllName,
                                              side=self.side,
                                              shape='square',
                                              orig=True,
                                              xformObj=self.input[0],
                                              parent=self.controlHierarchy)

        # build the lips upp and down
        self.uppLips = control.createAtObject(name='{}_uppAll'.format(self.name),
                                              shape='square',
                                              orig=True,
                                              trs=True,
                                              parent=self.lipsAll.name,
                                              shapeAim='y',
                                              xformObj=self.upperLipGuide,
                                              size=GUIDE_SCALE * 2,
                                              hideAttrs=['s', 'v'])

        self.lowLips = control.createAtObject(name='{}_lowAll'.format(self.name),
                                              shape='square',
                                              orig=True,
                                              trs=True,
                                              parent=self.lipsAll.name,
                                              shapeAim='y',
                                              xformObj=self.lowerLipGuide,
                                              size=GUIDE_SCALE * 2,
                                              hideAttrs=['s', 'v'])

        # build the main controls
        self.mainControls = list()
        for guide in self.mainControlGuides:
            guideName = guide.split("_guide")[0]
            ctl = control.createAtObject(name=guideName,
                                         shape='triangle',
                                         orig=True,
                                         trs=True,
                                         parent=self.lipsAll.name,
                                         shapeAim='y',
                                         xformObj=guide,
                                         size=GUIDE_SCALE * 2,
                                         hideAttrs=['s', 'v'])
            self.mainControls.append(ctl)

        # we will need to use the corners ALOT so lets store them to use later!
        self.lCorner = self.mainControls[4]
        self.rCorner = self.mainControls[0]

        # parent the upper lip and lower lip joints to the upperLipAll and lowerLipAll
        cmds.parent([x.orig for x in self.mainControls[1:4]], self.uppLips.name)
        cmds.parent([x.orig for x in self.mainControls[5:]], self.lowLips.name)

        # build the subControls
        self.subControls = list()
        for guide in self.subControlGuides:
            guideName = guide.split("_guide")[0] + "Tweak"
            ctl = control.createAtObject(name=guideName,
                                         shape='triangle',
                                         orig=True,
                                         trs=True,
                                         parent=self.lipsAll.name,
                                         shapeAim='y',
                                         xformObj=guide,
                                         size=GUIDE_SCALE,
                                         color='lightblue',
                                         hideAttrs=['s', 'v'])
            self.subControls.append(ctl)

    def preRigSetup(self):
        """ Setup the joints and curves needed for the setup"""
        # create the upVector
        self.upVector = cmds.createNode("transform", name="{}_upVec".format(self.name), p=self.spacesHierarchy)
        transform.matchTranslate(self.upVectorGuide, self.upVector)

        self.curvesHierarchy = cmds.createNode("transform", name="{}_curves".format(self.name), p=self.rootHierarchy)
        cmds.setAttr("{}.inheritsTransform".format(self.curvesHierarchy), False)

        topHighCurve = "{}_upperLip_high".format(self.name)
        botHighCurve = "{}_lowerLip_high".format(self.name)

        topLowCurve = "{}_upperLip_low".format(self.name)
        botLowCurve = "{}_lowerLip_low".format(self.name)

        topMidCurve = "{}_upperLip_mid".format(self.name)
        botMidCurve = "{}_lowerLip_mid".format(self.name)

        # Unlike the eyelids its super important that animators can rotate the lip controls.
        # So to do that we will create our lip control From the CONTROls not the per span guides

        # theese lists are comprised of the main and sub controls that would define the spans fo the lip.
        uppLipPoints = [self.mainControlGuides[0], self.subControlGuides[1], self.mainControlGuides[1],
                        self.subControlGuides[2], self.mainControlGuides[2], self.subControlGuides[3],
                        self.mainControlGuides[3], self.subControlGuides[4], self.mainControlGuides[4]]

        lowLipPoints = [self.mainControlGuides[0], self.subControlGuides[6], self.mainControlGuides[5],
                        self.subControlGuides[7], self.mainControlGuides[6], self.subControlGuides[8],
                        self.mainControlGuides[7], self.subControlGuides[9], self.mainControlGuides[4]]

        # create the two driver curves. The jionts will be bound to this
        self.topDriverCurve = curve.createCurveFromTransform(uppLipPoints, degree=3, name=topHighCurve,
                                                             parent=self.curvesHierarchy)
        self.botDriverCurve = curve.createCurveFromTransform(lowLipPoints, degree=3, name=botHighCurve,
                                                             parent=self.curvesHierarchy)

        # create the two low curves theese will be affected by the corners and upper/lower lips
        self.topLowCurve = cmds.duplicate(self.topDriverCurve, name=topLowCurve)[0]
        self.botLowCurve = cmds.duplicate(self.botDriverCurve, name=botLowCurve)[0]

        # create the two low curves theese will be affected by the corners and upper/lower lips
        self.topMidCurve = cmds.duplicate(self.topDriverCurve, name=topMidCurve)[0]
        self.botMidCurve = cmds.duplicate(self.botDriverCurve, name=botMidCurve)[0]

        # setup joints for each span of the lips
        self.targetHierarchy = cmds.createNode("transform", name="{}_aimTgts".format(self.name), p=self.rootHierarchy)
        cmds.setAttr("{}.inheritsTransform".format(self.targetHierarchy), False)

        # setup the joints for the eyelid
        # we can do this by looping through the upperGuide and lowerGuide lists
        # (skipping the first and last index of the lower lid)
        self.aimTgtList = list()
        for guide in self.upperGuideList + self.lowerGuideList[1:-1]:
            guideName = guide.split("_guide")[0]

            endJoint = cmds.createNode("joint", name="{}_bind".format(guideName), p=self.input[0])
            transform.matchTranslate(guide, endJoint)
            joint.setRadius([endJoint], GUIDE_SCALE)
            meta.tag(endJoint, "bind")

            targetLoc = cmds.createNode("transform", name="{}_trsTarget".format(guideName), p=self.targetHierarchy)
            transform.matchTransform(guide, targetLoc)

            targetCurve = self.botDriverCurve if 'lower' in guideName else self.topDriverCurve
            curve.attatchToCurve(targetLoc, curve=targetCurve, toClosestParam=True)

            # if not self.addZipperLips:
            joint.connectChains([targetLoc], [endJoint])
            self.aimTgtList.append(targetLoc)

    def rigSetup(self):
        """ create the main rig setup """
        joint.connectChains([self.lipsAll.name], [self.input[0]])

        # build the main control curve and its rig systems (this includes the mouthCorners)
        self.setupLowCurve()

        # build the middle resolution curve
        self.setupMidCurve()

        if self.addZipperLips:
            self.setupZipperLips()

    def setupLowCurve(self):
        """
        Build a rig setup for the low res curve.
        (its actully not that low res but we need to set the skinweights in a particular way to make it work)
        """

        # setup the main joint hierarchy
        self.jointsHierarchy = cmds.createNode("transform", name="{}_joints".format(self.name),
                                               parent=self.rootHierarchy)

        self.cornersHierarchy = cmds.createNode("transform", name="{}_corners".format(self.name),
                                                parent=self.rootHierarchy)

        # the first portion of this setup is to build a systemt to wrap the corner of the lips around the teeth.
        # this is accomplished by created a separate hierarchy at the lips joint which aims at the mouth control (giving an expected rotation)
        # however once the rotation reaches a limit the transformation instead becomes a translation

        attr.addSeparator(self.paramsHierarchy, "corners")
        wideLimit = attr.createAttr(self.paramsHierarchy, "rotLimitWide", "float", value=2, minValue=0)
        narrowLimit = attr.createAttr(self.paramsHierarchy, "rotLimitNarrow", "float", value=-2, maxValue=0)

        dummyJoints = list()
        self.cornerSetups = list()
        # first lets build the lipCorner system
        for side in 'lr':
            ctl = self.rCorner if side == 'r' else self.lCorner

            jawConnecter = cmds.createNode("transform", name="{}_setup".format(ctl.name), parent=self.cornersHierarchy)
            transform.matchTransform(ctl.name, jawConnecter)
            setupOffset = hierarchy.create(jawConnecter, hierarchy=["{}_offset".format(jawConnecter)],
                                           matchTransform=True)

            aimTrsOffset = cmds.createNode("transform", name='{}_aimTrs_offset'.format(ctl.name),
                                           parent=jawConnecter)
            aimTrs = cmds.createNode("transform", name='{}_aimTrs'.format(ctl.name), parent=aimTrsOffset)
            transform.matchTranslate(self.input[0], aimTrsOffset)

            # create a duplicate of the corner contorl
            aimDummy = cmds.createNode("transform", name="{}_dummy_trs".format(ctl.name), parent=jawConnecter)
            transform.matchTransform(ctl.name, aimDummy)
            hierarchy.create(aimDummy, hierarchy=["{}_offset".format(aimDummy)], matchTransform=True)

            node.clamp("{}.tx".format(ctl.name), inMin=narrowLimit, inMax=wideLimit, output="{}.tx".format(aimDummy),
                       name=aimDummy)

            # create a temportary aim constraint to orient the offset
            aimVector = (-1, 0, 0) if side == 'r' else (1, 0, 0)
            const = cmds.aimConstraint(ctl.name, aimTrsOffset, aim=aimVector, u=(0, 1, 0), wut='object',
                                       wuo=self.upVector)
            cmds.delete(const)
            cmds.aimConstraint(aimDummy, aimTrs, aim=aimVector, u=(0, 1, 0), wut='object',
                               wuo=self.upVector, skip=['x', 'z'])

            # next we need to make a dummy joint to constrain to
            dummyJoint = cmds.createNode("joint", name="{}_dummy_joint".format(ctl.name), parent=jawConnecter)
            transform.matchTransform(ctl.name, dummyJoint)
            dummyJntOffset = hierarchy.create(dummyJoint, hierarchy=["{}_offset".format(dummyJoint)],
                                              matchTransform=True)
            cmds.parentConstraint(aimTrs, dummyJntOffset, mo=True)

            # now we can build the setup to add translation to the joint
            narrowWideCond = node.condition("{}.tx".format(ctl.name), 0,
                                            ifTrue=[wideLimit, 2, 0],
                                            ifFalse=[narrowLimit, 4, 0],
                                            operation=">",
                                            name="{}_narrowOrWide".format(ctl.name))
            mdl = node.multDoubleLinear("{}.outColorR".format(narrowWideCond), -1, name="{}_neg".format(ctl.name))
            adl = node.addDoubleLinear("{}.tx".format(ctl.name), "{}.output".format(mdl),
                                       name="{}_offset".format(ctl.name))

            translateCondition = node.condition("{}.tx".format(ctl.name), "{}.outColorR".format(narrowWideCond),
                                                ifTrue=["{}.output".format(adl), 0, 0],
                                                ifFalse=[0, 0, 0],
                                                name="{}_translateAddition".format(ctl.name))
            cmds.connectAttr("{}.outColorG".format(narrowWideCond), "{}.{}".format(translateCondition, "operation"))

            # now we can connect to the driver joint
            cmds.connectAttr("{}.outColorR".format(translateCondition), "{}.tx".format(dummyJoint))
            cmds.connectAttr("{}.ty".format(ctl.name), "{}.ty".format(dummyJoint))
            cmds.connectAttr("{}.tz".format(ctl.name), "{}.tz".format(dummyJoint))

            # constrain it to the lips group
            transform.connectOffsetParentMatrix(self.lipsAll.name, setupOffset, mo=True)

            # store important data here to re-use later
            dummyJoints.append(dummyJoint)
            self.cornerSetups.append(jawConnecter)

        # create a a list of driver joints for the lowres curve
        mainJointsList = [dummyJoints[-1], self.uppLips.name, dummyJoints[0], self.lowLips.name]
        self.mainDriverJnts = self.createJointsForCurve(mainJointsList, suffix='main')

        uppLidJoints = self.mainDriverJnts[:3]
        lowLidJoints = [self.mainDriverJnts[0], self.mainDriverJnts[3], self.mainDriverJnts[2]]

        # for theese controls we need to set the skinning method to dual quaternion
        # so that we can get a nice rotationa around the teeth (skinningMethod=1 for DQ skinning)
        cmds.skinCluster(uppLidJoints, self.topLowCurve, dr=1, mi=2, bm=0,
                         name="{}_skinCluster".format(self.topLowCurve), skinMethod=1)
        cmds.skinCluster(lowLidJoints, self.botLowCurve, dr=1, mi=2, bm=0,
                         name="{}_skinCluster".format(self.botLowCurve), skinMethod=1)

        # autoskin the curves! This idea comes from "the art of moving points" to create a great shape for our lowres curve.
        # we can do that by setting the skinweights using the equation: y=-(x-1)^{2.4} +1
        lipsUtil.autoSkinLowCurve(self.topLowCurve, self.mainDriverJnts[0], self.mainDriverJnts[1],
                                  self.mainDriverJnts[2])
        lipsUtil.autoSkinLowCurve(self.botLowCurve, self.mainDriverJnts[0], self.mainDriverJnts[3],
                                  self.mainDriverJnts[2])

    def setupMidCurve(self):
        """ Setup the middle resolution curve """
        # create joints to ride on the curve
        self.connectControlsToCurve(self.mainControls[1:4], self.topLowCurve)
        self.connectControlsToCurve(self.mainControls[5:], self.botLowCurve)

        # create a bunch of driver joints
        midDriverJoints = self.createJointsForCurve(self.mainControls[1:4] + self.mainControls[5:], suffix="mid")

        # bind the joints to the curve
        uppLidJoints = [self.mainDriverJnts[0]] + midDriverJoints[:3] + [self.mainDriverJnts[2]]
        lowLidJoints = [self.mainDriverJnts[0]] + midDriverJoints[3:] + [self.mainDriverJnts[2]]

        cmds.skinCluster(uppLidJoints, self.topMidCurve, dr=1.5, mi=2, bm=0,
                         name="{}_skinCluster".format(self.topMidCurve))
        cmds.skinCluster(lowLidJoints, self.botMidCurve, dr=1.5, mi=2, bm=0,
                         name="{}_skinCluster".format(self.botMidCurve))

        # connect the secondary controls to this curve
        self.connectControlsToCurve(self.subControls[:5], self.topMidCurve)
        self.connectControlsToCurve(self.subControls[5:], self.botMidCurve)

        # add in the orientation for the sub controls
        cmds.parent(self.subControls[0].orig, self.mainControls[0].name)
        lipsUtil.noFlipOrient(self.mainControls[0].name, self.mainControls[1].name, self.subControls[1].trs)
        lipsUtil.noFlipOrient(self.mainControls[1].name, self.mainControls[2].name, self.subControls[2].trs)
        lipsUtil.noFlipOrient(self.mainControls[2].name, self.mainControls[3].name, self.subControls[3].trs)
        lipsUtil.noFlipOrient(self.mainControls[3].name, self.mainControls[4].name, self.subControls[4].trs)
        cmds.parent(self.subControls[5].orig, self.mainControls[4].name)

        lipsUtil.noFlipOrient(self.mainControls[0].name, self.mainControls[5].name, self.subControls[6].trs)
        lipsUtil.noFlipOrient(self.mainControls[5].name, self.mainControls[6].name, self.subControls[7].trs)
        lipsUtil.noFlipOrient(self.mainControls[6].name, self.mainControls[7].name, self.subControls[8].trs)
        lipsUtil.noFlipOrient(self.mainControls[7].name, self.mainControls[4].name, self.subControls[9].trs)

        # create joints for the high curve
        uppControlsForJoints = [self.subControls[0], self.subControls[1], self.mainControls[1], self.subControls[2],
                                self.mainControls[2], self.subControls[3], self.mainControls[3], self.subControls[4],
                                self.subControls[5]]
        lowControlsForJoints = [self.subControls[0], self.subControls[6], self.mainControls[5], self.subControls[7],
                                self.mainControls[6], self.subControls[8], self.mainControls[7], self.subControls[9],
                                self.subControls[5]]

        self.uppSubJoints = self.createJointsForCurve(uppControlsForJoints, suffix='sub')
        self.lowSubJoints = self.createJointsForCurve(lowControlsForJoints[1:-1], suffix='sub')

        # skin the upper and lower driver curves. For the lower curve we'll use the corners from the upper curve to avoid
        # duplicate connections
        cmds.skinCluster(self.uppSubJoints, self.topDriverCurve, dr=1.5, mi=1, bm=0,
                         name="{}_skinCluster".format(self.topDriverCurve))
        cmds.skinCluster([self.uppSubJoints[0]] + self.lowSubJoints + [self.uppSubJoints[-1]], self.botDriverCurve,
                         dr=1.5, mi=1, bm=0, name="{}_skinCluster".format(self.botDriverCurve))

        # finally we need to connect the joints rotation to the control orient
        # here we will use the joint targetLocators to drive the rotation
        self.uppOrtControls = [self.subControls[0], self.subControls[1], self.mainControls[1], self.subControls[2],
                               self.mainControls[2], self.subControls[3], self.mainControls[3], self.subControls[4],
                               self.subControls[5]]
        self.lowOrtControls = [self.subControls[0], self.subControls[6], self.mainControls[5], self.subControls[7],
                               self.mainControls[6], self.subControls[8], self.mainControls[7], self.subControls[9],
                               self.subControls[5]]

        # do the auto weighting for the lip controls
        lipsUtil.autoWeightOrientation(
            sampleCurve=self.topDriverCurve,
            controlsList=self.uppOrtControls,
            jointsList=self.aimTgtList[:self.lipSpans],
            parent=self.targetHierarchy)

        lipsUtil.autoWeightOrientation(
            sampleCurve=self.botDriverCurve,
            controlsList=self.lowOrtControls,
            jointsList=self.aimTgtList[self.lipSpans:],
            parent=self.targetHierarchy)

    def connectControlsToCurve(self, controlsList, targetCurve):
        """ Connect the controls to the curve"""
        for ctl in controlsList:
            targetLoc = cmds.createNode("transform", name="{}_trsTarget".format(ctl.name), p=self.targetHierarchy)
            transform.matchTranslate(ctl.name, targetLoc)

            curve.attatchToCurve(targetLoc, targetCurve)
            constrain.orientConstraint(self.lipsAll.name, targetLoc)

            transform.connectOffsetParentMatrix(targetLoc, ctl.trs, mo=False, r=False, s=False, sh=False)

    def createJointsForCurve(self, controlList, suffix=""):
        """ Create a bunch of joints to use for a curve"""
        driverJoints = list()
        for ctl in controlList:
            if isinstance(ctl, control.Control):
                ctl = ctl.name

            jnt = cmds.createNode("joint", name="{}_{}_driver".format(ctl, suffix), parent=self.jointsHierarchy)
            transform.matchTransform(ctl, jnt)
            transform.connectOffsetParentMatrix(ctl, jnt)

            driverJoints.append(jnt)

        # hide the joints
        joint.hideJoints(driverJoints)

        return driverJoints

    def setupZipperLips(self):
        """ Setup the zipperLips"""
        # if we want to do a zipper lips setup we need to create the curve here before we add the other setup to it
        zipperUppCurveName = "{}_upper_zipper".format(self.name)
        zipperLowCurveName = "{}_lower_zipper".format(self.name)
        zipCurveName = "{}_mid_zipper".format(self.name)

        zipperCurve = cmds.duplicate(self.topDriverCurve, name=zipCurveName)[0]
        zipperUppCurve = cmds.duplicate(self.topDriverCurve, name=zipperUppCurveName)[0]
        zipperLowCurve = cmds.duplicate(self.botDriverCurve, name=zipperLowCurveName)[0]

        self.zipperHierarchy = cmds.createNode("transform", name="{}_zipper".format(self.name),
                                               parent=self.rootHierarchy)

        cmds.setAttr("{}.inheritsTransform".format(self.zipperHierarchy), False)

        # setuo attributes for the zipper
        lZipper = attr.createAttr(self.paramsHierarchy, 'lZipper', "float", minValue=0, maxValue=10, value=0)
        rZipper = attr.createAttr(self.paramsHierarchy, "rZipper", "float", minValue=0, maxValue=10, value=0)

        lZipperFalloff = attr.createAttr(self.paramsHierarchy, 'lZipperFalloff', "float", minValue=0.001, maxValue=10,
                                         value=4)
        rZipperFalloff = attr.createAttr(self.paramsHierarchy, "rZipperFalloff", "float", minValue=0.001, maxValue=10,
                                         value=4)

        # we need to make a duplicate of the high curve so we can drive the joints that move the actull high curve without causing a cycle
        self.zipperJointsHierarchy = cmds.createNode("transform", name="{}_zipper_joints".format(self.name),
                                                     parent=self.zipperHierarchy)

        # create the joints we need for the duplicated hierarchy
        zipUppJointNames = [x.replace("driver", "zipper") for x in self.uppSubJoints]
        zipLowJointNames = [x.replace("driver", "zipper") for x in self.lowSubJoints]
        uppZipperDriverJoints = joint.duplicateChain(self.uppSubJoints, self.zipperJointsHierarchy, zipUppJointNames)
        cmds.parent(uppZipperDriverJoints[1:], self.zipperJointsHierarchy)

        lowZipperDriverJoints = joint.duplicateChain(self.lowSubJoints, self.zipperJointsHierarchy, zipLowJointNames)
        cmds.parent(lowZipperDriverJoints[1:], self.zipperJointsHierarchy)

        # connect them to the controls
        for ctl, jnt in zip(self.uppOrtControls + self.lowOrtControls[1:-1],
                            uppZipperDriverJoints + lowZipperDriverJoints):
            transform.connectOffsetParentMatrix(ctl.name, jnt)

        # skin the duplicates to the curves
        cmds.skinCluster(uppZipperDriverJoints, zipperUppCurve,
                         dr=1.5, mi=1, bm=0, name="{}_skinCluster".format(zipperUppCurve))
        cmds.skinCluster([uppZipperDriverJoints[0]] + lowZipperDriverJoints + [uppZipperDriverJoints[-1]],
                         zipperLowCurve,
                         dr=1.5, mi=1, bm=0, name="{}_skinCluster".format(zipperLowCurve))

        # create zipperLocs
        zipperTargets = list()
        # now we can loop through the top lip joints to create a zipper joint for each child
        for jnt in self.uppSubJoints[1:-1]:
            jntName = jnt.split("_guide")[0]
            jntName = jntName.replace("_upper_", "_mid_")
            jntName = jntName.replace("_upp", "_mid")
            jntName = jntName.replace("_driver", "_zipper")

            targetLoc = cmds.createNode("transform", name="{}_trs".format(jntName), p=self.zipperHierarchy)
            transform.matchTransform(jnt, targetLoc)

            curve.attatchToCurve(targetLoc, curve=zipperCurve, toClosestParam=True)
            zipperTargets.append(targetLoc)

        # setup the zipper blendshape
        self.zipperBlendshape = blendshape.create(zipperCurve, name='{}_zipper'.format(zipperCurve))
        blendshape.addTarget(self.zipperBlendshape, target=zipperUppCurve, targetWeight=0.5)
        blendshape.addTarget(self.zipperBlendshape, target=zipperLowCurve, targetWeight=0.5)

        # setup a blending hierarchy for the zipper joints
        lipsUtil.setupZipperBlending(self.uppSubJoints[1:-1], zipperTargets=zipperTargets)
        lipsUtil.setupZipperBlending(self.lowSubJoints, zipperTargets=zipperTargets)

        # setup the zipper lips
        lipsUtil.setupZipper(
            name=self.name,
            uppJoints=self.uppSubJoints[1:-1],
            lowJoints=self.lowSubJoints,
            paramsHolder=self.paramsHierarchy)

    def setupAnimAttrs(self):
        """ setup the animator parameters"""
        # create a visability control for the ikGimble control
        attr.addSeparator(self.lipsAll.name, "----")
        attr.createAttr(self.lipsAll.name, "tweakers", attributeType='bool', value=0, keyable=False, channelBox=True)
        subControls = [x.name for x in self.subControls]
        control.connectControlVisiblity(self.lipsAll.name, "tweakers", controls=subControls)

    def connect(self):
        """Create the connection to other components """

        if cmds.objExists(self.rigParent):
            # connect the lips all
            transform.connectOffsetParentMatrix(self.rigParent, self.lipsAll.orig, mo=True)

        # connect the up vector to the eyesocket control
        transform.connectOffsetParentMatrix(self.lipsAll.name, self.upVector, mo=True)

        # If we have specified a new jaw then connection then connect it here. The goal here is to add the transform of
        # the jaw to the transform of the lipsAll so that both have full influence of the controls. To do this we will
        # create a simple hierarchy to combine transforms and a local rig to extract the movement of the jaw.
        if self.useJaw:
            jawConnectControls = [self.uppLips, self.lowLips, self.mainControls[4], self.mainControls[0]]

            jawOffsetGroup = cmds.createNode("transform", name="{}_jaw_space".format(self.name),
                                             parent=self.spacesHierarchy)

            # if the rig parent exists connect it to the offset control
            if cmds.objExists(self.rigParent):
                transform.connectOffsetParentMatrix(self.rigParent, jawOffsetGroup)

            for i, ctl in enumerate(jawConnectControls):

                # first we can create the local rig to extract the jaw transformation
                # create an offset transform node
                jawTrs = cmds.createNode("transform", name="{}_jawTrs".format(ctl.name), parent=jawOffsetGroup)
                transform.matchTransform(ctl.name, jawTrs)
                hierarchy.create(jawTrs, hierarchy=["{}_offset".format(jawTrs)], above=True, matchTransform=True)

                # connect the offset transforms to the jaw joints  (Must drive the transforms directly!! use a constraint)
                cmds.parentConstraint(self.jawJoints[i], jawTrs, mo=True)

                # Finally, connect the jaw offsets to the control trs groups. We can use the direct connections here to add
                # the transformation of the jaws to the positions that theyre in from the lipsAll.
                for channel in attr.TRANSLATE + attr.ROTATE:
                    cmds.connectAttr("{}.{}".format(jawTrs, channel), "{}.{}".format(ctl.trs, channel))

                    # if we are on the corners then we need to connect the offsets as well to the jaw translation
                    if i > 1:
                        # we can use the index by subtracting 2 from the index
                        cmds.connectAttr("{}.{}".format(jawTrs, channel),
                                         "{}.{}".format(self.cornerSetups[i - 2], channel))

    def finalize(self):
        """ Finalize the rig setup """
        return

        # hide the curves group
        cmds.setAttr("{}.v".format(self.curvesHierarchy), 0)
        attr.lock(self.curvesHierarchy, attr.TRANSFORMS)