#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: realisticEyelid.py.py
    author: masonsmigel
    date: 11/2022
    discription:  A realistic eyelid component module

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


class Eyelid(rigamajig2.maya.cmpts.base.Base):
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

    def __init__(self, name, input, size=1, rigParent=str(), eyelidSpans=8, addCrease=True,
                 addFleshyEye=True, eyeballJoint=str(),
                 useCreaseFollow=False, uppCreaseDriver=str(), lowCreaseDriver=str()):
        """
        :param name: Component Name
        :param input: A single joint located at the center of the eyeball. This will become the eyeRoot.
        :param size: default size of the controls
        :param rigParent: connect the component to a rigParent
        :param eyelidSpans: The number of spans from the inner corner to the outer corner. (including the corner verts)
                            This will be used to create joints on each span of the lid.
        :param addCrease: if True a second set of joints around the crease of the eyelid will be created.
        :param addFleshyEye: If True an eyeballJoint must be provided and the rotation will drive the eye look
        :param eyeballJoint: Used when adding a fleshy eye setup to drive the fleshy eye
        :param useCreaseFollow: If True setup the crease follows
        :param uppCreaseDriver: The other driver for the upper crease follow. Only the first idex is used.
        :param uppCreaseFollow: The other driver for the lower crease follow. Only the first idex is used.
        """
        super(Eyelid, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['eyelidSpans'] = eyelidSpans
        self.cmptSettings['addCrease'] = addCrease
        self.cmptSettings['addFleshyEye'] = addFleshyEye
        self.cmptSettings['eyeballJoint'] = eyeballJoint

        self.cmptSettings['useCreaseFollow'] = useCreaseFollow
        self.cmptSettings['uppCreaseDriver'] = uppCreaseDriver
        self.cmptSettings['lowCreaseDriver'] = lowCreaseDriver

        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.cmptSettings['eyeSocketName'] = inputBaseNames[0]

    def createBuildGuides(self):
        """Create all build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        socketPos = cmds.xform(self.input[0], q=True, ws=True, t=True)

        # create the up vector
        self.upVectorGuide = control.createGuide(
            "{}_upVecTgt".format(self.name),
            parent=self.guidesHierarchy,
            position=socketPos)

        # create the eyelid guides
        self.uppLidGuideList, self.lowLidGuideList = self._createGuides(part='', startPos=socketPos)

        # create the eyelid control guides
        self.eyelidControllerGuides = self._createCurveGuides(
            part='',
            uppGuides=self.uppLidGuideList,
            lowGuides=self.lowLidGuideList)

        # if we want to create the crease guides do that here
        if self.addCrease:
            # create the crease guides
            self.uppCreaseGuideList, self.lowCreaseGuideList = self._createGuides(
                part="Crease",
                startPos=socketPos,
                offset=1.5,
                color='lightorange')
            # create the crease control guides
            self.creaseControllerGuides = self._createCurveGuides(
                part='Crease',
                uppGuides=self.uppCreaseGuideList,
                lowGuides=self.lowCreaseGuideList)

    def _createGuides(self, part='', startPos=[0, 0, 0], offset=1.0, color='turquoise'):
        """This creates a series of guides to be used for the eyelid or crease"""

        sideMultipler = -1 if self.side == 'r' else 1
        # Here we can caululcate the mid point
        # zowever we eant to reduce the number of eyelid spans by two to remove the corners
        midpoint = (float((self.eyelidSpans - 2) - 1) * 0.5) * GUIDE_SCALE
        guideSize = self.size * GUIDE_SCALE

        parent = cmds.createNode("transform", name='{}_{}_guide'.format(self.name, part), parent=self.guidesHierarchy)

        upperList = list()
        lowerList = list()

        for section in ['upper', 'lower']:
            for x in range(self.eyelidSpans - 2):
                # first we can caluclate the position of the guides at the origin
                # then multiply them by the postion of the socket joint to position them around the eyeball.
                translateX = float(-midpoint + (x * GUIDE_SCALE)) * sideMultipler
                translateY = offset if section == 'upper' else -offset
                localPos = (translateX, translateY, 0)
                guidePos = mathUtils.addVector(localPos, startPos)

                guide = control.createGuide(
                    name="{}_{}{}_{}".format(self.name, section, part, x),
                    parent=parent,
                    position=guidePos,
                    size=guideSize,
                    hideAttrs=['s'],
                    color=color)

                # add the guide to the upper or lower guide list
                if section == 'upper':
                    upperList.append(guide)
                elif section == 'lower':
                    lowerList.append(guide)

        # Create the inner and outer guides.
        # Once again we add the midpointScale to the socket position.
        innCorner = control.createGuide(
            "{}_inn{}_corner".format(self.name, part),
            parent=parent,
            hideAttrs=['s'],
            position=mathUtils.addVector(((-midpoint - GUIDE_SCALE * offset) * sideMultipler, 0, 0), startPos),
            size=guideSize,
            color=color)
        outCorner = control.createGuide(
            "{}_out{}_corner".format(self.name, part),
            parent=parent,
            hideAttrs=['s'],
            position=mathUtils.addVector(((midpoint + GUIDE_SCALE * offset) * sideMultipler, 0, 0), startPos),
            size=guideSize,
            color=color)

        # create a curve through the guide points so we can attatch the eyelid control guides to them!
        uppGuideList = [innCorner] + upperList + [outCorner]
        lowGuideList = [innCorner] + lowerList + [outCorner]

        return uppGuideList, lowGuideList

    def _createCurveGuides(self, part, uppGuides, lowGuides):
        """
        This utility function will create the guides for the eyelid and crease on a curve.
        This code is used to creast the controls on both the eyelid and crease if theyre needed

        While its not great formatting we pass in the list we want to append the controls to in order to use them effectivly later.
        """

        returnList = list()
        uppCurveName = "{}_upper{}_guideCrv".format(self.name, part)
        uppGuideCurve = live.createLiveCurve(uppGuides,
                                             curveName=uppCurveName,
                                             parent=self.guidesHierarchy)

        lowCurveName = "{}_lower{}_guideCrv".format(self.name, part)
        lowGuideCurve = live.createLiveCurve(lowGuides,
                                             curveName=lowCurveName,
                                             parent=self.guidesHierarchy)

        # now create the control guides.
        eyelidControlNames = ['innCorner', 'uppInn', 'upp', 'uppOut', 'outCorner', 'lowInn', 'low', 'lowOut']
        eyelidControlParams = [0, 0.25, 0.5, 0.75, 1, 0.25, 0.5, 0.75]

        hierarchyName = "{}_{}Controls_guides".format(self.name, part)
        lidControlHierarchy = cmds.createNode("transform", name=hierarchyName, p=self.guidesHierarchy)
        for i in range(len(eyelidControlNames)):
            suffix = eyelidControlNames[i]
            guide = control.createGuide("{}_{}{}".format(self.name, suffix, part),
                                        shape='sphere',
                                        size=GUIDE_SCALE,
                                        parent=lidControlHierarchy,
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
                cmds.setAttr("{}.rotateY".format(guide), 180)

            returnList.append(guide)
        return returnList

    def initialHierarchy(self):
        """Build the inital rig hierarchy"""
        super(Eyelid, self).initialHierarchy()

        self.eyeSocket = control.createAtObject(name=self.eyeSocketName,
                                                side=self.side,
                                                shape='eye',
                                                orig=True,
                                                xformObj=self.input[0],
                                                parent=self.controlHierarchy)

        self.lidControls = list()
        for guide in self.eyelidControllerGuides:
            guideName = guide.split("_guide")[0]
            ctl = control.createAtObject(name=guideName,
                                         shape='triangle',
                                         orig=True,
                                         trs=True,
                                         parent=self.eyeSocket.name,
                                         shapeAim='y',
                                         xformObj=guide,
                                         size=GUIDE_SCALE,
                                         hideAttrs=['s', 'v'])
            self.lidControls.append(ctl)

        # if we have a crease then add the creasr controls too
        if self.addCrease:
            self.creaseControls = list()
            for guide in self.creaseControllerGuides:
                guideName = guide.split("_guide")[0]
                ctl = control.createAtObject(name=guideName,
                                             shape='triangle',
                                             orig=True,
                                             sdk=True,
                                             trs=True,
                                             parent=self.eyeSocket.name,
                                             shapeAim='y',
                                             xformObj=guide,
                                             size=GUIDE_SCALE,
                                             color='indigo',
                                             hideAttrs=['s', 'v'])
                self.creaseControls.append(ctl)

    def preRigSetup(self):
        """ Setup the joints and curves neeeded for this eyelid setup"""
        # create the upVector
        self.upVector = cmds.createNode("transform", name="{}_upVec".format(self.name), p=self.spacesHierarchy)
        transform.matchTranslate(self.upVectorGuide, self.upVector)

        # setup the base curves
        self.curvesHierarchy = cmds.createNode("transform", name="{}_curves".format(self.name), p=self.rootHierarchy)

        topHighCurve = "{}_upperLid_high".format(self.name)
        botLowCurve = "{}_lowerLid_high".format(self.name)
        topControlCurveName = "{}_upperLid_low".format(self.name)
        botControlCurveName = "{}_lowerLid_low".format(self.name)
        blinkCurveName = "{}_blink_low".format(self.name)
        topBlinkCurveName = "{}_upperLid_blink".format(self.name)
        botBlinkCurveName = "{}_lowerLid_blink".format(self.name)

        self.topDriverCruve = curve.createCurveFromTransform(
            self.uppLidGuideList,
            degree=1,
            name=topHighCurve,
            parent=self.curvesHierarchy)
        self.botDriverCurve = curve.createCurveFromTransform(
            self.lowLidGuideList,
            degree=1,
            name=botLowCurve,
            parent=self.curvesHierarchy)

        # create the low-res curves
        self.topLowCurve = cmds.duplicate(self.topDriverCruve, name=topControlCurveName)[0]
        cmds.rebuildCurve(self.topLowCurve, spans=4, degree=3, fitRebuild=True)

        self.botLowCurve = cmds.duplicate(self.botDriverCurve, name=botControlCurveName)[0]
        cmds.rebuildCurve(self.botLowCurve, spans=4, degree=3, fitRebuild=True)

        # create the blink curves

        # # to build a better blink system we will make a nuteral blink curve to use as a base for the inbetween.
        tempBlinkCurve = cmds.duplicate(self.topDriverCruve, name="self.tmpBlinkCurve")[0]
        tempBshp = blendshape.create(tempBlinkCurve, targets=[self.topDriverCruve, self.botDriverCurve])
        for target in blendshape.getTargetList(tempBshp):
            cmds.setAttr("{}.{}".format(tempBshp, target), 0.5)
        cmds.delete(tempBlinkCurve, ch=True)
        cmds.rebuildCurve(tempBlinkCurve, kcp=True, degree=3)

        # smooth out this curve. we can use it ad an inbetween to the blendshape targets! then parent them to the hierarchy
        cmds.smoothCurve("{}.cv[*]".format(tempBlinkCurve), smoothness=10)
        self.blinkCurve = cmds.rebuildCurve(tempBlinkCurve, spans=4, degree=3, rpo=False, name=blinkCurveName)[0]
        self.uppBlinkCurve = cmds.rebuildCurve(tempBlinkCurve, kcp=True, degree=1, rpo=False, name=topBlinkCurveName)[0]
        self.lowBlinkCurve = cmds.rebuildCurve(tempBlinkCurve, kcp=True, degree=1, rpo=False, name=botBlinkCurveName)[0]
        cmds.parent(self.blinkCurve, self.uppBlinkCurve, self.lowBlinkCurve, self.curvesHierarchy)

        # now we can delete the temp blink curve
        cmds.delete(tempBlinkCurve)

        # When using the point on curve info node to drive the translation of transforms
        # its easier to ensure they dont inherit any transforms than to negate the parent transform.
        # For this case we will use a series of locators to drive the rotation of the eyelid joints.
        self.aimLocHierarchy = cmds.createNode("transform", name="{}_aimTgts".format(self.name), p=self.rootHierarchy)
        cmds.setAttr("{}.inheritsTransform".format(self.aimLocHierarchy), False)

        # setup the joints for the eyelid
        # we can do this by looping through the upperGuide and lowerGuide lists
        # (skipping the first and last index of the lower lid)
        for guide in self.uppLidGuideList + self.lowLidGuideList[1:-1]:
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

            targetCurve = self.botDriverCurve if 'lower' in guideName else self.topDriverCruve
            curve.attatchToCurve(aimLoc, curve=targetCurve, toClosestParam=True)

            # aim the joint to the targetloc
            cmds.aimConstraint(aimLoc, baseJoint, aimVector=(1, 0, 0), upVector=(0, 1, 0),
                               worldUpType='object', worldUpObject=self.upVector)

        if self.addCrease:
            # build the crease curve and driver curve

            topCreaseHighCurve = "{}_upperCreaseLid_high".format(self.name)
            botCreaseLowCurve = "{}_lowerCreaseLid_high".format(self.name)
            topCreaseControlCurveName = "{}_upperCreaseLid_low".format(self.name)
            botCreaseControlCurveName = "{}_lowerCreaseLid_low".format(self.name)

            self.topCreaseDriverCruve = curve.createCurveFromTransform(
                self.uppCreaseGuideList,
                degree=1,
                name=topCreaseHighCurve,
                parent=self.curvesHierarchy)
            self.botCreaseDriverCurve = curve.createCurveFromTransform(
                self.lowCreaseGuideList,
                degree=1,
                name=botCreaseLowCurve,
                parent=self.curvesHierarchy)

            # create the low-res curves
            self.topCreaseLowCurve = cmds.duplicate(self.topCreaseDriverCruve,
                                                    name=topCreaseControlCurveName)[0]
            cmds.rebuildCurve(self.topCreaseLowCurve, spans=4, degree=3, fitRebuild=True)

            self.botCreaseLowCurve = cmds.duplicate(self.botCreaseDriverCurve,
                                                    name=botCreaseControlCurveName)[0]
            cmds.rebuildCurve(self.botCreaseLowCurve, spans=4, degree=3, fitRebuild=True)

            # if using crease create joints for that
            for guide in self.uppCreaseGuideList + self.lowCreaseGuideList[1:-1]:
                guideName = guide.split("_guide")[0]

                # create joints... they need to be parented into the bind hierarchy.
                endJoint = cmds.createNode("joint", name="{}_bind".format(guideName), p=self.input[0])
                transform.matchTranslate(guide, endJoint)
                joint.setRadius([baseJoint, endJoint], GUIDE_SCALE)
                meta.tag(endJoint, "bind")

                # much like the eyelid we need an offset. Instead of aiming here we will just connect the translate
                targetLoc = cmds.createNode("transform", name="{}_trsTarget".format(guideName), p=self.aimLocHierarchy)
                transform.matchTranslate(guide, targetLoc)

                targetCurve = self.botCreaseDriverCurve if 'lower' in guideName else self.topCreaseDriverCruve
                curve.attatchToCurve(targetLoc, curve=targetCurve, toClosestParam=True)
                constrain.orientConstraint(self.eyeSocket.name, targetLoc)

                joint.connectChains([targetLoc], [endJoint], connectScale=False)

    def rigSetup(self):
        """ create the main rig setup """
        # connect the eyesocket control to the eyesocket joint
        joint.connectChains([self.eyeSocket.name], [self.input[0]])

        # setup the blink system
        self.setupBlink()

        # setup eyelidControls
        self.jointsHierarchy = cmds.createNode("transform", name="{}_joints".format(self.name),
                                               parent=self.rootHierarchy)

        self.setupDriverCurve(
            controls=self.lidControls,
            uppCurve=self.topLowCurve,
            lowCurve=self.botLowCurve,
            prefix='Lid')
        # self.setupEyelidControls()

        if self.addFleshyEye:
            self.setupFleshyEye()

        # if add crease
        if self.addCrease:
            wire1, _ = cmds.wire(self.topCreaseDriverCruve, wire=self.topCreaseLowCurve,
                                 dds=[0, 5], name="{}_wire".format(self.topDriverCruve))
            wire2, _ = cmds.wire(self.botCreaseDriverCurve, wire=self.botCreaseLowCurve,
                                 dds=[0, 5], name="{}_wire".format(self.botDriverCurve))

            # now we need to set the scale for all the wires. This prevents them from scaling weirdly.
            # it will slightly alter the shape of the curves, but since we do it before the bind it wont affect the model!
            for wire in [wire1, wire2]:
                cmds.setAttr("{}.scale[0]".format(wire), 0)

            self.setupDriverCurve(
                controls=self.creaseControls,
                uppCurve=self.topCreaseLowCurve,
                lowCurve=self.botCreaseLowCurve,
                prefix="Crease")

    def setupBlink(self):
        """ Setup the blink"""

        # setup the blink wires.
        wire1, _ = cmds.wire(self.topDriverCruve, wire=self.topLowCurve,
                             dds=[0, 5], name="{}_wire".format(self.topDriverCruve))
        wire2, _ = cmds.wire(self.botDriverCurve, wire=self.botLowCurve,
                             dds=[0, 5], name="{}_wire".format(self.botDriverCurve))
        wire3, _ = cmds.wire(self.uppBlinkCurve, wire=self.blinkCurve,
                             dds=[0, 5], name="{}_wire".format(self.uppBlinkCurve))
        wire4, _ = cmds.wire(self.lowBlinkCurve, wire=self.blinkCurve,
                             dds=[0, 5], name="{}_wire".format(self.lowBlinkCurve))

        # now we need to set the scale for all the wires. This prevents them from scaling weirdly.
        # it will slightly alter the shape of the curves, but since we do it before the bind it wont affect the model!
        for wire in [wire1, wire2, wire3, wire4]:
            cmds.setAttr("{}.scale[0]".format(wire), 0)

        # create a blendshape for the control curve.
        self.blinkBlendshape = blendshape.create(self.blinkCurve, name='{}_blink'.format(self.blinkCurve))
        blendshape.addTarget(self.blinkBlendshape, target=self.botLowCurve, targetWeight=1)
        blendshape.addTarget(self.blinkBlendshape, target=self.topLowCurve, targetWeight=1)

        # Do the blink setup. Here we neeed to drive the upper and lower curves by the blink height and its inverse.
        bshpTargets = blendshape.getTargetList(self.blinkBlendshape)
        blinkAttr = attr.createAttr(self.paramsHierarchy, "blink", "float", value=0, minValue=0, maxValue=1)
        heightAttr = attr.createAttr(self.paramsHierarchy, "blinkHeight", "float", value=0.15, minValue=0, maxValue=1)

        lowBlinkMdl = node.multDoubleLinear(heightAttr, -1, name="{}_blinkHeightReverse".format(self.name))
        lowBlinkAdl = node.addDoubleLinear("{}.{}".format(lowBlinkMdl, "output"), 1, name="{}_height".format(self.name))

        cmds.connectAttr("{}.{}".format(lowBlinkAdl, "output"), "{}.{}".format(self.blinkBlendshape, bshpTargets[0]))
        cmds.connectAttr(heightAttr, "{}.{}".format(self.blinkBlendshape, bshpTargets[1]))

        # create the blendshapes to trigger the blinks
        uppBlinkBshp = blendshape.create(self.topDriverCruve, targets=self.uppBlinkCurve,
                                         name="{}_blink".format(self.topDriverCruve))
        lowBlinkBshp = blendshape.create(self.botDriverCurve, targets=self.lowBlinkCurve,
                                         name="{}_blink".format(self.botDriverCurve))

        # finally connect the blink the envelope of the blendshape to control when the eyes blink.
        cmds.connectAttr(blinkAttr, "{}.{}".format(uppBlinkBshp, blendshape.getTargetList(uppBlinkBshp)[0]))
        cmds.connectAttr(blinkAttr, "{}.{}".format(lowBlinkBshp, blendshape.getTargetList(lowBlinkBshp)[0]))

        # To create a smooth transitional curve between the top and bottom we will add a smooth node to the blink curve.
        # the smoothness will be multiplied by the blink height to get a smooth on and off as we approach
        # the upper and lower lids we need to turn off the smoothness
        smoothCurveNode = "{}_smoothCurve".format(self.blinkCurve)
        tempSmooth = cmds.smoothCurve("{}.cv[*]".format(self.blinkCurve), s=10, ch=True)[-1]
        cmds.rename(tempSmooth, smoothCurveNode)

        # create a remap value node and use it to create a smooth transition for the smoothness multiplier
        smoothness = attr.createAttr(self.paramsHierarchy, "blinkSmoothness", "float", value=10, minValue=0,
                                     maxValue=100)
        remapValue = node.remapValue(heightAttr, inMin=0, inMax=1, outMin=0, outMax=1,
                                     name="{}_smooth".format(self.name))

        # here we need to set the attributes for the graph. This will create the type of interolation we need.
        # we will set the value 0=0, 0.5=1, and 1=0. this will turn off the smoothness as it touches the lids but
        # it will be full strength at the middle point.
        interpDict = {"0": [0.0, 0.0, 3], "1": [0.5, 1.0, 3], "2": [1.0, 0.0, 3]}
        for i in interpDict.keys():
            cmds.setAttr(remapValue + '.value[{}].value_Position'.format(i), interpDict[i][0])
            cmds.setAttr(remapValue + '.value[{}].value_FloatValue'.format(i), interpDict[i][1])
            cmds.setAttr(remapValue + '.value[{}].value_Interp'.format(i), interpDict[i][2])

        mdl = node.multDoubleLinear(smoothness, "{}.{}".format(remapValue, "outValue"),
                                    name="{}_smooth".format(self.name))
        cmds.connectAttr("{}.{}".format(mdl, "output"), "{}.{}".format(smoothCurveNode, "smoothness"))

        # turn off inherit transform on all curves. This will prevent any double transforms when moving the global control.
        cmds.setAttr("{}.inheritsTransform".format(self.curvesHierarchy), False)

    def setupDriverCurve(self, controls, uppCurve, lowCurve, prefix=''):
        """
        Setup the driver curve system. This can be used on both the eyelid and creases
        :param controls:
        :param uppCurve:
        :param lowCurve:
        :return:
        """
        driverJoints = list()
        for ctl in controls:
            jnt = cmds.createNode("joint", name=ctl.name + "_driver", parent=self.jointsHierarchy)
            transform.matchTransform(ctl.name, jnt)
            transform.connectOffsetParentMatrix(ctl.name, jnt)

            driverJoints.append(jnt)

        # bind the top lid
        uppLidJoints = driverJoints[:5]
        lowLidJoints = [driverJoints[0]] + driverJoints[5:] + [driverJoints[4]]

        cmds.skinCluster(uppLidJoints, uppCurve, dr=1, mi=2, bm=0, name="{}_skinCluster".format(uppCurve))
        cmds.skinCluster(lowLidJoints, lowCurve, dr=1, mi=2, bm=0, name="{}_skinCluster".format(lowCurve))

        # hide the joints
        joint.hideJoints(driverJoints)

        # setup the constraint relationship between the eyelid and

        uppLidFollow = attr.createAttr(self.paramsHierarchy, "upp{}TweakFollow".format(prefix), "float", minValue=0,
                                       maxValue=1, value=0.8)
        lowLidFollow = attr.createAttr(self.paramsHierarchy, "low{}TweakFollow".format(prefix), "float", minValue=0,
                                       maxValue=1, value=0.8)

        # create some parent constraints for the eyelid controls
        blend1 = transform.blendedOffsetParentMatrix(controls[0].name, controls[2].name, controls[1].trs, mo=True)
        blend2 = transform.blendedOffsetParentMatrix(controls[4].name, controls[2].name, controls[3].trs, mo=True)
        blend3 = transform.blendedOffsetParentMatrix(controls[0].name, controls[6].name, controls[5].trs, mo=True)
        blend4 = transform.blendedOffsetParentMatrix(controls[4].name, controls[6].name, controls[7].trs, mo=True)

        cmds.connectAttr(uppLidFollow, "{}.envelope".format(blend1))
        cmds.connectAttr(uppLidFollow, "{}.envelope".format(blend2))
        cmds.connectAttr(lowLidFollow, "{}.envelope".format(blend3))
        cmds.connectAttr(lowLidFollow, "{}.envelope".format(blend4))

    def setupFleshyEye(self):
        """ Setup teh fleshy eye system"""

        if not cmds.objExists(self.eyeballJoint):
            raise Exception("The eyeball joint '{}' does not exist".format(self.eyeballJoint))

        # create the fleshy eye reader
        aimAxis = transform.getAimAxis(self.eyeballJoint)
        upAxis = transform.getClosestAxis(self.eyeballJoint, target=self.upVector)

        if not aimAxis == 'z' and not upAxis == "y":
            cmds.warning("Eyeball joints should be oriented in world space. Skipping fleshy eyelid setup")
            return

        fleshyEyeAttr = attr.createAttr(self.paramsHierarchy, "fleshyEye", "float", value=1, minValue=0, maxValue=1)

        # create an offset to store the rotation between the eyesocket and eyeball joints.
        # This is important to ensuring the eyes move in a predicatble direction.
        fleshyEyeOffset = cmds.createNode("transform", name="{}_fleshyOffset".format(self.name), p=self.eyeSocket.name)
        transform.matchTransform(self.eyeballJoint, fleshyEyeOffset)
        # create separate drivers for the upper and lower lids
        for part in ['upper', 'lower']:
            # build a reader node
            readerName = "{}_{}_fleshy_reader".format(self.name, part)
            eyeReader = cmds.createNode("transform", name=readerName, p=fleshyEyeOffset)
            transform.matchTransform(self.eyeballJoint, eyeReader)

            followRX = attr.createAttr(self.paramsHierarchy, "{}FollowRx".format(part), "float", value=.3, minValue=0,
                                       maxValue=1)
            followRY = attr.createAttr(self.paramsHierarchy, "{}FollowRy".format(part), "float", value=.3, minValue=0,
                                       maxValue=1)

            multName = "{}_{}_fleshyFollow".format(self.name, part)
            fleshySwitchName = "{}_{}_fleshySwitch".format(self.name, part)
            mult = node.multiplyDivide("{}.r".format(self.eyeballJoint), [followRX, followRY, 0], name=multName)
            fleshySwitch = node.multiplyDivide("{}.output".format(mult), [fleshyEyeAttr, fleshyEyeAttr, fleshyEyeAttr],
                                               name=fleshySwitchName)
            cmds.connectAttr("{}.output".format(fleshySwitch), "{}.r".format(eyeReader))

            # connect the reader to the eyeball
            eyelidControl = self.lidControls[2] if part == "upper" else self.lidControls[6]
            transform.connectOffsetParentMatrix(eyeReader, eyelidControl.trs, mo=True, t=True, r=False, s=False)

    def setupAnimAttrs(self):
        """Setup animation attributes."""
        attr.addSeparator(self.eyeSocket.name, "----")
        attr.driveAttribute("blink", self.paramsHierarchy, self.eyeSocket.name)
        attr.driveAttribute("blinkHeight", self.paramsHierarchy, self.eyeSocket.name)

        # setup the upper lid
        attr.addSeparator(self.lidControls[2].name, "----")
        attr.moveAttribute("uppLidTweakFollow", self.paramsHierarchy, self.lidControls[2].name)

        # setup the lower lid
        attr.addSeparator(self.lidControls[6].name, "----")
        attr.moveAttribute("lowLidTweakFollow", self.paramsHierarchy, self.lidControls[6].name)

        # setup the upper lid
        attr.addSeparator(self.creaseControls[2].name, "----")
        attr.moveAttribute("uppCreaseTweakFollow", self.paramsHierarchy, self.creaseControls[2].name)

        # setup the lower lid
        attr.addSeparator(self.creaseControls[6].name, "----")
        attr.moveAttribute("lowCreaseTweakFollow", self.paramsHierarchy, self.creaseControls[6].name)

        # setup controlVisabilities
        attr.createAttr(self.eyeSocket.name, "crease", attributeType='bool', value=1, keyable=False, channelBox=True)
        control.connectControlVisiblity(self.eyeSocket.name, "crease",
                                        controls=[ctl.name for ctl in self.creaseControls])

    def connect(self):
        """connect to the rig parent"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            # connect the eyesocket
            transform.connectOffsetParentMatrix(self.rigParent, self.eyeSocket.orig, mo=True)

            # connect the up vector to the eyesocket control
            transform.connectOffsetParentMatrix(self.eyeSocket.name, self.upVector, mo=True)

        # if we're using the crease follow and have a crease then connect the crease follow
        if self.addCrease and self.useCreaseFollow:
            self.setupCreaseFollows()

    def setupCreaseFollows(self):
        """Build the crease follow stuff"""

        for part in ['upp', 'low']:
            creaseDriver = self.uppCreaseDriver if part == 'upp' else self.lowCreaseDriver
            # if the string is empty then we can display a wanring and skip this
            if creaseDriver == '':
                cmds.warning("Must provide a crease driver to useCreaseFollow")
                return

            creaseHierachy = cmds.createNode("transform", name="{}_{}CreaseFollow".format(self.name, part),
                                             parent=self.spacesHierarchy)

            # create a trs node to get the position of the curve then attatch it to the curve
            lidTrsName = "{}_{}CreaseFollow_lid_trs".format(self.name, part)
            lidTrs = cmds.createNode("transform", name=lidTrsName, parent=creaseHierachy)
            cmds.setAttr("{}.inheritsTransform".format(lidTrs), False)

            lidControl = self.lidControls[2] if part == 'upp' else self.lidControls[6]
            creaseControl = self.creaseControls[2] if part == 'upp' else self.creaseControls[6]
            lidCurve = self.topDriverCruve if part == 'upp' else self.botDriverCurve
            transform.matchTransform(lidControl.name, lidTrs)
            curve.attatchToCurve(lidTrs, curve=lidCurve, toClosestParam=True)

            # add an attribute to drive the bias fo the crease
            creaseBiasAttr = attr.createAttr(self.paramsHierarchy, "{}CreaseBias".format(part), "float",
                                             value=0.5, minValue=0, maxValue=1)

            # now build a trs to store the positon of the lidTrs and the creaseDriver
            creaseTrsName = "{}_{}CreaseFollow_out_trs".format(self.name, part)
            outputTrs = cmds.createNode("transform", name=creaseTrsName, parent=creaseHierachy)
            transform.matchTransform(creaseControl.name, outputTrs)
            creaseBlend = transform.blendedOffsetParentMatrix(lidTrs, creaseDriver, outputTrs, mo=True, blend=0.5)
            cmds.connectAttr(creaseBiasAttr, "{}.envelope".format(creaseBlend))

            # connect the outputTrs into the creaseTrs node and add a blend so we can turn it on or off
            mm, pick = transform.connectOffsetParentMatrix(outputTrs, creaseControl.trs,
                                                           mo=True, t=True, r=False, s=False, sh=False)

            blend = cmds.createNode("blendMatrix", name="{}_{}creaseFollow_blendMatrix".format(self.name, part))
            cmds.connectAttr("{}.outputMatrix".format(pick), "{}.target[0].targetMatrix".format(blend))
            cmds.connectAttr("{}.outputMatrix".format(blend), "{}.offsetParentMatrix".format(creaseControl.trs), f=True)

            # add the crease follow attribute to the lidControl.
            followAttr = attr.createAttr(lidControl.name, "creaseFollow", "float", value=1, minValue=0, maxValue=1)
            cmds.connectAttr(followAttr, "{}.envelope".format(blend))

    def finalize(self):
        """ Finalize the rig setup """
        # hide the curves group
        cmds.setAttr("{}.v".format(self.curvesHierarchy), 0)
        attr.lock(self.curvesHierarchy, attr.TRANSFORMS)
