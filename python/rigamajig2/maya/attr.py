#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: attr.py
    author: masonsmigel
    date: 01/2021
    description: attribute functions and helpers.
"""
import logging
from typing import Union

import maya.api.OpenMaya as om2
import maya.cmds as cmds

import rigamajig2.shared.common as common

logger = logging.getLogger(__name__)

TRANSLATE = ["tx", "ty", "tz"]
ROTATE = ["rx", "ry", "rz"]
SCALE = ["sx", "sy", "sz"]
TRANSFORMS = TRANSLATE + ROTATE + SCALE


def isAttr(plug):
    """
    Check if the node is a valid Container

    :param str plug: Node to check
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    node = plug.split(".")[0]
    attr = plug.replace(node + ".", "")
    attrNoCompound = attr.split("[")[0]

    if cmds.attributeQuery(attrNoCompound, node=node, exists=True):
        return True
    return False


# We need alot of arguments here
# pylint:disable=too-many-arguments
def createAttr(
    node,
    longName,
    attributeType,
    value=None,
    niceName=None,
    shortName=None,
    minValue=None,
    maxValue=None,
    keyable=True,
    readable=True,
    writable=True,
    storable=True,
    channelBox=False,
    locked=False,
):
    """
    Add a new attribute to the provided node.

    :param str list node: Node to add the attribute to
    :param str longName: Long name of the attribute
    :param str attributeType: Attribute Type. ['string', 'bool', 'float', 'int', 'double3', matrix]
    :param int float str value: (Optional) Default value of the attribute
    :param str niceName: (Optional) Nice name of the attribute
    :param str shortName: (Optional) Short name of the attribute
    :param int float minValue: (Optional) Minimum value
    :param int float maxValue: (Optional) Maximum value
    :param bool keyable: (Optional) If the attribute is keyable. Default True.
    :param bool readable: (Optional) If the attribute can have outgoing connections. Default True.
    :param bool writable: (Optional) If the attribute can have incoming connections. Default True.
    :param bool storable: (Optional) If the attribute can be stored to a file. Default True.
    :param bool channelBox: (Optional) If the attribute is non-keyable should it be in the channel box.
    :param bool locked: (Optional) Lock the the attribute on creation

    :return: Attribute Added
    :rtype: str
    """
    if hasAttr(node, longName):
        logger.warning("Attribute {1}, already exists on {0}".format(node, longName))
        return
    data = dict()
    if shortName is not None:
        data["shortName"] = shortName
    if niceName is not None:
        data["niceName"] = niceName

    if attributeType in ["string"]:
        data["dataType"] = attributeType
    else:
        data["attributeType"] = attributeType

    if minValue is not None and minValue is not False:
        data["minValue"] = minValue
    if maxValue is not None and maxValue is not False:
        data["maxValue"] = maxValue

    data["keyable"] = keyable
    data["readable"] = readable
    data["storable"] = storable
    data["writable"] = writable

    if value is not None and attributeType not in ["string"]:
        data["defaultValue"] = value

    cmds.addAttr(node, longName=longName, **data)

    plug = str(node + "." + longName)
    if value:
        if attributeType == "string":
            cmds.setAttr(plug, value, type=attributeType)
        else:
            cmds.setAttr(plug, value)
    if channelBox:
        cmds.setAttr(plug, channelBox=True)
    if locked:
        lock(node, longName)

    return plug


# We need alot of arguments here
# pylint:disable=too-many-arguments
def createEnum(
    node,
    longName,
    enum,
    value=None,
    niceName=None,
    shortName=None,
    keyable=True,
    readable=True,
    writable=True,
    storable=True,
    channelBox=False,
):
    """
    Add an Enum attribute

    :param str list node: Node to add the attribute to
    :param str longName: Long name of the attribute
    :param list enum: enum values to add
    :param int float value: (Optional) Default value of the attribute
    :param str niceName: (Optional) Nice name of the attribute
    :param str shortName: (Optional) Short name of the attribute
    :param bool keyable: (Optional) If the attribute is keyable. Default True.
    :param bool readable: (Optional) If the attribute can have outgoing connections. Default True.
    :param bool writable: (Optional) If the attribute can have incoming connections. Default True.
    :param bool storable: (Optional) If the attribute can be stored to a file. Default True.
    :param bool channelBox: (Optional) If the attribute is non-keyable should it be in the channel box.

    :return: newly added attribute
    :rtype: str
    """
    if hasAttr(node, longName):
        logger.warning("Attribute {1}, already exists on {0}".format(node, longName))
        return

    data = dict()
    if shortName is not None:
        data["shortName"] = shortName
    if niceName is not None:
        data["niceName"] = niceName

    data["attributeType"] = "enum"
    data["en"] = ":".join([str(x) for x in enum])

    data["keyable"] = keyable
    data["readable"] = readable
    data["storable"] = storable
    data["writable"] = writable

    cmds.addAttr(node, longName=longName, **data)
    plug = str(node + "." + longName)
    if value:
        cmds.setAttr(plug, value)
    if channelBox:
        cmds.setAttr(plug, channelBox=True)
    return plug


def addSeparator(node, label, repeat=4):
    """
    Add a separator attribute to visually separate groups of attributes.
    Separator is an enum

    :param str node: Node to add the separator too
    :param str label: Label of the separator
    :param int repeat: Number of times to repeat the "-" character. default is 16
    :return: The plug of the separator added
    :rtype: str
    """
    existing = [str(i) for i in cmds.listAttr(node, userDefined=True) or [] if i.startswith("sep")]
    sep = "sep" + str(len(existing))

    createEnum(node, longName=sep, niceName=("-" * repeat), enum=[label])
    plug = node + "." + sep
    cmds.setAttr(plug, keyable=True, channelBox=True)

    return plug


def createProxy(sources, targets):
    """
    Add a proxy attribute to the list of target nodes.

    :param str list sources: source attributes to add to the proxy attributes
    :param str list targets: list of target nodes to add the proxy attribute
    """
    sources = common.toList(sources)
    targets = common.toList(targets)

    for sourceAttr in sources:
        for target in targets:
            attrName = cmds.attributeName(sourceAttr, long=True)
            # If an attribute already exits, a new attrName from the full attribute name.
            if cmds.attributeQuery(attrName, node=target, exists=True):
                attrName = "{}_{}".format(sourceAttr.split(".")[0], attrName)

            # Add the attribute if it does not exist. otherwise throw an error.
            if not cmds.attributeQuery(attrName, node=target, exists=True):
                cmds.addAttr(target, longName=attrName, proxy=sourceAttr)
            else:
                logger.error("Attribute {} already exists. Cannot make a proxy".format(target + "." + attrName))


# We need alot of arguments here
# pylint:disable=too-many-arguments
def createColorAttr(
    node,
    longName,
    value=False,
    niceName=None,
    shortName=None,
    keyable=True,
    readable=True,
    storable=True,
    writable=True,
    channelBox=False,
    channelBoxType="rgb",
):
    """
    Add a new attribute to the provided node.

    :param str list node: Node to add the attribute to
    :param str longName: Long name of the attribute
    :param list tuple value: (Optional) Default color of the attribute. Set in RGB values from 0-1. Unless channelboxType is 'hsv'
    :param str niceName: (Optional) Nice name of the attribute
    :param str shortName: (Optional) Short name of the attribute
    :param bool keyable: (Optional) If the attribute is keyable. Default True.
    :param bool readable: (Optional) If the attribute can have outgoing connections. Default True.
    :param bool writable: (Optional) If the attribute can have incoming connections. Default True.
    :param bool storable: (Optional) If the attribute can be stored to a file. Default True.
    :param bool channelBox: (Optional) If the attribute is non-keyable should it be in the channel box.
    :param str channelBoxType: (Optional) how to add the color attribute to the channel box. types are 'rgb' or 'hsv'

    :return: Plug of the  Attribute Added
    :rtype: str
    """
    if hasAttr(node, longName):
        logger.warning("Attribute {1}, already exists on {0}".format(node, longName))
        return
    data = {
        "attributeType": "float3",
        "usedAsColor": True,
        "keyable": keyable,
        "readable": readable,
        "storable": storable,
        "writable": writable,
    }

    dataChild = {"attributeType": "float", "parent": longName}

    if shortName is not None:
        data["shortName"] = shortName
    if niceName is not None:
        data["niceName"] = niceName

    cmds.addAttr(node, longName=longName, **data)
    cmds.addAttr(node, longName=longName + "_r", **dataChild)
    cmds.addAttr(node, longName=longName + "_g", **dataChild)
    cmds.addAttr(node, longName=longName + "_b", **dataChild)

    # if channel box is on. Make a couple float attributes to control the color.
    if channelBox:
        if channelBoxType == "rgb":
            rChannel = createAttr(node, longName + "R", attributeType="float", minValue=0, maxValue=1)
            gChannel = createAttr(node, longName + "G", attributeType="float", minValue=0, maxValue=1)
            bChannel = createAttr(node, longName + "B", attributeType="float", minValue=0, maxValue=1)

            cmds.connectAttr(rChannel, node + "." + longName + "_r", force=True)
            cmds.connectAttr(gChannel, node + "." + longName + "_g", force=True)
            cmds.connectAttr(bChannel, node + "." + longName + "_b", force=True)

            if value:
                cmds.setAttr(rChannel, value[0])
                cmds.setAttr(gChannel, value[1])
                cmds.setAttr(bChannel, value[2])

        elif channelBoxType == "hsv":
            hueChannel = createAttr(node, longName + "Hue", attributeType="float", minValue=0, maxValue=1)
            satChannel = createAttr(node, longName + "Sat", attributeType="float", minValue=0, maxValue=1)
            valChannel = createAttr(node, longName + "Val", attributeType="float", minValue=0, maxValue=1)
            hsvNode = cmds.createNode("hsvToRgb", name=node + "_" + longName + "_hsv")
            hueMult = cmds.createNode("multDoubleLinear", name=node + "_" + longName + "_hue_mdl")

            cmds.connectAttr(hueChannel, hueMult + ".input1")
            cmds.setAttr(hueMult + ".input2", 360)

            cmds.connectAttr(hueMult + ".output", hsvNode + ".inHsvR", force=True)
            cmds.connectAttr(satChannel, hsvNode + ".inHsvG", force=True)
            cmds.connectAttr(valChannel, hsvNode + ".inHsvB", force=True)
            cmds.connectAttr(hsvNode + ".outRgb", node + "." + longName)
            if value:
                cmds.setAttr(hueChannel, value[0])
                cmds.setAttr(satChannel, value[1])
                cmds.setAttr(valChannel, value[2])

        else:
            logger.error(
                "{} is not a valid channel box type. Channel box types are: 'rgb', 'hsv'".format(channelBoxType)
            )
    else:
        if value:
            cmds.setAttr(node + "_r", value[0])
            cmds.setAttr(node + "_g", value[1])
            cmds.setAttr(node + "_b", value[2])

    return str(node + "." + longName)


def copyAttribute(attr, source, target):
    """
    Create a copy of an attribute on a new target node

    :param str attr: name of the  attribute to move
    :param str source: name of the source node of the attribute
    :param str target:name of the node to move the attribute to
    """
    if not cmds.objExists("{}.{}".format(source, attr)):
        raise RuntimeError("Source attribute {}.{} does not exist".format(source, attr))

    if not cmds.objExists("{}.{}".format(target, attr)):
        kwargs = dict()
        kwargs["niceName"] = cmds.attributeQuery(attr, node=source, niceName=True)
        kwargs["keyable"] = cmds.getAttr("{}.{}".format(source, attr), keyable=True)
        kwargs["channelBox"] = cmds.getAttr("{}.{}".format(source, attr), channelBox=True)
        value = cmds.getAttr("{}.{}".format(source, attr))

        # add Enum
        if cmds.attributeQuery(attr, node=source, listEnum=True):
            kwargs["enum"] = cmds.attributeQuery(attr, node=source, listEnum=True)
            createEnum(target, longName=attr, **kwargs)

        # add attr
        else:
            kwargs["attributeType"] = cmds.attributeQuery(attr, node=source, attributeType=True)
            if cmds.attributeQuery(attr, node=source, minExists=True):  # check if the attribute has a minimum
                kwargs["minValue"] = cmds.attributeQuery(attr, node=source, minimum=True)[0]
            if cmds.attributeQuery(attr, node=source, maxExists=True):  # check if the attribute has a maximum
                kwargs["maxValue"] = cmds.attributeQuery(attr, node=source, maximum=True)[0]
            createAttr(target, longName=attr, **kwargs)

        cmds.setAttr("{}.{}".format(target, attr), value)  # set the value of the attribtue


def moveAttribute(attr, source, target):
    """
    Move an attribute from one node to another node while  keeping the connections intact.

    :param str attr: attribute to move
    :param str source: source node of the attribute
    :param str target: node to move the attribute to
    """
    copyAttribute(attr=attr, source=source, target=target)

    sourceConnections = (
        cmds.listConnections("{}.{}".format(source, attr), source=True, destination=False, plugs=True) or []
    )
    destConnections = (
        cmds.listConnections("{}.{}".format(source, attr), destination=True, source=False, plugs=True) or []
    )

    # connect source and  destination attributes
    for plug in sourceConnections:
        cmds.connectAttr(plug, "{}.{}".format(target, attr), force=True)
    for plug in destConnections:
        cmds.connectAttr("{}.{}".format(target, attr), plug, force=True)


def driveAttribute(attr, source, target, forceVisable=False, multiplier=None):
    """
    Create an identical attribute on a target node and connect it to the source.
    Essnetially this is like moving an attribute, but it still keeps the final output on the source node.

    :param str attr: attribute to move
    :param str source: source node of the attribute
    :param str target: node to move the attribute to
    :param bool forceVisable: force the target attribute to be visable in the channel box
    :param float multiplier: multiply the driven attr by a number
    """
    copyAttribute(attr=attr, source=source, target=target)
    if multiplier:
        multNode = cmds.createNode("multDoubleLinear", name=f"{source}_{attr}_mdl")
        cmds.connectAttr(f"{target}.{attr}", f"{multNode}.input1")
        cmds.setAttr(f"{multNode}.input2", multiplier)
        cmds.connectAttr(f"{multNode}.output", f"{source}.{attr}", force=True)

    else:
        cmds.connectAttr(f"{target}.{attr}", f"{source}.{attr}", force=True)

    if forceVisable:
        cmds.setAttr(f"{target}.{attr}", keyable=True)


def unlock(nodes, attrs):
    """
    Unlock Attributes on a node

    :param  str list nodes: Node with attributes to act on
    :param str list attrs: Attributes to act on
    """
    _editAttrParams(nodes, attrs, lock=False)


def lock(nodes, attrs):
    """
    Lock attributes on a node

    :param  str list nodes: Node with attributes to act on
    :param str list attrs: Attributes to act on
    """
    _editAttrParams(nodes, attrs, lock=True)


def hide(nodes, attrs):
    """
    hide attributes on a node

    :param str list nodes: Node with attributes to act on
    :param str list attrs: Attributes to act on
    """
    _editAttrParams(nodes, attrs, channelBox=False, keyable=False)


def unhide(nodes, attrs):
    """
    Unlock attributes on a node

    :param str list nodes: Node with attributes to act on
    :param str list attrs: Attributes to act on
    """
    _editAttrParams(nodes, attrs, keyable=False, channelBox=True)
    _editAttrParams(nodes, attrs, keyable=True)


def lockAndHide(nodes, attrs):
    """
    Lock and hide attributes on a node

    :param str list nodes: Node with attributes to act on
    :param str list attrs: Attributes to act on
    """
    lock(nodes, attrs)
    hide(nodes, attrs)


def unlockAndUnhide(nodes, attrs):
    """
    Unlock and unhide attributes on a node

    :param str list nodes: Node with attributes to act on
    :param str list attrs: Attributes to act on
    """
    unhide(nodes, attrs)
    unlock(nodes, attrs)


def nonKeyable(nodes, attrs):
    """
    Makes attributes display only in the channel box

    :param str list nodes: Node with attributes to act on
    :param str list attrs: Attributes to act on
    """
    _editAttrParams(nodes, attrs, keyable=False, channelBox=True)


def keyable(nodes, attrs):
    """
    Makes attributes keyable in the channel box

    :param str list nodes: Node with attributes to act on
    :param str list attrs: Attributes to act on
    """
    _editAttrParams(nodes, attrs, keyable=True, lock=False)


def setAttr(nodes, attrs, value):
    """
    Set the value of given nodes and attributes to a given value

    :param str list nodes: Nodes with attributes to set the value of
    :param str list  attrs: Attributes to set the value of
    :param value: Value to set the attributes to
    """
    if not isinstance(nodes, list):
        nodes = [nodes]

    if not isinstance(attrs, list):
        attrs = [attrs]

    for node in nodes:
        for attr in attrs:
            plug = node + "." + attr
            setPlugValue(plug, value)


def resetDefault(nodes, attrs):
    """
    Reset the given attributes to a default value.
    For Transforms its their identity matrix (Translate and rotate [0,0,0] and scale [1,1,1]).
    For User defined attributes its their default value if one is provided. Otherwise it defaults to 0.
    Note: attributes of type bool, string and matrix do not have a default value and therefore cannot be reset.

    :param str list nodes:

    :param str list attrs:
    """

    if not isinstance(nodes, list):
        nodes = [nodes]

    if not isinstance(attrs, list):
        attrs = [attrs]

    for node in nodes:
        for attr in attrs:
            plug = _getPlug(node + "." + attr)
            pAttribute = plug.attribute()
            apiType = pAttribute.apiType()
            if apiType is not om2.MFn.kTypedAttribute:
                if not plug.isCompound:
                    defaultValue = cmds.attributeQuery(attr, node=node, listDefault=True)
                    if defaultValue:
                        setAttr(node, attr, defaultValue[0])


def disconnectAttrs(node, source=True, destination=True, skipAttrs=None):
    """
    disconnect all  connections between a source and node.

    :param str node: node to disconnect attributes from
    :param bool source: Disconnect all attributes on the source side of the connection
    :param bool destination:Disconnect all attributes on the destination side of the connection
    :param list skipAttrs: list of attributes we dont want to skip
    """
    if skipAttrs is None:
        skipAttrs = list()

    connectionPairs = []
    skipAttrs = common.toList(skipAttrs)
    if source:
        conns = cmds.listConnections(node, plugs=True, connections=True, destination=False)
        if conns:
            connectionPairs.extend(zip(conns[1::2], conns[::2]))

    if destination:
        conns = cmds.listConnections(node, plugs=True, connections=True, source=False)
        if conns:
            connectionPairs.extend(zip(conns[::2], conns[1::2]))

    if skipAttrs:
        for pair in connectionPairs:
            for skipAttr in skipAttrs:
                if "{}.{}".format(node, skipAttr) in pair:
                    connectionPairs.remove(pair)

    for srcAttr, destAttr in connectionPairs:
        cmds.disconnectAttr(srcAttr, destAttr)


def hasAttr(node, attr):
    """
    Check if a node has an attribute

    :param str node: Node to check for attribute
    :param str attr: Attribute to check for
    :return: If the attribute exists on the node
    :rtype: bool
    """
    return True if cmds.attributeQuery(attr, exists=True, node=node) else False


# disable the name checking because we want this to be like a constant
# pylint:disable=invalid-name
def USER(node):
    """
    Get user defined attributes of a node

    :param str node: Node to retreive attributes from
    """
    return list([str(a) for a in cmds.listAttr(node, userDefined=True) or [] if "." not in a])


# disable the name checking because we want this to be like a constant
# pylint:disable=invalid-name
def KEYABLE(node):
    """
    Get keyable attributes of a node

    :param str node: Node to retreive attributes from
    """
    return list([str(a) for a in cmds.listAttr(node, keyable=True) or [] if "." not in a])


# disable the name checking because we want this to be like a constant
# pylint:disable=invalid-name
def NONKEYABLE(node):
    """
    Get non keyable attributes of a node

    :param str node: Node to retreive attributes from
    """
    return list([str(a) for a in cmds.listAttr(node, channelBox=True) or [] if "." not in a])


# disable the name checking because we want this to be like a constant
# pylint:disable=invalid-name
def CHANNELBOX(node):
    """
    Get attributes in the channelbox of a node

    :param str node: Node to retreive attributes from
    """
    return KEYABLE(node) + NONKEYABLE(node)


# disable the name checking because we want this to be like a constant
# pylint:disable=invalid-name
def ALL(node):
    """
    Get all attribues of a node

    :param str node: Node to retreive attributes from
    """
    return list([str(a) for a in cmds.listAttr(node) or [] if "." not in a])


def _editAttrParams(nodes, attrs, channelBox: bool = -1, lock: bool = -1, keyable: bool = -1):
    if not isinstance(nodes, list):
        nodes = [nodes]

    if not isinstance(attrs, list):
        attrs = [attrs]

    for node in nodes:
        for attr in attrs:
            if isCompound("{}.{}".format(node, attr)):
                childPlugs = getCompoundChildren("{}.{}".format(node, attr))
                childAttrs = [a.split(".")[-1] for a in childPlugs]
                if childAttrs not in attrs:
                    attrs += childAttrs

            if lock != -1:
                cmds.setAttr(node + "." + attr, lock=lock)
            if keyable != -1:
                cmds.setAttr(node + "." + attr, keyable=keyable)
            if channelBox != -1:
                cmds.setAttr(node + "." + attr, channelBox=channelBox)


def reorderToBottom(node, attr):
    """
    Move attribute to the bottom of channel box.

    :param str node: Node to modify attributes on
    :param str attr: attribute
    """
    cmds.deleteAttr(node, attribute=attr)
    cmds.undo()


def reorderAttr(plug, pos="bottom"):
    """
    Reorder attributes

    :param str plug: Attribute to reorder
    :param str pos: Reorder position. ["up", "down", "top" and "bottom"]
    """
    if not cmds.objExists(plug):
        raise RuntimeError('Attribute "' + plug + '" does not exist!')
    node = plug.split(".")[0]
    attr = plug.replace(node + ".", "")

    allAttrList = [i for i in USER(node) if KEYABLE(node).count(i) or CHANNELBOX(node).count(i)]
    allAttrLen = len(allAttrList)
    attrInd = allAttrList.index(attr)

    # reorder up
    if pos == "up":
        if not attrInd:
            return
        reorderToBottom(node, allAttrList[attrInd - 1])
        for i in allAttrList[attrInd + 1 :]:
            reorderToBottom(node, i)

    # reorder down
    if pos == "down":
        if attrInd == (allAttrLen - 1):
            return
        reorderToBottom(node, allAttrList[attrInd])
        if attrInd >= (allAttrLen - 1):
            return
        for i in allAttrList[attrInd + 2 :]:
            reorderToBottom(node, i)

    # reorder top
    if pos == "top":
        for i in range(len(allAttrList)):
            if i == attrInd:
                return
            reorderToBottom(node, allAttrList[i])

    # reorder bottom
    if pos == "bottom":
        reorderToBottom(node, allAttrList[attrInd])

    # Refresh UI
    cmds.channelBox("mainChannelBox", edit=True, update=True)


def getNextAvailableElement(plug):
    """
    Get the next available index of a multi or array attribute.
    ie.  `node.exampleAttray[0]` has a connection it will return `node.exampleAttray[1]`

    :param str plug: plug to get the next available element of
    :return: The name of the next available plug
    :rtype: bool
    """
    if not isinstance(plug, om2.MPlug):
        plug = _getPlug(plug)

    if not plug:
        raise RuntimeError("Plug not found")

    return plug.elementByLogicalIndex(plug.evaluateNumElements())


def isCompound(plug: Union[om2.MPlug, str]):
    """
    Check if the attribute is a multi attribute

    :param str plug: plug to check
    :return: True if the plug is a compound attribute
    :rtype: bool
    """
    if not isinstance(plug, om2.MPlug):
        plug = _getPlug(plug)

    if not plug:
        raise RuntimeError("Plug not found")

    pAttribute = plug.attribute()
    apiType = pAttribute.apiType()

    if apiType in [
        om2.MFn.kAttribute3Double,
        om2.MFn.kAttribute3Float,
        om2.MFn.kCompoundAttribute,
    ]:
        if plug.isCompound:
            return True
    return False


def getCompoundChildren(plug: Union[om2.MPlug, str]):
    """
    Get the children of a compound plug.
    ie: 'pCube.t' will return ['pCube.tx', 'pCube.ty', 'pCube.tz']

    :param om2.MPlug str plug: plug to get children of
    :return: list of child plugs
    :rtype: list
    """
    if not isinstance(plug, om2.MPlug):
        plug = _getPlug(plug)

    if not plug:
        raise RuntimeError("Plug not found")

    # if the plug is not a compound plug return the plug as a string.
    if not isCompound(plug):
        return str(plug)
    childPlugs = list()
    if plug.isCompound:
        for i in range(plug.numChildren()):
            compoundChild = plug.child(i)
            childPlugs.append(str(compoundChild))
    return childPlugs


def _getPlug(plug):
    """
    Return the MPlug object for the specified attribute

    :param str attr: The attribute to return the MPlug for
    """
    # Check attribute
    parts = plug.split(".")
    node = parts[0]
    attr = ".".join(parts[1:])
    baseAttr = parts[1].split("[")[0]

    # get node function set
    selList = om2.MSelectionList()
    selList.add(node)
    nodeObject = selList.getDependNode(0)
    nodeFn = om2.MFnDependencyNode(nodeObject)

    # get plug
    if len(parts) > 2 or "[" in attr:
        # compound attrs
        if nodeFn.hasAttribute(baseAttr):
            # child plugs iterator
            def _getChildPlugs(p):
                a = p.attribute()
                apiType = a.apiType()
                childPlugs.append(p)
                if p.isArray:
                    if apiType == om2.MFn.kTypedAttribute:
                        for i in xrange(p.numElements()):
                            compountAttr = p.elementByLogicalIndex(i)
                            _getChildPlugs(compountAttr)
                    elif apiType == om2.MFn.kMessageAttribute:
                        childPlugs.append(p)
                    else:
                        numChildren = int()
                        try:
                            numChildren = p.numElements()
                        except TypeError:
                            pass
                        try:
                            numChildren = p.numChildren()
                        except TypeError:
                            pass
                        for i in range(numChildren):
                            compountAttr = om2.MPlug(p.elementByLogicalIndex(i))
                            _getChildPlugs(compountAttr)
                elif p.isCompound:
                    for i in range(p.numChildren()):
                        compountAttr = p.child(i)
                        _getChildPlugs(compountAttr)

            # get child plugs
            childPlugs = list()
            basePlug = nodeFn.findPlug(baseAttr, True)
            _getChildPlugs(basePlug)

            for childPlug in childPlugs:
                if childPlug.name().partition(".")[-1] == attr:
                    return childPlug
    else:
        # simple attrs
        if nodeFn.hasAttribute(attr):
            return nodeFn.findPlug(attr, True)

    logger.warning("Plug {} could not be found.".format(plug))
    return


# pylint: disable=too-many-return-statements
def getPlugValue(plug):
    """
    Gets the value of the given plug.

    :param MPlug plug:The node plug.

    :return: The value of the passed in node plug.
    """

    if not isinstance(plug, om2.MPlug):
        plug = _getPlug(plug)

    if not plug:
        raise RuntimeError("Plug not found")

    pAttribute = plug.attribute()
    apiType = pAttribute.apiType()

    # Float Groups - rotate, translate, scale; Compounds
    if apiType in [
        om2.MFn.kAttribute3Double,
        om2.MFn.kAttribute3Float,
        om2.MFn.kCompoundAttribute,
    ]:
        result = []

        if plug.isCompound:
            for c in xrange(plug.numChildren()):
                result.append(getPlugValue(plug.child(c)))
            return result

    # Distance
    elif apiType in [om2.MFn.kDoubleLinearAttribute, om2.MFn.kFloatLinearAttribute]:
        return plug.asMDistance().asCentimeters()

    # Angle
    elif apiType in [om2.MFn.kDoubleAngleAttribute, om2.MFn.kFloatAngleAttribute]:
        return plug.asMAngle().asDegrees()

    # TYPED
    elif apiType == om2.MFn.kTypedAttribute:
        pType = om2.MFnTypedAttribute(pAttribute).attrType()

        # Matrix
        if pType == om2.MFnData.kMatrix:
            return om2.MFnMatrixData(plug.asMObject()).matrix()

        # String
        elif pType == om2.MFnData.kString:
            return plug.asString()

    # MATRIX
    elif apiType == om2.MFn.kMatrixAttribute:
        return om2.MFnMatrixData(plug.asMObject()).matrix()

    # NUMBERS
    elif apiType == om2.MFn.kNumericAttribute:
        pType = om2.MFnNumericAttribute(pAttribute).numericType()
        if pType == om2.MFnNumericData.kBoolean:
            return plug.asBool()

        elif pType in [
            om2.MFnNumericData.kShort,
            om2.MFnNumericData.kInt,
            om2.MFnNumericData.kLong,
            om2.MFnNumericData.kByte,
        ]:
            return plug.asInt()
        elif pType in [
            om2.MFnNumericData.kFloat,
            om2.MFnNumericData.kDouble,
            om2.MFnNumericData.kAddr,
        ]:
            return plug.asDouble()

    # Enum
    elif apiType == om2.MFn.kEnumAttribute:
        return plug.asInt()


# this is a long function with alot of checks
# pylint: disable=too-many-statements
# pylint: disable=too-many-branches
def setPlugValue(plug, value):
    """
    Sets the given plug's value to the passed in value.

    :param MPlug plug: The node plug.
    :param value: Any value of any data type.
    """
    if not isinstance(plug, om2.MPlug):
        plug = _getPlug(plug)

    if not plug:
        raise RuntimeError("Plug not found")

    plugAttribute = plug.attribute()
    apiType = plugAttribute.apiType()

    # Float Groups - rotate, translate, scale
    if apiType in [om2.MFn.kAttribute3Double, om2.MFn.kAttribute3Float]:
        result = []
        if plug.isCompound:
            if isinstance(value, list):
                for c in xrange(plug.numChildren()):
                    result.append(setPlugValue(plug.child(c), value[c]))
                return result

            elif isinstance(value, om2.MEulerRotation):
                setPlugValue(plug.child(0), value.x)
                setPlugValue(plug.child(1), value.y)
                setPlugValue(plug.child(2), value.z)
            else:
                raise RuntimeError(
                    "{0} :: Passed in value ( {1} ) is {2}. Needs to be type list.".format(
                        plug.info, value, type(value)
                    )
                )

    # Distance
    elif apiType in [om2.MFn.kDoubleLinearAttribute, om2.MFn.kFloatLinearAttribute]:
        if isinstance(value, float):
            value = om2.MDistance(value, om2.MDistance.kCentimeters)
            plug.setMDistance(value)
        elif isinstance(value, int):
            value = float(value)
            value = om2.MDistance(value, om2.MDistance.kCentimeters)
            plug.setMDistance(value)
        else:
            raise RuntimeError(
                "{0} :: Passed in value ( {1} ) is {2}. Needs to be type float or int.".format(
                    plug.info, value, type(value)
                )
            )

    # Angle
    elif apiType in [om2.MFn.kDoubleAngleAttribute, om2.MFn.kFloatAngleAttribute]:
        if isinstance(value, float):
            value = om2.MAngle(value, om2.MAngle.kDegrees)
            plug.setMAngle(value)
        elif isinstance(value, int):
            value = float(value)
            value = om2.MAngle(value, om2.MAngle.kDegrees)
            plug.setMAngle(value)
        else:
            raise RuntimeError(
                "{0} :: Passed in value ( {1} ) is {2}. Needs to be type float.".format(plug.info, value, type(value))
            )

    # Typed - matrix WE DON'T HANDLE THIS CASE YET!!!!!!!!!
    elif apiType == om2.MFn.kTypedAttribute:
        pType = om2.MFnTypedAttribute(plugAttribute).attrType()
        if pType == om2.MFnData.kMatrix:
            if isinstance(value, om2.MPlug):
                pass
            else:
                plugNode = plug.node()
                mfnTransform = om2.MFnTransform(plugNode)
                sourceMatrix = om2.MTransformationMatrix(value)  # .asMatrix()
                mfnTransform.set(sourceMatrix)

        # String
        elif pType == om2.MFnData.kString:
            value = str(value)
            plug.setString(value)

    # MATRIX
    elif apiType == om2.MFn.kMatrixAttribute:
        if isinstance(value, om2.MPlug):
            # value must be a MPlug!
            sourceValueAsMObject = om2.MFnMatrixData(value.asMObject()).object()
            plug.setMObject(sourceValueAsMObject)
        else:
            raise RuntimeError(
                "Value object is not an MPlug. To set a MMatrix value, both passed in variables must be MPlugs."
            )

    # Numbers
    elif apiType == om2.MFn.kNumericAttribute:
        pType = om2.MFnNumericAttribute(plugAttribute).numericType()
        if pType == om2.MFnNumericData.kBoolean:
            if isinstance(value, bool):
                plug.setBool(value)
            elif isinstance(value, int) and value == 1 or value == 0:
                plug.setBool(bool(value))
            elif isinstance(value, float) and value == 1.0 or value == 0.0:
                plug.setBool(bool(value))
            else:
                raise RuntimeError(
                    "{0} :: Passed in value ( {1} ) is {2}. Needs to be type bool.".format(
                        plug.info, value, type(value)
                    )
                )

        elif pType in [
            om2.MFnNumericData.kShort,
            om2.MFnNumericData.kInt,
            om2.MFnNumericData.kLong,
            om2.MFnNumericData.kByte,
        ]:
            value = int(value)
            if isinstance(value, int):
                plug.setInt(value)
            elif isinstance(value, float):
                plug.setInt(int(value))
            else:
                raise RuntimeError(
                    "{0} :: Passed in value ( {1} ) is {2}. Needs to be type int or float.".format(
                        plug.info, value, type(value)
                    )
                )

        elif pType in [
            om2.MFnNumericData.kFloat,
            om2.MFnNumericData.kDouble,
            om2.MFnNumericData.kAddr,
        ]:
            if isinstance(value, float):
                plug.setDouble(value)
            elif isinstance(value, int):
                plug.setDouble(float(value))
            else:
                raise RuntimeError(
                    "{0} :: Passed in value ( {1} ) is {2}. Needs to be type float or int.".format(
                        plug.info, value, type(value)
                    )
                )

    # Enums
    elif apiType == om2.MFn.kEnumAttribute:
        plug.setInt(value)
