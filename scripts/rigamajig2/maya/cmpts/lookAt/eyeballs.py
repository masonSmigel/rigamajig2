#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: eyeballs.py
    author: masonsmigel
    date: 12/2022
    discription: eyeballs component. This is a subclass of the lookAt component but with some attributes for the iris and pupil

"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.lookAt.lookAt
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import live
from rigamajig2.maya import hierarchy
from rigamajig2.maya import transform
from rigamajig2.maya import attr
from rigamajig2.maya import meta
from rigamajig2.maya import joint
from rigamajig2.maya import node
from rigamajig2.maya import mathUtils

IRIS_PERCENT = 0.9
PUPIL_PERCENT = 0.8


class Eyeballs(rigamajig2.maya.cmpts.lookAt.lookAt.LookAt):
    """
    The eyeballs component is a Sublcass of the lookAt component but it has extra options for the iris and pupil scaling
    """

    def __init__(self, name, input, size=1, rigParent=str(), lookAtSpaces=None, rigParentList=None):
        super(Eyeballs, self).__init__(name=name, input=input, size=size, rigParent=rigParent,
                                       lookAtSpaces=lookAtSpaces, rigParentList=rigParentList)

    def createBuildGuides(self):
        super(Eyeballs, self).createBuildGuides()

        # add guides for the pupil and iris
        for inputJoint in self.input:
            inputChild = hierarchy.getChild(inputJoint)
            irisGuide = control.createGuide("{}_iris".format(inputJoint), parent=self.guidesHierarchy)
            pupilGuide = control.createGuide("{}_pupil".format(inputJoint), parent=self.guidesHierarchy)

            # orient the guides
            cmds.orientConstraint(inputJoint, irisGuide, mo=False)
            cmds.orientConstraint(inputJoint, pupilGuide, mo=False)

            # lock the unneeded attributes
            live.slideBetweenTransforms(irisGuide, inputJoint, inputChild, defaultValue=IRIS_PERCENT)
            live.slideBetweenTransforms(pupilGuide, inputJoint, inputChild, defaultValue=PUPIL_PERCENT)

            # lock the transforms
            attr.lockAndHide([irisGuide, pupilGuide], attr.TRANSFORMS)

            setattr(self, "{}_irisGuide".format(inputJoint), irisGuide)
            setattr(self, "{}_pupilGuide".format(inputJoint), pupilGuide)

    def preRigSetup(self):
        """ We'll use the preRigSetup to build the joints for the pupil and iris"""

        for inputJoint in self.input:
            irisGuide = getattr(self, "{}_irisGuide".format(inputJoint))
            pupilGuide = getattr(self, "{}_pupilGuide".format(inputJoint))

            irisGuideName = irisGuide.split("_guide")[0]
            pupilGuideName = pupilGuide.split("_guide")[0]

            # create the joints for the iris
            irisJoint = cmds.createNode("joint", name="{}_bind".format(irisGuideName), p=inputJoint)
            transform.matchTranslate(irisGuide, irisJoint)

            # create the joints for the pupil
            pupilJoint = cmds.createNode("joint", name="{}_bind".format(pupilGuideName), p=inputJoint)
            transform.matchTranslate(pupilGuide, pupilJoint)

            # set some attributes on the joint
            meta.tag([irisJoint, pupilJoint], "bind")
            joint.toOrientation([irisJoint, pupilJoint])

            setattr(self, "{}_irisJoint".format(inputJoint), irisJoint)
            setattr(self, "{}_pupilJoint".format(inputJoint), pupilJoint)

    def rigSetup(self):
        """ do the rig setup"""
        super(Eyeballs, self).rigSetup()

        for inputJoint, lookAtControl in zip(self.input, self.lookAtCtlList):
            # get the aim axis and length to use in the iris and pupil setup
            aimAxis = transform.getAimAxis(inputJoint)
            length = joint.length(inputJoint)

            irisJoint = getattr(self, "{}_irisJoint".format(inputJoint))
            pupilJoint = getattr(self, "{}_pupilJoint".format(inputJoint))

            attr.addSeparator(lookAtControl.name, "----")
            for jnt, part in zip([irisJoint, pupilJoint], ["iris", "pupil"]):
                dialateAttr = attr.createAttr(lookAtControl.name, "{}Dialate".format(part), "float", minValue=-10, maxValue=10)

                # use the guide to get the position of the joint
                position = cmds.getAttr("{joint}.t{axis}".format(joint=jnt, axis=aimAxis))
                percent = position / length

                # create the nodes we need for the setup

                # find the right starting value =

                w = pow((1 - (pow(percent, 2))), 0.5)
                angle = mathUtils.quaternionToEuler(percent, 0, 0, w)

                offset = angle[0] / 180
                print offset

                # add the offset to the default value so the joint starts in the right place
                remapName = "{}_dialate".format(jnt)
                remap = node.remapValue(input=dialateAttr, inMin=-10, inMax=10, outMin=0, outMax=1, name=remapName)
                # add a midpoint to the remap value with the value set at our offset
                remapDict = {"0": [0.0, 0.0, 1],
                             "1": [0.5, offset, 1],
                             "2": [1.0, 1.0, 1]}
                for i in remapDict.keys():
                    cmds.setAttr(remap + '.value[{}].value_Position'.format(i), remapDict[i][0])
                    cmds.setAttr(remap + '.value[{}].value_FloatValue'.format(i), remapDict[i][1])
                    cmds.setAttr(remap + '.value[{}].value_Interp'.format(i), remapDict[i][2])

                mdl = node.multDoubleLinear("{}.outValue".format(remap), 180, name="{}_toDegree".format(jnt))

                quat = cmds.createNode("eulerToQuat", name="{}_eulerToQuat".format(jnt))
                cmds.connectAttr("{}.output".format(mdl), "{}.inputRotateX".format(quat))

                sinScale = node.multDoubleLinear("{}.outputQuatX".format(quat), length, name="{}_sinScale".format(jnt))
                cosScale = node.multDoubleLinear("{}.outputQuatW".format(quat), length, name="{}_cosScale".format(jnt))

                cmds.connectAttr("{}.output".format(sinScale), "{joint}.t{axis}".format(joint=jnt, axis=aimAxis))
                scaleAxies = ['x', 'y', 'z']
                scaleAxies.remove(aimAxis)
                for axis in scaleAxies:
                    cmds.connectAttr("{}.output".format(cosScale), "{joint}.s{axis}".format(joint=jnt, axis=axis))
