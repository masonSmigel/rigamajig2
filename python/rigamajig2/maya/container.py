"""
Functions for working with containers
"""
import logging
from typing import *

import maya.cmds as cmds

import rigamajig2.shared.common as common

logger = logging.getLogger(__name__)


class InvalidContainer(Exception):
    pass


Multiuse = Union[List[str], str]


def isContainer(name: str) -> bool:
    """
    Check if the node is a valid Container

    :param str name: Node to check
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    if not cmds.objExists(name):
        return False
    if "containerBase" not in cmds.nodeType(name, inherited=True):
        return False
    return True


def create(name: str, nodes=None, dagContainer=False):
    """
    Create a new container

    :param str name: name of the new container to create
    :param list str nodes: nodes to put in the newly created container
    :param bool dagContainer: create a DAG container if True else create  a DG container
    :return: name of the container created
    :rtype: str
    """
    if cmds.objExists(name):
        raise InvalidContainer(
            "Object {} already exists. Cannot create a container with that name".format(
                name
            )
        )
    if nodes:
        for node in nodes:
            if not cmds.objExists(node):
                raise RuntimeError(
                    "Node {} does not exist. Cannot add it to the container".format(
                        node
                    )
                )

    if not dagContainer:
        containerNode = cmds.container(name=name)
    else:
        containerNode = cmds.container(name=name, type="dagContainer")

    if nodes:
        cmds.container(containerNode, edit=True, addNode=nodes, force=True)

    return containerNode


def addNodes(nodes: Union[List[str], str], container, addShape=True, force=False):
    """
    Add nodes to a container.

    :param list nodes: nodes to add to the container
    :param str container: name of the container
    :param bool addShape: add the shapes to the containter too
    :return: nodes added to the container
    :rtype: list
    """
    if not isContainer(container):
        raise InvalidContainer("{} is not a container.".format(container))

    cmds.container(container, edit=True, addNode=nodes, force=force)
    if addShape:
        nodes = common.toList(nodes)
        for node in nodes:
            shapes = cmds.listRelatives(node, shapes=True)
            if shapes:
                cmds.container(container, edit=True, addNode=shapes, force=force)
    return nodes


def removeNodes(nodes, container, removeShapes=True):
    """
    remove nodes from the given container

    :param list nodes: nodes to remove from the container
    :param str container: name of the container
    :param bool removeShapes: remove the shapes from the containter too
    :return: nodes removed from the container
    :rtype: list
    """
    if not isContainer(container):
        logger.error("{} is not a container.".format(container))
        return None
    cmds.container(container, edit=True, removeNode=nodes)
    nodes = common.toList(nodes)
    if removeShapes:
        for node in nodes:
            shapes = cmds.listRelatives(node, shapes=True)
            if shapes:
                cmds.container(container, edit=True, removeNode=shapes)


def getNodesInContainer(container, getSubContained=False):
    """
    get the nodes within a container

    :param str container: container
    :param bool getSubContained: get nodes within subcontainers
    :return: list of nodes within the container
    :rtype: list
    """
    if not isContainer(container):
        raise InvalidContainer("{} is not a container.".format(container))
    nodeList = cmds.container(container, query=True, nodeList=True) or []

    # we also need to get nodes from subcontainers
    if getSubContained:
        subContainers = cmds.ls(nodeList, type="container")
        for subContainer in subContainers:
            subNodeList = cmds.container(subContainer, query=True, nodeList=True) or []
            nodeList += subNodeList

    return nodeList


def getContainerFromNode(node: Multiuse) -> str:
    """
    Get the parent container from a node

    :param str node: Name of the node
    :return : The container that holds the given node
    :rtype: list
    """
    node = common.getFirstIndex(node)
    containerNode = cmds.container(query=True, findContainer=node)
    return containerNode


def addPublishAttr(attr, assetAttrName=None, bind=True):
    """
    Publish an attribute

    :param str attr: contained node attribute to publish. Attribute should be listed as a plug:
    :param str assetAttrName: Name used on the container. if node it will be auto generated from the node and attr name
    :param bool bind: bind the publish node to the container
    """
    if not cmds.objExists(attr):
        raise RuntimeError(
            "Attribute {} does not exist. Cannot publish attribute".format(attr)
        )

    if not assetAttrName:
        assetAttrName = attr.replace(".", "_")

    node = cmds.ls(attr, objectsOnly=True)
    containerNode = getContainerFromNode(node)

    cmds.container(containerNode, edit=True, publishName=assetAttrName)
    if bind:
        cmds.container(containerNode, edit=True, bindAttr=(attr, assetAttrName))

    return containerNode + "." + assetAttrName


def addPublishNodes(nodes, container=None, bind=True):
    """
    Publish a node.

    :param str list nodes: contained node to publish.
    :param str container: Optional- specify a container to add nodes to if nodes are not in a container
    :param bool bind: bind the publish node to the container
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if not cmds.objExists(node):
            raise RuntimeError(
                "Node {} does not exist. Cannot publish Node".format(node)
            )

        assetNodeName = node

        containerNode = getContainerFromNode(node)
        if not containerNode:
            if not container:
                raise Exception(
                    "{} is not a part of a container and no container specified".format(
                        node
                    )
                )
            addNodes(node, container)
            containerNode = container

        containedNodes = cmds.containerPublish(
            containerNode, query=True, publishNode=True
        )
        if not containedNodes:
            containedNodes = list()
        if node not in containedNodes:
            cmds.containerPublish(containerNode, publishNode=(node, "transform"))
            if bind:
                cmds.containerPublish(containerNode, bindNode=(node, assetNodeName))


def addParentAnchor(node, container=None, assetNodeName: str = None):
    """
    Publish a node as the parent Anchor

    :param node: nodes to make an anchor parent
    :param str container: (Optional)- specify a container to add nodes to if nodes are not in a container
    :param str assetNodeName: (Optional)- alias name for the node attribute in the container
    """
    node = common.getFirstIndex(node)
    if not cmds.objExists(node):
        raise RuntimeError("Node {} does not exist. Cannot publish Node".format(node))

    if not assetNodeName:
        assetNodeName = "parent"

    containerNode = getContainerFromNode(node)
    if not containerNode:
        if not container:
            raise Exception(
                "{} is not a part of a container and no container specified".format(
                    node
                )
            )
        addNodes(node, container)
        containerNode = container

    cmds.container(containerNode, edit=True, publishAsParent=(node, assetNodeName))


def addChildAnchor(node, container=None, assetNodeName=None):
    """
    Publish a node as the child Anchor

    :param node: nodes to make an anchor child
    :param container: Optional- specify a container to add nodes to if nodes are not in a container
    :param assetNodeName: (Optional)- alias name for the node attribute in the container
    """
    node = common.getFirstIndex(node)
    if not cmds.objExists(node):
        raise RuntimeError("Node {} does not exist. Cannot publish Node".format(node))

    if not assetNodeName:
        assetNodeName = "child"

    containerNode = getContainerFromNode(node)
    if not containerNode:
        if not container:
            raise Exception(
                "{} is not a part of a container and no container specified".format(
                    node
                )
            )
        addNodes(node, container)
        containerNode = container

    cmds.container(containerNode, edit=True, publishAsChild=(node, assetNodeName))


def safeDeleteContainer(container):
    """
    Safely delete the container.
    This will delete the container without deleting any contained nodes.

    :param str container: container to delete
    """
    nodes = getNodesInContainer(container)
    removeNodes(nodes, container, removeShapes=False)
    cmds.delete(container)


def sainityCheck():
    """
    Run several checks to make sure maya is setup to work with containers.
    There are a couple 'gotcha's' to look out for

    First of all it will set 'use assets' OFF in the node editor

    set 'show at top' OFF in the channel box editor

    set asset display is to 'under parent'
    """

    # set 'use assets' OFF in the node editor
    cmds.nodeEditor("nodeEditorPanel1NodeEditorEd", e=True, useAssets=False)

    # set 'show at top' OFF in the channel box editor
    cmds.channelBox("mainChannelBox", edit=True, containerAtTop=False)

    # set asset centric selection to be OFF in the maya preferences
    cmds.selectPref(containerCentricSelection=False)

    # set asset display is to 'under parent'
    outliners = cmds.getPanel(type="outlinerPanel")
    for outlinerPanel in outliners:
        cmds.outlinerEditor(outlinerPanel, edit=True, showContainerContents=False)
        cmds.outlinerEditor(outlinerPanel, edit=True, showContainedOnly=False)


class ActiveContainer(object):
    """
    context to set and exit from setting an active container.

    When the context manager is active any newly created
    nodes are added to the container.
    """

    def __init__(self, container):
        """
        Set the current container to active

        :param str ontainer: name of the container
        """
        self.container = container

    def __enter__(self):
        cmds.container(self.container, edit=True, current=True)

    def __exit__(self, type, value, traceback):
        cmds.container(self.container, edit=True, current=False)
