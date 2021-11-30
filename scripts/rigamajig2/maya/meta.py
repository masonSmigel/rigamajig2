"""
Functions to add metadata to nodes
"""
import json
import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.attr as attr


def tag(nodes, tag, type=None):
    """
    Tag the specified nodes with the proper type
    :param nodes: nodes to add the tag to
    :type nodes: str | list
    :param tag: tag to add
    :type tag: str
    :param type: type of tag
    :type type: str
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.objExists(node):
            if not cmds.objExists("{}.__{}__".format(node, tag)):
                cmds.addAttr(node, ln='__{}__'.format(tag), at='message')
            if type:
                if not cmds.objExists("{}.__{}_{}__".format(node, type, tag)):
                    cmds.addAttr(node, ln='__{}_{}__'.format(type, tag), at='message')


def untag(nodes, tag):
    """
    Remove the tag from the nodes
    :param nodes: nodes to remove the tag to
    :type nodes: str | list
    :param tag: tag to remove
    :type tag: str
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.objExists(node):
            udAttrs = cmds.listAttr(node, ud=True) or list()

            for attr in udAttrs:
                if "{}__".format(tag) in attr:
                    cmds.deleteAttr("{}.{}".format(node, attr))


def getTagged(tag, namespace=None):
    """
    Get a list of all the objects with a tag in a scene.
    :param tag: tag to get
    :type tag: str
    :param namespace: Get controls found within a specific namespace
    :type namespace: str
    :return:
    """
    if not namespace:
        return [s.split(".")[0] for s in cmds.ls("*.__{}__".format(tag))]
    else:
        return [s.split(".")[0] for s in cmds.ls("{}:*.__{}__".format(namespace, tag))]


def addMessageConnection(sourceNode, dataNode, sourceAttr, dataAttr=None):
    """
    Add a message connection between a source and target node
    :param sourceNode: source node of the message connection
    :param dataNode: destination of the message connection
    :param sourceAttr: name of the source attribute
    :param dataAttr: name of the destination attribute
    """
    if cmds.objExists("{}.{}".format(dataNode, dataAttr)):
        raise RuntimeError("The desination '{}.{}' already exist".format(dataNode, dataAttr))
    if not cmds.objExists("{}.{}".format(sourceNode, sourceAttr)):
        cmds.addAttr(sourceNode, ln=sourceAttr, at='message')
    if dataAttr is None:
        dataAttr = sourceAttr
    cmds.addAttr(dataNode, ln=dataAttr, at='message')
    cmds.connectAttr("{}.{}".format(sourceNode, sourceAttr), "{}.{}".format(dataNode, dataAttr))


def addMessageListConnection(sourceNode, dataList, sourceAttr, dataAttr=None):
    """
    Add a message connection between a source and list of data nodes
    :param sourceNode: source node of the message connection
    :param dataList: destination of the message connection
    :param sourceAttr: name of the source attribute
    :param dataAttr: name of the destination attribute
    """
    dataList = common.toList(dataList)
    for dataNode in dataList:
        if cmds.objExists("{}.{}".format(dataNode, dataAttr)):
            raise RuntimeError("The desination '{}.{}' already exist".format(dataNode, dataAttr))
    if not cmds.objExists("{}.{}".format(sourceNode, sourceAttr)):
        cmds.addAttr(sourceNode, ln=sourceAttr, at='message', m=True)
    if dataAttr is None:
        dataAttr = sourceAttr
    for dataNode in dataList:
        nextIndex = attr.getNextAvailableElement("{}.{}".format(sourceNode, sourceAttr))
        print nextIndex
        cmds.addAttr(dataNode, ln=dataAttr, at='message')
        cmds.connectAttr(nextIndex, "{}.{}".format(dataNode, dataAttr))


def getMessageConnection(dataPlug, silent=True):
    """
    Get the data connected to the given plug.
    :param dataPlug: plug to get the message for
    :param silent: if the function fails return None instead of erroring
    :return: nodes connected to the message attribute. if the attribute has multiconnections return a list.
    """

    if cmds.objExists(dataPlug):
        data = cmds.listConnections(dataPlug, d=True)
        if len(data) > 1:
            return data
        else:
            return common.getFirstIndex(data)
    elif not silent:
        raise RuntimeError('Plug "{}" does not exist'.format(dataPlug))
    else:
        return None


class mayaJson(object):
    def __init__(self, node):
        self.node = node

    def getData(self):
        pass

    def setData(self):
        pass

