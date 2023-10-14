"""
Functions for connections
"""
import logging

import maya.api.OpenMaya as om2
import maya.cmds as cmds

import rigamajig2.maya.attr as attr

logger = logging.getLogger(__name__)

def getPlugInput(plug):
    """
    Returns the input of a plug

    :param str plug: Plug to get the input of
    :return: The input connection of the plug
    :rtype: str
    """
    plugList = list()
    for sourcePlug in cmds.listConnections(plug, source=True, destination=False, plugs=True) or []:
        plugList.append(str(sourcePlug))
    return plugList


def getPlugOutput(plug):
    """
    Returns the output of a plug

    :param str plug: Plug to get the output of
    :return: The output connection of the plug
    :rtype: str
    """
    plugList = list()
    for sourcePlug in cmds.listConnections(plug, source=False, destination=True, plugs=True) or []:
        plugList.append(str(sourcePlug))
    return plugList


def connectPlugs(source, destination):
    """
    Connect input plug to output plug using maya API

    :param str source: plug on the source end of the connection
    :param str destination: plug on the destination end of the connection
    """
    sourcePlug = attr._getPlug(source)
    destPlug = attr._getPlug(destination)

    mdgModifier = om2.MDGModifier()
    mdgModifier.connect(sourcePlug, destPlug)
    mdgModifier.doIt()


def connectTransforms(source, destination, t=True, r=True, s=True):
    """
    Connect the transform plugs between two nodes.

    :param str source: node on the source end of the connection
    :param str destination: node on the destination end of the connection
    :param bool t:
    :param bool r:
    :param bool s:
    """
    attrs = list()
    if t:
        attrs += ["tx", "ty", "tz"]
    if r:
        attrs += ["rx", "ry", "rz"]
    if s:
        attrs += ["sx", "sy", "sz"]

    for attr in attrs:
        connectPlugs("{}{}".format(source, attr), "{}{}".format(destination, attr))


def connectPlugs2(source, destination):
    """
    Connect input plug to output plug using maya.cmds
    :param str source: name of the source plug
    :param str destination: nme of the desination plug
    """
    if attr.isCompound(source) == attr.isCompound(destination):
        cmds.connectAttr(source, destination, f=True)
    else:
        logger.error('Cannot connect compound and non-compound attributes: {} to {}'.format(source, destination))
