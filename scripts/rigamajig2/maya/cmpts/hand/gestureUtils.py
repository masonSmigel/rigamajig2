#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: gestureUtils.py.py
    author: masonsmigel
    date: 07/2022
    discription:

"""

import maya.cmds as cmds

import rigamajig2.shared.common as common
import rigamajig2.maya.sdk as sdk
import rigamajig2.maya.attr as attr
import rigamajig2.maya.rig.control as rig_control


def setupSpreadSdk(controlsList, attrHolder, driverAttr, axis='y', multiplier=1.0):
    """
    setup the spread on a list of controls.
    the list should contain a list of joints starting with the index finger and extend towards the pinky.


    Note: different numbers of fingers are supported however 4 if the typically expected amount.
    :param controlsList:
    :param attrHolder:
    :param driverAttr:
    :param str axis: the axis that the transformation should take place on. the default value is z for spread.
    :param multiplier: overal multiplier on the values of the spread system
    :return:
    """
    controlsList = common.toList(controlsList)

    if not cmds.objExists("{}.{}".format(attrHolder, driverAttr)):
        attr.createAttr(attrHolder, driverAttr, attributeType='float', value=0)

    driverPlug = "{}.{}".format(attrHolder, driverAttr)
    for i, control in enumerate(controlsList):
        controlObj = rig_control.Control(control)
        targetPlug = "{}.r{}".format(controlObj.sdk, axis)

        if i == 0:
            value = float(1 * multiplier)
            valueList = [(-1, value), (0, 0), (1, -value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        if i == 2:
            value = float(1 * multiplier)
            valueList = [(-1, -value), (0, 0), (1, value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True,
                          postInfinity=True)
        if i > 2:
            value = float(2 * multiplier * (i-2))
            valueList = [(-1, -value), (0, 0), (1, value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True,
                          postInfinity=True)


def setupCurlSdk(controlsList, attrHolder, driverAttr, axis='z', multiplier=1.0, metaControls=2):
    """
    setup the curl controls.


    :param controlsList: list of controls to apply the curl to
    :param attrHolder: node to hold the drive attribute
    :param driverAttr: attribute to drive the curl
    :param axis: axis to curl on
    :param multiplier: overal multiplier on the values of the curl system
    :param metaControls: number of meta joints

    :return:
    """
    controlsList = common.toList(controlsList)

    if not cmds.objExists("{}.{}".format(attrHolder, driverAttr)):
        attr.createAttr(attrHolder, driverAttr, attributeType='float', value=0)

    driverPlug = "{}.{}".format(attrHolder, driverAttr)
    for i, control in enumerate(controlsList):
        controlObj = rig_control.Control(control)
        targetPlug = "{}.r{}".format(controlObj.sdk, axis)

        if i < metaControls:
            if i == 0:
                value = float(0.05 * multiplier)
            else:
                value = float(0.1 * multiplier)
            valueList = [(-1, value), (0, 0), (1, -value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        else:
            value = float(1.0 * multiplier)
            valueList = [(-1, value), (0, 0), (1, -value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)


def setupFanSdk(controlsList, attrHolder, driverAttr, axis='z', multiplier=1.0):
    """
    setup the fan on a list of controls.
    the list should contain a list of joints starting with the index finger and extend towards the pinky.


    Note: different numbers of fingers are supported however 4 if the typically expected amount.
    :param controlsList:
    :param attrHolder:
    :param driverAttr:
    :param str axis: the axis that the transformation should take place on. the default value is z for spread.
    :param multiplier: overal multiplier on the values of the spread system
    :return:
    """
    controlsList = common.toList(controlsList)

    if not cmds.objExists("{}.{}".format(attrHolder, driverAttr)):
        attr.createAttr(attrHolder, driverAttr, attributeType='float', value=0)

    driverPlug = "{}.{}".format(attrHolder, driverAttr)
    for i, control in enumerate(controlsList):
        controlObj = rig_control.Control(control)
        targetPlug = "{}.r{}".format(controlObj.sdk, axis)

        if i == 0:
            value = float(1.5 * multiplier)
            valueList = [(-1, -value), (0, 0), (1, value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True,postInfinity=True)
        if i == 1:
            value = float(0.5 * multiplier)
            valueList = [(-1, -value), (0, 0), (1, value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        if i == 2:
            value = float(0.5 * multiplier)
            valueList = [(-1, value), (0, 0), (1, -value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        if i > 2:
            value = float(1.5 * multiplier * (i-2))
            valueList = [(-1, value), (0, 0), (1, -value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)


def setupSimple(controlsList, attrHolder, driverAttr, axis='x', multplier=1.0):

    controlsList = common.toList(controlsList)

    if not cmds.objExists("{}.{}".format(attrHolder, driverAttr)):
        attr.createAttr(attrHolder, driverAttr, attributeType='float', value=0)

    driverPlug = "{}.{}".format(attrHolder, driverAttr)
    for i, control in enumerate(controlsList):
        control = checkForSDK(control)
        targetPlug = "{}.r{}".format(control, axis)

        value = float(1 * multplier)
        valueList = [(-1, -value), (0, 0), (1, value)]
        sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)


def checkForSDK(control):
    if rig_control.isControl(control):
        controlObj = rig_control.Control(control)
        return controlObj.sdk
    return control


if __name__ == '__main__':
    setupSpreadSdk(['indexMeta_fk', 'middleMeta_fk', 'ringMeta_fk', 'pinkyMeta_fk'], 'Hand_poses', 'spread',
                   multiplier=0.7)
    setupSpreadSdk(['indexMeta_fk_1', 'middleMeta_fk_1', 'ringMeta_fk_1', 'pinkyMeta_fk_1'], 'Hand_poses', 'spread',
                   multiplier=0.3)

    # meta Spread
    setupSpreadSdk(['indexMeta_fk', 'middleMeta_fk', 'ringMeta_fk', 'pinkyMeta_fk'], 'Hand_poses', 'metaSpread',
                   multiplier=1)