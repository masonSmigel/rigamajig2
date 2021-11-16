"""
Functions to add metadata to nodes
"""
import maya.cmds as cmds
import rigamajig2.shared.common as common


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


def messageNameConnection(sourceNode, dataNode, dataAttr):
    """
    Add a message connection between a source and target node
    :param sourceNode: source node of the message connection
    :param dataNode: destination of the message connection
    :param dataAttr: name of the destination attribute
    """
    if cmds.objExists("{}.{}".format(dataNode, dataAttr)):
        raise RuntimeError("The desination '{}.{}' already exist".format(dataNode, dataAttr))
    cmds.addAttr(dataNode, ln=dataAttr, at='message')
    cmds.connectAttr("{}.{}".format(sourceNode, 'message'), "{}.{}".format(dataNode, dataAttr))


def getMessageConnection(dataPlug, silent=True):
    """
    Get the data connected to the given plug.
    :param dataPlug: plug to get the message for
    :param silent: if the function fails return None instead of erroring
    :return:
    """

    if cmds.objExists(dataPlug):
        return common.getFirstIndex(cmds.listConnections(dataPlug, d=True))
    elif not silent:
        raise RuntimeError('Plug "{}" does not exist'.format(dataPlug))
    else:
        return None
