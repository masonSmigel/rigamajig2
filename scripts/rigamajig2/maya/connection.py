"""
Functions for connections
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2
import rigamajig2.maya.attr as attr


def getPlugInput(plug):
    """
    Returns the input of a plug
    :param plug: Plug to get the input of
    :type plug: str

    :return: The input connection of the plug
    :rtype: str
    """
    plugList = list()
    for sourcePlug in cmds.listConnections(plug, source=True, plugs=True):
        plugList.append(str(sourcePlug))
    return plugList


def getPlugOutput(plug):
    """
    Returns the output of a plug
    :param plug: Plug to get the output of
    :type plug: str

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
    :param source: plug on the source end of the connection
    :param destination: plug on the destination end of the connection
    :return:
    """
    sourcePlug = attr._getPlug(source)
    destPlug = attr._getPlug(destination)

    mdgModifier = om2.MDGModifier()
    mdgModifier.connect(sourcePlug, destPlug)
    mdgModifier.doIt()


def connectPlugs2(source, destination):
    """
    Connect input plug to output plug using maya.cmds
    :param source:
    :param destination:
    :return:
    """
    if attr.isCompound(source) == attr.isCompound(destination):
        cmds.connectAttr(source, destination, f=True)
    else:
        cmds.error('Cannot connect compound and non-compound attributes: {} to {}'.format(source, destination ))