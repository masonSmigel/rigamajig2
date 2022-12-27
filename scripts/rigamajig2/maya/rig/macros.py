#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: macros.py
    author: masonsmigel
    date: 12/2022
    discription: Functions and tool for building macros

"""
import maya.cmds as cmds
from rigamajig2.maya import sdk
from rigamajig2.maya import attr


def createMacroPose(driverPlug, drivenControls=None, preInfinity=False, postInfinity=False,
                    tangent='linear'):
    """
    Create a new macro pose with the given controls and driver. The pose is set based on the CURRENT values of the controls.

    :param driverPlug: name of the driver plug.
    :param drivenControls: list of controls to be driven by the macroPose. If None any posed controls will be used.
    :param bool preInfinity: If true set the tanget to PreInfitity to linear
    :param bool postInfinity:If true set the tanget to postInfinity to linear
    :param str tangent: type of tangent for the curve.
    :return:
    """
    if not cmds.objExists(driverPlug):
        raise Exception("The driver plug {} does not exist".format(driverPlug))

    driverValue = cmds.getAttr(driverPlug)

    if driverValue == 0:
        raise Exception("The driver value cannot equal zero".format(driverPlug))

    for drivenControl in drivenControls:
        pass


def createSdkPose(driverPlug, drivenPlug, driverValue, drivenValue, preInfinity=False, postInfinity=False,
                  tangent='linear'):
    """
    Add a new macro pose with the given driver and driven plug and values

    :param driverPlug: name of the plug to drive the SDK connection
    :param drivenPlug: name of the plug driven By the SDK connection
    :param driverValue: value of the driver plug to trigger the pose. Cannot be 0.
    :param drivenValue: value of the driven plug with the pose is triggered
    :param bool preInfinity: If true set the tanget to PreInfitity to linear
    :param bool postInfinity:If true set the tanget to postInfinity to linear
    :param str tangent: type of tangent for the curve.
    :return: the name of the SDK node created
    """

    # first lets make a new valueList with the rest pose set at 0
    valueList = [(0, 0), (driverValue, drivenValue)]

    sdkNode = sdk.createSdk(driverPlug=driverPlug,
                            drivenPlug=drivenPlug,
                            values=valueList,
                            preInfinity=preInfinity,
                            postInfinity=postInfinity,
                            tangent=tangent
                            )

    return sdkNode


def createCombo(drivers, name=None, method="mult"):
    """
    Create a combo Node from a list of drivers.

    :param drivers: list of plugs to add as drivers to the combo shape
    :param name: optional name of the combo driver node
    :param method: combination method. Valid values are "mult", "lowest", "smooth"
    """
    if not name:
        name = "__".join([x.replace(".", "_") for x in drivers]) + "_combo"
    comboNode = cmds.createNode("combinationShape", name=name)

    # set the combination method
    methodDict = {"mult": 0, "lowest": 1, "smooth": 2}
    if method not in list(methodDict.keys()):
        raise Exception("{} is not a valid method type. Valid types are: {}".format(method, list(methodDict.keys())))

    cmds.setAttr("{}.combinationMethod".format(comboNode), methodDict[method])

    for driver in drivers:
        if cmds.objExists(driver):
            nextAvailable = attr.getNextAvailableElement("{}.inputWeight".format(comboNode))
            cmds.connectAttr(driver, nextAvailable)

    return comboNode + ".outputWeight"
