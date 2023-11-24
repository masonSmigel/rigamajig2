#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: lipsUtil.py
    author: masonsmigel
    date: 12/2022
    description: Utility functions used in the lips component

"""
import maya.cmds as cmds

from rigamajig2.maya import curve
from rigamajig2.maya import mathUtils
from rigamajig2.maya import node
from rigamajig2.maya import skinCluster
from rigamajig2.maya import transform


def autoSkinLowCurve(crv, min, mid, max):
    """
    Auto skinweight the main curves.

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
        y = (-(((x * 2) - 1) ** 2)) + 1

        # to get the outer control use 1-y
        outer = 1 - y

        if i > midPoint:
            transformValue = [(min, 0), (mid, y), (max, outer)]
        else:
            transformValue = [(min, outer), (mid, y), (max, 0)]

        # finally set the skinweights for the given CV
        cmds.skinPercent(skin, cv, transformValue=transformValue)


def noFlipOrient(driver1, driver2, target, blend=0.5):
    """
    Create the no flip orient constraint for the lips.
    This is done by creating two separate orient constraints and blending them together using a pairBlend
    with the rotate interpolation set to Quaternion

    :param driver1: first driver node
    :param driver2: second driver node
    :param target: target node to constraint
    :param blend: blend between the first and second drivers
    """
    parent = cmds.listRelatives(target, parent=True)

    # a simple hierarchy for the rotations. we will create two joints each constrained to a different control then use a pair blend to rotate them!
    offset = cmds.createNode(
        "transform", name="{}_offset".format(target), parent=parent[0]
    )
    driver1Jnt = cmds.createNode(
        "transform", name="{}_{}_ort".format(target, driver1), parent=offset
    )
    driver2Jnt = cmds.createNode(
        "transform", name="{}_{}_ort".format(target, driver2), parent=offset
    )

    transform.matchTransform(target, offset)

    cmds.orientConstraint(driver1, driver1Jnt, mo=True, w=1)
    cmds.orientConstraint(driver2, driver2Jnt, mo=True, w=1)

    # create and connect a pairBlend None
    pairBlend = cmds.createNode("pairBlend", n="{}_ort_pairBlend".format(target))
    cmds.connectAttr("{}.r".format(driver1Jnt), "{}.inRotate1".format(pairBlend))
    cmds.connectAttr("{}.r".format(driver2Jnt), "{}.inRotate2".format(pairBlend))

    # set the rotation interpolation to quaternions
    cmds.setAttr("{}.rotInterpolation".format(pairBlend), 1)

    cmds.setAttr("{}.weight".format(pairBlend), blend)

    # finally connect the output to the joint
    cmds.connectAttr("{}.outRotate".format(pairBlend), "{}.r".format(target), f=True)


def autoWeightOrientation(sampleCurve, controlsList, jointsList, parent):
    """
    Auto weight orientation of controls along a curve. This is done by sampling the controls parameter,
    then sampling the joints and comparng them to the controls. Joints have their orientation weighted between the two
    nearest controls.

    :param sampleCurve: Curve which to sample the parameters off of.
    :param controlsList: List of controls(or other objects) which will drive the rotation of the joints
    :param jointsList: list of joints (or other nodes) that will be driven by objects in the controlList
    :param parent: specify a parent for setups we create
    """

    # first make a list of the control parameters to setup.
    # we will use this list to compare against the parameter of the joints
    controlParams = list()
    for ctl in controlsList:
        pos = cmds.xform(ctl.name, q=True, ws=True, t=True)
        param = curve.getClosestParameter(sampleCurve, pos)
        controlParams.append(param)

    # next we can start to find values for the orient constraint
    for jnt in jointsList:
        # get the joint parameter and find the closest control by comparing to the controlList
        jntPos = cmds.xform(jnt, q=True, ws=True, t=True)
        jntParam = curve.getClosestParameter(sampleCurve, jntPos)
        closestParam = mathUtils.closestValue(controlParams, jntParam)

        # now that we have the parameter we can index the controlParams list
        # to find the the control from the controlsList
        controlIndex = controlParams.index(closestParam)
        closestControl = controlsList[controlIndex]

        # great new we need the next closest control so we can blend the rotation.

        # first lets check if the two are almost equal.
        # If they are then we dont need to find another control and can constrain directly to the cloestControl
        if mathUtils.isEqual(jntParam, closestParam, tol=0.001):
            nextIndex = None

        # if the jntParam is larger than the closestParam we can get the control that is next to the closestControl
        elif jntParam > closestParam:
            nextIndex = controlIndex + 1
            nextIsLarger = True
        # if the jntParam is smaller than the closestparam we can get the control before the closest control
        elif jntParam < closestParam:
            nextIndex = controlIndex - 1
            nextIsLarger = False

        # if the values are equal we can skip the orient weighting and go straight to the nearest joint
        if nextIndex is not None:
            # next grab the next control
            nextControl = controlsList[nextIndex]

            # now we need to get the weights for the two controls. We can do this by comparing the distance between the
            # jntParam and the smaller parameter to get a fraction.
            nextParam = controlParams[nextIndex]
            minParam = min([closestParam, nextParam])
            closestDistance = jntParam - minParam

            # round this to the nearest decimal to make the numbers a bit nicer. We dont need alot of precision here!
            roundedDistance = round(closestDistance, 1)

            # next because sometimes the nextControl is before and sometimes after the closest control
            # we may need to invert the distance
            if nextIsLarger:
                closeWeight = roundedDistance

            elif not nextIsLarger:
                closeWeight = 1 - roundedDistance

            # Finally we can build a simple hierarchy for the rotations. we will create two joints each constrained
            # to a different control then use a pair blend to rotate them!
            offset = cmds.createNode(
                "transform", name="{}_offset".format(jnt), parent=parent
            )
            closestJoint = cmds.createNode(
                "transform",
                name="{}_{}_ort".format(jnt, closestControl.name),
                parent=offset,
            )
            nextJoint = cmds.createNode(
                "transform",
                name="{}_{}_ort".format(jnt, nextControl.name),
                parent=offset,
            )

            # match the orientation of the new joint before we adjust them
            for newJoint in [closestJoint, nextJoint]:
                transform.matchRotate(jnt, newJoint)

            # because we know theese are constrained to a point on a curve
            # lets grab the pointOnCurveInfo node to drive our offset
            transform.matchTransform(jnt, offset)
            jntPci = cmds.listConnections("{}.t".format(jnt), type="pointOnCurveInfo")
            cmds.connectAttr(
                "{}.result.position".format(jntPci[0]), "{}.t".format(offset)
            )

            cmds.orientConstraint(closestControl.name, closestJoint, mo=True, w=1)
            cmds.orientConstraint(nextControl.name, nextJoint, mo=True, w=1)

            pairBlend = cmds.createNode("pairBlend", n="{}_ort_pairBlend".format(jnt))

            # connect our two driver joints
            cmds.connectAttr(
                "{}.r".format(closestJoint), "{}.inRotate1".format(pairBlend)
            )
            cmds.connectAttr("{}.r".format(nextJoint), "{}.inRotate2".format(pairBlend))

            # set the rotation interpolation to quaternions and connect the weight
            cmds.setAttr("{}.rotInterpolation".format(pairBlend), 1)
            cmds.setAttr("{}.weight".format(pairBlend), closeWeight)

            # finally connect the output to the joint
            cmds.connectAttr(
                "{}.outRotate".format(pairBlend), "{}.r".format(jnt), f=True
            )

        else:
            cmds.orientConstraint(closestControl.name, jnt, mo=False, w=1)


def setupZipperBlending(joints, zipperTargets):
    """
    Setup a hierarachy to drive the zipper joints

    :param joints: list of zipper joints to be driven by the list of zipper targets
    :param zipperTargets: list of zipper targets to drive the joints
    :return:
    """
    for i, jnt in enumerate(joints):
        multMatrix = cmds.listConnections(
            "{}.offsetParentMatrix".format(jnt), s=True, d=False, plugs=False
        )[0]
        zipperMultMatrix, _ = transform.connectOffsetParentMatrix(
            zipperTargets[i], jnt, mo=True
        )

        blendMatrix = cmds.createNode(
            "blendMatrix", n="{}_zipper_blendMatrix".format(jnt)
        )

        # connect the other two matricies into the blendMatrix
        cmds.connectAttr(
            "{}.matrixSum".format(multMatrix), "{}.inputMatrix".format(blendMatrix)
        )
        cmds.connectAttr(
            "{}.matrixSum".format(zipperMultMatrix),
            "{}.target[0].targetMatrix".format(blendMatrix),
        )

        # connect the blend matrix back to the joint
        cmds.connectAttr(
            "{}.outputMatrix".format(blendMatrix),
            "{}.offsetParentMatrix".format(jnt),
            f=True,
        )


ZIPPER_ATTR = "Zipper"
ZIPPER_FALLOFF_ATTR = "ZipperFalloff"


def setupZipper(name, uppJoints, lowJoints, paramsHolder):
    """
    Build the supper setup by creating a setup to adjust the weight of the blendMatrix nodes we built
    in the previous step.

    :param name: name of the component. this is used to rename some of the nodes
    :param uppJoints: list of joints for the upper zipper
    :param lowJoints:  list of joints for the lower zipper
    :param paramsHolder: the node that holds our zipperAttributes
    """

    # first we need to build a set of triggers
    triggers = {"r": list(), "l": list()}
    numJoints = len(uppJoints)

    for side in "rl":
        # setup the falloff
        delaySubtract = node.plusMinusAverage1D(
            [10, "{}.{}{}".format(paramsHolder, side, ZIPPER_FALLOFF_ATTR)],
            operation="sub",
            name="{}_l_delay".format(name),
        )

        delayDivide = node.multDoubleLinear(
            input1="{}.{}".format(delaySubtract, "output1D"),
            input2=1.0 / float(numJoints - 1),
            name="{}_zipper_{}_div".format(name, side),
        )

        multTriggers = list()
        subTriggers = list()
        triggers[side].append(multTriggers)
        triggers[side].append(subTriggers)

        for index in range(numJoints):
            indexName = "{}_{:02d}".format(name, index)

            delayMultName = "{}_zipper_{}".format(indexName, side)
            delayMult = node.multDoubleLinear(
                index, "{}.{}".format(delayDivide, "output"), name=delayMultName
            )
            multTriggers.append(delayMult)

            subDelayName = "{}_zipper_{}".format(indexName, side)
            subDelay = node.plusMinusAverage1D(
                inputs=[
                    "{}.{}".format(delayMult, "output"),
                    "{}.{}{}".format(paramsHolder, side, ZIPPER_FALLOFF_ATTR),
                ],
                operation="sum",
                name=subDelayName,
            )
            subTriggers.append(subDelay)

    for i in range(numJoints):
        rIndex = i
        lIndex = numJoints - rIndex - 1
        indexName = "{}_zipper_{}".format(name, lIndex)

        lMultTrigger, lSubTrigger = triggers["l"][0][lIndex], triggers["l"][1][lIndex]
        rMultTrigger, rSubTrigger = triggers["r"][0][rIndex], triggers["r"][1][rIndex]

        # Setup the network for the left side
        lRemap = node.remapValue(
            "{}.{}{}".format(paramsHolder, "l", ZIPPER_ATTR),
            inMin="{}.{}".format(lMultTrigger, "output"),
            inMax="{}.{}".format(lSubTrigger, "output1D"),
            outMax=1,
            interp="smooth",
            name="{}_zipper_{}".format(indexName, "l"),
        )

        # setup the nextwork for the right side
        rSub = node.plusMinusAverage1D(
            [1, "{}.{}".format(lRemap, "outValue")],
            operation="sub",
            name="{}_offset_zipper_r_sub".format(indexName),
        )

        rRemap = node.remapValue(
            "{}.{}{}".format(paramsHolder, "r", ZIPPER_ATTR),
            inMin="{}.{}".format(rMultTrigger, "output"),
            inMax="{}.{}".format(rSubTrigger, "output1D"),
            outMax="{}.{}".format(rSub, "output1D"),
            interp="smooth",
            name="{}_zipper_{}".format(indexName, "r"),
        )

        # Add the outputs of both the left and right network together so we can zip from either side
        total = node.plusMinusAverage1D(
            ["{}.{}".format(rRemap, "outValue"), "{}.{}".format(lRemap, "outValue")],
            name="{}_sum".format(indexName),
        )

        # clamp the value to one so we cant overdrive the zip
        clamp = node.remapValue(
            "{}.output1D".format(total), name="{}_clamp".format(indexName)
        )

        # Connect the clamp node to our blendMatrix node
        for jointList in [uppJoints, lowJoints]:
            jnt = jointList[i]
            blendMatrix = cmds.listConnections(
                "{}.offsetParentMatrix".format(jnt), s=True, d=False, plugs=False
            )[0]
            cmds.connectAttr(
                "{}.{}".format(clamp, "outValue"),
                "{}.{}".format(blendMatrix, "envelope"),
                f=True,
            )
