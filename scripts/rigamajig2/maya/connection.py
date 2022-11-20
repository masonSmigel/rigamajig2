"""
Functions for connections
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2
import rigamajig2.maya.attr as attr


def getPlugInput(plug):
    """
    Returns the input of a plug

    :param str plug: Plug to get the input of
    :return: The input connection of the plug
    :rtype: str
    """
    plugList = list()
    for sourcePlug in cmds.listConnections(plug, source=True, plugs=True) or []:
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
    for sourcePlug in cmds.listConnections(plug, destination=True, plugs=True):
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


def connectPlugs2(source, destination):
    """
    Connect input plug to output plug using maya.cmds
    :param str source: name of the source plug
    :param str destination: nme of the desination plug
    """
    if attr.isCompound(source) == attr.isCompound(destination):
        cmds.connectAttr(source, destination, f=True)
    else:
        cmds.error('Cannot connect compound and non-compound attributes: {} to {}'.format(source, destination ))