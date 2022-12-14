#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: lipsUtil.py
    author: masonsmigel
    date: 12/2022
    discription: Utility functions used in the lips component

"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
from rigamajig2.maya import transform
from rigamajig2.maya import node
from rigamajig2.maya import curve
from rigamajig2.maya import hierarchy
from rigamajig2.maya import mathUtils
from rigamajig2.maya import constrain
from rigamajig2.maya import skinCluster
from rigamajig2.maya import connection


def autoSkinLowCurve(crv, min, mid, max):
    """
    Auto skinweight the main curves
    :param crv:  the curve to weigh
    :param min: the minimum influence (the right corner)
    :param mid: the middle influence (the top or bottom lip)
    :param max:  the maximum inlfluence (the left corner)
    :return:
    """
    skin = skinCluster.getSkinCluster(crv)

    cvs = curve.getCvs(crv)

    midPoint = int(len(cvs) / 2)
    maxParam = len(cvs)

    for i, cv in enumerate(cvs):

        # get the parameter of the current CV
        x = float(i) / (maxParam - 1)

        # here y is equal to the value of the middle control
        y = (-((x * 2) - 1) ** 2) + 1

        # to get the outer control use 1-y
        outer = 1 - y

        if i > midPoint:
            transformValue = [(min, 0), (mid, y), (max, outer)]
        else:
            transformValue = [(min, outer), (mid, y), (max, 0)]

        # finally set the skinweights for the given CV
        cmds.skinPercent(skin, cv, transformValue=transformValue)


def noFlipOrient(driver1, driver2, target, blend=0.5):
    parent = cmds.listRelatives(target, parent=True)

    # a simple hierarchy for the rotations. we will create two joints each constrained to a different control then use a pair blend to rotate them!
    offset = cmds.createNode("transform", name="{}_offset".format(target), parent=parent[0])
    driver1Jnt = cmds.createNode("transform", name="{}_{}_ort".format(target, driver1), parent=offset)
    driver2Jnt = cmds.createNode("transform", name="{}_{}_ort".format(target, driver2), parent=offset)

    transform.matchTransform(target, offset)

    cmds.orientConstraint(driver1, driver1Jnt, mo=True, w=1)
    cmds.orientConstraint(driver2, driver2Jnt, mo=True, w=1)

    pairBlend = cmds.createNode("pairBlend", n="{}_ort_pairBlend".format(target))

    cmds.connectAttr("{}.r".format(driver1Jnt), "{}.inRotate1".format(pairBlend))
    cmds.connectAttr("{}.r".format(driver2Jnt), "{}.inRotate2".format(pairBlend))

    # set the rotation interpolation to quaternions
    cmds.setAttr("{}.rotInterpolation".format(pairBlend), 1)

    cmds.setAttr("{}.weight".format(pairBlend), blend)

    # finally connect the output to the joint
    cmds.connectAttr("{}.outRotate".format(pairBlend), "{}.r".format(target), f=True)


def autoWeightOrientation(sampleCurve, controlsList, jointsList, parent):
    """ Auto weight a bunch of controls """

    controlParams = list()
    # first make a list of the control parameters to setup
    for ctl in controlsList:
        pos = cmds.xform(ctl.name, q=True, ws=True, t=True)
        param = curve.getClosestParameter(sampleCurve, pos)
        controlParams.append(param)

    # next we can start to find values for the orient constraint
    for jnt in jointsList:

        jntPos = cmds.xform(jnt, q=True, ws=True, t=True)
        jntParam = curve.getClosestParameter(sampleCurve, jntPos)

        closestParam = mathUtils.closestValue(controlParams, jntParam)

        # now we can get the closest control!
        controlIndex = controlParams.index(closestParam)
        closestControl = controlsList[controlIndex]

        # great new we need the next closest control
        # first lets check if the two are almost equal
        if mathUtils.isEqual(jntParam, closestParam, tol=0.001):
            nextIndex = None

        elif jntParam > closestParam:
            nextIndex = controlIndex + 1
            nextIsLarger = True

        elif jntParam < closestParam:
            nextIndex = controlIndex - 1
            nextIsLarger = False

        # if the values are equal we can skip the orient weighting and go straight to the nearest joint
        if nextIndex is not None:

            nextControl = controlsList[nextIndex]
            # now we need to get the weights for the two controls
            nextParam = controlParams[nextIndex]
            minParam = min([closestParam, nextParam])

            # now we know the distance between the joint and the smallest parameter.
            closestDistance = jntParam - minParam

            # round this to the nearest decimal to make the numbers a bit nicer. We dont need alot of precision here!
            roundedDistance = round(closestDistance, 1)

            # now we can get a proper weight
            if nextIsLarger:
                closeWeight = roundedDistance

            elif not nextIsLarger:
                closeWeight = 1 - roundedDistance

            # a simple hierarchy for the rotations. we will create two joints each constrained
            # to a different control then use a pair blend to rotate them!
            offset = cmds.createNode("transform", name="{}_offset".format(jnt), parent=parent)
            closestJoint = cmds.createNode("transform", name="{}_{}_ort".format(jnt, closestControl.name),
                                           parent=offset)
            nextJoint = cmds.createNode("transform", name="{}_{}_ort".format(jnt, nextControl.name), parent=offset)

            # match the orientation of the new joint before we adjus them
            for newJoint in [closestJoint, nextJoint]:
                transform.matchRotate(jnt, newJoint)

            transform.matchTransform(jnt, offset)
            jntPci = cmds.listConnections("{}.t".format(jnt), type="pointOnCurveInfo")
            cmds.connectAttr("{}.result.position".format(jntPci[0]), "{}.t".format(offset))

            cmds.orientConstraint(closestControl.name, closestJoint, mo=True, w=1)
            cmds.orientConstraint(nextControl.name, nextJoint, mo=True, w=1)

            pairBlend = cmds.createNode("pairBlend", n="{}_ort_pairBlend".format(jnt))

            # connect our two driver joints
            cmds.connectAttr("{}.r".format(closestJoint), "{}.inRotate1".format(pairBlend))
            cmds.connectAttr("{}.r".format(nextJoint), "{}.inRotate2".format(pairBlend))

            # set the rotation interpolation to quaternions and connect the weight
            cmds.setAttr("{}.rotInterpolation".format(pairBlend), 1)
            cmds.setAttr("{}.weight".format(pairBlend), closeWeight)

            # finally connect the output to the joint
            cmds.connectAttr("{}.outRotate".format(pairBlend), "{}.r".format(jnt), f=True)

        else:
            cmds.orientConstraint(closestControl.name, jnt, mo=False, w=1)


def setupZipperBlending(joints, zipperTargets):
    """
    Setup a hierarachy to drive the zipper joints
    :param joints:
    :param zipperTargets:
    :return:
    """
    for i, jnt in enumerate(joints):
        mm = cmds.listConnections("{}.offsetParentMatrix".format(jnt), s=True, d=False, plugs=False)[0]
        zipperMM, dcmp = transform.connectOffsetParentMatrix(zipperTargets[i], jnt, mo=True)

        blendMatrix = cmds.createNode("blendMatrix", n="{}_zipper_blendMatrix".format(jnt))

        # connect the other two matricies into the blendMatrix
        cmds.connectAttr("{}.matrixSum".format(mm), "{}.inputMatrix".format(blendMatrix))
        cmds.connectAttr("{}.matrixSum".format(zipperMM), "{}.target[0].targetMatrix".format(blendMatrix))

        # connect the blend matrix back to the joint
        cmds.connectAttr("{}.outputMatrix".format(blendMatrix), "{}.offsetParentMatrix".format(jnt), f=True)


def setupZipper(name, uppJoints, lowJoints, paramsHolder):
    """
    Build the supper setup

    :param uppJoints: list of joints for the upper zipper
    :param lowJoints:  list of joints for the lower zipper
    """

    # first we need to build a set of triggers
    triggers = {"r": list(), "l": list()}
    numJoints = len(uppJoints)

    for side in 'rl':
        # setup the falloff
        delaySubtract = node.plusMinusAverage1D([10, "{}.{}ZipperFalloff".format(paramsHolder, side)], operation='sub',
                                                name="{}_l_delay".format(name))

        lerp = 1.0 / float(numJoints - 1)
        delayDivide = node.multDoubleLinear(input1="{}.{}".format(delaySubtract, 'output1D'), input2=lerp,
                                            name="{}_zipper_{}_div".format(name, side))

        multTriggers = list()
        subTriggers = list()
        triggers[side].append(multTriggers)
        triggers[side].append(subTriggers)

        for index in range(numJoints):
            indexName = "{}_{:02d}".format(name, index)

            delayMult = node.multDoubleLinear(index, "{}.{}".format(delayDivide, 'output'),
                                              name="{}_seal_{}".format(indexName, side))
            multTriggers.append(delayMult)

            subDelay = node.plusMinusAverage1D(["{}.{}".format(delayMult, "output"),
                                                "{}.{}ZipperFalloff".format(paramsHolder, side)],
                                               operation='sum', name="{}_seal_{}".format(indexName, side))
            subTriggers.append(subDelay)

    for i in range(numJoints):
        rIndex = i
        lIndex = numJoints - rIndex - 1
        indexName = "{}_zipper_{}".format(name, lIndex)

        lMultTrigger, lSubTrigger = triggers['l'][0][lIndex], triggers['l'][1][lIndex]
        rMultTrigger, rSubTrigger = triggers['r'][0][rIndex], triggers['r'][1][rIndex]

        # right network
        lRemap = node.remapValue("{}.{}Zipper".format(paramsHolder, 'l'),
                                 inMin="{}.{}".format(lMultTrigger, "output"),
                                 inMax="{}.{}".format(lSubTrigger, "output1D"),
                                 outMax=1, interp='smooth', name="{}_seal_{}".format(indexName, 'l'))

        # right network
        rSub = node.plusMinusAverage1D([1, "{}.{}".format(lRemap, "outValue")], operation='sub',
                                       name="{}_offset_seal_r_sub".format(indexName))

        rRemap = node.remapValue("{}.{}Zipper".format(paramsHolder, 'r'),
                                 inMin="{}.{}".format(rMultTrigger, "output"),
                                 inMax="{}.{}".format(rSubTrigger, "output1D"),
                                 outMax="{}.{}".format(rSub, "output1D"),
                                 interp='smooth', name="{}_seal_{}".format(indexName, 'r'))
        # final addition of both sides
        total = node.plusMinusAverage1D(["{}.{}".format(rRemap, "outValue"), "{}.{}".format(lRemap, "outValue")],
                                      name="{}_sum".format(indexName))

        clamp = node.remapValue("{}.output1D".format(total), name="{}_clamp".format(indexName))

        for jointList in [uppJoints, lowJoints]:
            # get the proper joint and attatch the output of the zipper setup
            jnt = jointList[i]
            blendMatrix = cmds.listConnections("{}.offsetParentMatrix".format(jnt), s=True, d=False, plugs=False)[0]
            cmds.connectAttr("{}.{}".format(clamp, 'outValue'), "{}.{}".format(blendMatrix, "envelope"), f=True)
