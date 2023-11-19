#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: gestureUtils.py.py
    author: masonsmigel
    date: 07/2022
    description:

"""
from typing import List

import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import sdk
from rigamajig2.maya.rig import control
from rigamajig2.shared import common


def setupSpreadSdk(
    controlsList: List[str], attrHolder: str, driverAttr: str, axis: str = "y", multiplier: float = 1.0
) -> None:
    """
    setup the spread on a list of controls.
    the list should contain a list of joints starting with the index finger and extend towards the pinky.


    Note: different numbers of fingers are supported however 4 if the typically expected amount.
    :param controlsList: list of controls to apply the sdk to
    :param attrHolder: node to hold the drive attribute
    :param driverAttr: attribute to drive the sdk
    :param str axis: the axis that the transformation should take place on. the default value is z for spread.
    :param multiplier: overal multiplier on the values of the spread system
    :return:
    """
    controlsList = common.toList(controlsList)

    if not cmds.objExists("{}.{}".format(attrHolder, driverAttr)):
        attr.createAttr(attrHolder, driverAttr, attributeType="float", value=0)

    driverPlug = "{}.{}".format(attrHolder, driverAttr)
    for i, eachControl in enumerate(controlsList):
        controlObj = control.Control(eachControl)
        targetPlug = "{}.r{}".format(controlObj.sdk, axis)

        if i == 0:
            value = float(1 * multiplier)
            valueList = [(-1, value), (0, 0), (1, -value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        if i == 2:
            value = float(1 * multiplier)
            valueList = [(-1, -value), (0, 0), (1, value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        if i > 2:
            value = float(2 * multiplier * (i - 2))
            valueList = [(-1, -value), (0, 0), (1, value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)


def setupCurlSdk(
    controlsList: List[str],
    attrHolder: str,
    driverAttr: str,
    axis: str = "z",
    multiplier: float = 1.0,
    metaControls: int = 2,
) -> None:
    """
    setup the curl controls.


    :param controlsList: list of controls to apply the sdk to
    :param attrHolder: node to hold the drive attribute
    :param driverAttr: attribute to drive the sdk
    :param axis: axis to curl on
    :param multiplier: overal multiplier on the values of the curl system
    :param metaControls: number of meta joints

    :return:
    """
    controlsList = common.toList(controlsList)

    if not cmds.objExists("{}.{}".format(attrHolder, driverAttr)):
        attr.createAttr(attrHolder, driverAttr, attributeType="float", value=0)

    driverPlug = "{}.{}".format(attrHolder, driverAttr)
    for i, eachControl in enumerate(controlsList):
        controlObj = control.Control(eachControl)
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


def setupFanSdk(
    controlsList: List[str], attrHolder: str, driverAttr: str, axis: str = "z", multiplier: float = 1.0
) -> None:
    """
    setup the fan on a list of controls.
    the list should contain a list of joints starting with the index finger and extend towards the pinky.


    Note: different numbers of fingers are supported however 4 if the typically expected amount.
    :param controlsList: list of controls to apply sdk to
    :param attrHolder: node to hold the drive attribute
    :param driverAttr: attribute to drive the sdk
    :param str axis: the axis that the transformation should take place on. the default value is z for spread.
    :param multiplier: overal multiplier on the values of the spread system
    :return:
    """
    controlsList = common.toList(controlsList)

    if not cmds.objExists("{}.{}".format(attrHolder, driverAttr)):
        attr.createAttr(attrHolder, driverAttr, attributeType="float", value=0)

    driverPlug = "{}.{}".format(attrHolder, driverAttr)
    for i, eachControl in enumerate(controlsList):
        controlObj = control.Control(eachControl)
        targetPlug = "{}.r{}".format(controlObj.sdk, axis)

        if i == 0:
            value = float(1.5 * multiplier)
            valueList = [(-1, -value), (0, 0), (1, value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        if i == 1:
            value = float(0.5 * multiplier)
            valueList = [(-1, -value), (0, 0), (1, value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        if i == 2:
            value = float(0.5 * multiplier)
            valueList = [(-1, value), (0, 0), (1, -value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
        if i > 2:
            value = float(1.5 * multiplier * (i - 2))
            valueList = [(-1, value), (0, 0), (1, -value)]
            sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)


def setupSimple(
    controlsList: List[str], attrHolder: str, driverAttr: str, axis: str = "x", multplier: float = 1.0
) -> None:
    """
    Setup a simple connection
    :param controlsList: list of controls to apply sdk to
    :param attrHolder: node to hold the drive attribute
    :param driverAttr: attribute to drive the sdk
    :param axis: the axis that the transformation should take place on. the default value is z for spread.
    :param multplier: overal multiplier on the values of the spread system
    """
    controlsList = common.toList(controlsList)

    if not cmds.objExists("{}.{}".format(attrHolder, driverAttr)):
        attr.createAttr(attrHolder, driverAttr, attributeType="float", value=0)

    driverPlug = "{}.{}".format(attrHolder, driverAttr)
    for i, eachControl in enumerate(controlsList):
        targetPlug = "{}.r{}".format(eachControl, axis)

        value = float(1 * multplier)
        valueList = [(-1, -value), (0, 0), (1, value)]
        sdk.createSdk(driverPlug, targetPlug, values=valueList, preInfinity=True, postInfinity=True)
