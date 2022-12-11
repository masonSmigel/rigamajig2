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

    def __init__(self, name, input, size=1, rigParent=str(), lipSpans=17, useJaw=False, jawJoints=None):
        """
        :param name: Component Name
        :param input: a single joint this will be the pivot where the lips rotate around
        :param size: default size of the controls
        :param rigParent: connect the component to a rigParent
        :param lipSpans: The number of spans from the right corner to the left corner.
        :param useJaw: If true connect the setup to the jaw
        :param jawJoints:  If useJaw then provide the following joints to the jaw:
                            [lipsTop, lipsBot, lips_l, lips_r]
        """
        super(Lips, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['lipSpans'] = lipSpans
        self.cmptSettings['useJaw'] = useJaw
        self.cmptSettings['jawJoints'] = jawJoints or list()

        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.cmptSettings['lipsAllName'] = inputBaseNames[0]

    def createBuildGuides(self):
        """ create all build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        lipsPos = cmds.xform(self.input[0], q=True, ws=True, t=True)

        self.upperLipGuide = control.createGuide(name="{}_uppLipAll".format(self.name),
                                                 parent=self.guidesHierarchy,
                                                 hideAttrs=['s'],
                                                 position=lipsPos,
                                                 size=self.size * (GUIDE_SCALE *2),
                                                 )
        self.lowerLipGuide = control.createGuide(name="{}_lowLipAll".format(self.name),
                                                 parent=self.guidesHierarchy,
                                                 hideAttrs=['s'],
                                                 position=lipsPos,
                                                 size=self.size * (GUIDE_SCALE *2),
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

        uppSubControlNames = ['r_uppCorner', 'r_uppOut', 'r_uppInn',
                              'l_uppInn', 'l_uppOut', 'l_uppCorner', ]

        lowSubControlNames = ['r_lowCorner', 'r_lowOut', 'r_lowInn',
                              'l_lowInn', 'l_lowOut', 'l_lowCorner']

        subControlParams = [0.08, 0.16, 0.375,
                            0.625, 0.84, 0.92]

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

        # # build the subControls
        # self.subControls = list()
        # for guide in self.subControlGuides:
        #     guideName = guide.split("_guide")[0] + "Tweak"
        #     ctl = control.createAtObject(name=guideName,
        #                                  shape='triangle',
        #                                  orig=True,
        #                                  trs=True,
        #                                  parent=self.lipsAll.name,
        #                                  shapeAim='y',
        #                                  xformObj=guide,
        #                                  size=GUIDE_SCALE,
        #                                  color='lightblue',
        #                                  hideAttrs=['s', 'v'])
        #     self.subControls.append(ctl)

    def preRigSetup(self):
        """ Setup the joints and curves needed for the setup"""

        self.curvesHierarchy = cmds.createNode("transform", name="{}_curves".format(self.name), p=self.rootHierarchy)
        cmds.setAttr("{}.inheritsTransform".format(self.curvesHierarchy), False)

        topHighCurve = "{}_upperLip_high"
        botHighCurve = "{}_lowerLip_high"

        topMidCurve = "{}_upperLip_low".format(self.name)
        botMidName = "{}_lowerLip_low".format(self.name)

        topMidCurveName = "{}_upperLip_low".format(self.name)
        botMidCurveName = "{}_lowerLip_low".format(self.name)

        self.topDriverCruve = curve.createCurveFromTransform(
            self.upperGuideList,
            degree=1,
            name=topHighCurve,
            parent=self.curvesHierarchy)

        self.botDriverCurve = curve.createCurveFromTransform(
            self.lowerGuideList,
            degree=1,
            name=botHighCurve,
            parent=self.curvesHierarchy)

        self.topLowCurve = cmds.duplicate(self.topDriverCruve, name=topMidCurve)[0]
        cmds.rebuildCurve(self.topLowCurve, spans=4, degree=3, fitRebuild=True)

        self.botLowCurve = cmds.duplicate(self.botDriverCurve, name=botMidName)[0]
        cmds.rebuildCurve(self.botLowCurve, spans=4, degree=3, fitRebuild=True)

        # build the subControlCurves

        # setup joints for each span of the lips
        self.targetHierarchy = cmds.createNode("transform", name="{}_aimTgts".format(self.name), p=self.rootHierarchy)
        cmds.setAttr("{}.inheritsTransform".format(self.targetHierarchy), False)

        # setup the joints for the eyelid
        # we can do this by looping through the upperGuide and lowerGuide lists
        # (skipping the first and last index of the lower lid)
        for guide in self.upperGuideList + self.lowerGuideList[1:-1]:
            guideName = guide.split("_guide")[0]

            endJoint = cmds.createNode("joint", name="{}_bind".format(guideName), p=self.input[0])
            transform.matchTranslate(guide, endJoint)
            joint.setRadius([endJoint], GUIDE_SCALE)
            meta.tag(endJoint, "bind")

            targetLoc = cmds.createNode("transform", name="{}_trsTarget".format(guideName), p=self.targetHierarchy)
            transform.matchTranslate(guide, targetLoc)

            targetCurve = self.botDriverCurve if 'lower' in guideName else self.topDriverCruve
            curve.attatchToCurve(targetLoc, curve=targetCurve, toClosestParam=True)
            # cmds.tangentConstraint(self.driverCurve, targetLoc, aim=(1, 0, 0), u=(0,1,0))
            constrain.orientConstraint(self.lipsAll.name, targetLoc)

            joint.connectChains([targetLoc], [endJoint])





    def rigSetup(self):
        """ create the main rig setup """

        joint.connectChains([self.lipsAll.name], [self.input[0]])

        # setup the main joint hierarchy
        self.jointsHierarchy = cmds.createNode("transform", name="{}_joints".format(self.name),
                                               parent=self.rootHierarchy)

        # build the main control curve
        self.setupMainCurve()

        # TODO: remove this later. This is just temporary
        wire1, _ = cmds.wire(self.topDriverCruve, wire=self.topLowCurve,
                             dds=[0, 5], name="{}_wire".format(self.topDriverCruve))
        wire2, _ = cmds.wire(self.botDriverCurve, wire=self.botLowCurve,
                             dds=[0, 5], name="{}_wire".format(self.botDriverCurve))
        for wire in [wire1, wire2]:
            cmds.setAttr("{}.scale[0]".format(wire), 0)

    def setupMainCurve(self):
        """ Setup a main curve"""

        # We need to create joints along each main control to influence the low Curve
        driverJoints = list()
        for ctl in self.mainControls:
            jnt = cmds.createNode("joint", name=ctl.name + "_driver", parent=self.jointsHierarchy)
            transform.matchTransform(ctl.name, jnt)
            transform.connectOffsetParentMatrix(ctl.name, jnt)

            driverJoints.append(jnt)

        uppLidJoints = driverJoints[:5]
        lowLidJoints = [driverJoints[0]] + driverJoints[5:] + [driverJoints[4]]

        cmds.skinCluster(uppLidJoints, self.topLowCurve, dr=1, mi=2, bm=0,
                         name="{}_skinCluster".format(self.topLowCurve))
        cmds.skinCluster(lowLidJoints, self.botLowCurve, dr=1, mi=2, bm=0,
                         name="{}_skinCluster".format(self.botLowCurve))

        # hide the joints
        joint.hideJoints(driverJoints)

        # setup the constraint relationship between the inner and outer mouth and
        cornerFollow = attr.createAttr(self.paramsHierarchy, "cornerFollow", "float", minValue=0, maxValue=1, value=0.2)

        cornerFollowReverse = node.reverse(cornerFollow, name="{}_uppFollow".format(self.name))

        # create a system of parent contraints for the lip controls
        rCorner = self.mainControls[0]
        lCorner = self.mainControls[4]
        const1 = cmds.parentConstraint(self.uppLips.name, rCorner.name, self.mainControls[1].orig, mo=True)
        const2 = cmds.parentConstraint(self.uppLips.name, lCorner.name, self.mainControls[3].orig, mo=True)
        const3 = cmds.parentConstraint(self.lowLips.name, rCorner.name, self.mainControls[5].orig, mo=True)
        const4 = cmds.parentConstraint(self.lowLips.name, lCorner.name, self.mainControls[7].orig, mo=True)

        cmds.parentConstraint(self.uppLips.name, self.mainControls[2].orig, mo=True)
        cmds.parentConstraint(self.lowLips.name, self.mainControls[6].orig, mo=True)

        # setup the target weight inputs and reverse nodes.
        for const in [const1, const2, const3, const4]:
            cmds.connectAttr(cornerFollow, "{}.w1".format(const[0]))
            cmds.connectAttr("{}.outputX".format(cornerFollowReverse), "{}.w0".format(const[0]))

    def connect(self):
        """Create the connection to other components """

        # If we have specified a new jaw then connection then connect it here. The goal here is to add the transform of
        # the jaw to the transform of the lipsAll so that both have full influence of the controls. To do this we will
        # create a simple hierarchy to combine transforms and a local rig to extract the movement of the jaw.
        if self.useJaw:

            jawConnectControls = [self.uppLips, self.lowLips, self.mainControls[0], self.mainControls[4]]

            jawOffsetGroup = cmds.createNode("transform", name="{}_jaw_space".format(self.name), parent=self.spacesHierarchy)

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

