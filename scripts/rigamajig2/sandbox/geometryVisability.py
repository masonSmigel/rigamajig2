#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: geometryVisability.py
    author: masonsmigel
    date: 11/2022
    description: 

"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import node
from rigamajig2.shared import common


def addGeometrySwitch(driverNode, driverAttr, geoSets=None, enumNames=None):
    """
    Add a switch for geometry visability
    :param driverNode: driver node
    :param driverAttr: driver attribute
    :param list geoSets: list of  geometry nodes or list of lists
    :param enumNames: list of names for the geometry names
    :return:
    """

    if not cmds.objExists("{}.{}".format(driverNode, driverAttr)):
        attr.createEnum(driverNode, longName=driverAttr, enum=enumNames, value=0)

    numberOfSets = len(geoSets)

    choiceNodes = list()
    for i in range(numberOfSets):
        choicesList = [1 if i == x else 0 for x in range(len(geoSets))]
        choice = node.choice("{}.{}".format(driverNode, driverAttr),
                             choices=choicesList,
                             name="{}_{}".format(driverAttr, enumNames[i]))

        geoInSet = common.toList(geoSets[i])
        choiceNodes.append(choice)

        for geo in geoInSet:
            cmds.connectAttr("{}.{}".format(choice, "output"), "{}.{}".format(geo, "v"))

    return choiceNodes
