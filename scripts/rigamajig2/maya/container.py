"""
Functions for working with containers
"""
import maya.cmds as cmds
import rigamajig2.shared.common as common
from functools import wraps


def isContainer(name):
    """
    Check if the node is a valid Container
    :param name: Node to check
    :type name: str
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    if not cmds.objExists(name): return False
    if 'containerBase' not in cmds.nodeType(name, i=True): return False
    return True


def create(name, nodes=None, dagContainer=False):
    """
    Create a new container
    :param name:
    :param nodes:
    :param dagContainer: create a DAG container or a DG container
    :return:
    """
    if cmds.objExists(name):
        raise RuntimeError("Object {} already exists. Cannot create a container with that name".format(name))
    if nodes:
        for node in nodes:
            if not cmds.objExists(node):
                raise RuntimeError("Node {} does not exist. Cannot add it to the container".format(node))

    if not dagContainer:
        containerNode = cmds.container(n=name)
    else:
        containerNode = cmds.container(n=name, typ='dagContainer')

    if nodes: cmds.container(containerNode, e=True, addNode=nodes, f=True)

    return containerNode


def addNodes(nodes, container, addShape=True):
    """
    Add nodes to a container. If t
    :param nodes:
    :param container:
    :param addShape: add the shapes to the containter too
    :return:
    """
    if not isContainer(container):
        raise Exception("{} is not a container.".format(container))

    cmds.container(container, e=True, addNode=nodes)
    if addShape:
        nodes = common.toList(nodes)
        for node in nodes:
            shapes = cmds.listRelatives(node, s=True)
            if shapes:
                [cmds.container(container, e=True, addNode=shape) for shape in shapes]
    return nodes


def removeNodes(nodes, container, removeShapes=True):
    """
    remove nodes from the given container
    :param nodes:
    :param container:
    :param removeShapes: 
    :return:
    """
    if not isContainer(container):
        raise Exception("{} is not a container.".format(container))
    cmds.container(container, e=True, removeNode=nodes)
    nodes = common.toList(nodes)
    if removeShapes:
        for node in nodes:
            shapes = cmds.listRelatives(node, s=True)
            if shapes:
                [cmds.container(container, e=True, removeNode=shape) for shape in shapes]


def listNodes(container):
    """
    get the nodes within a container
    :param container: container
    :return: list of nodes within the container
    """
    if not isContainer(container):
        raise RuntimeError("{} is not a container.".format(container))
    nodeList = cmds.container(container, q=True, nodeList=True) or []
    return nodeList


def getContainerFromNode(node):
    """
    Get the parent container from a node
    :param node:
    :return:
    """
    node = common.getFirstIndex(node)
    containerNode = cmds.container(q=True, findContainer=node)
    return containerNode


def addPublishAttr(attr, assetAttrName=None, bind=True):
    """
    Publish an attribute
    :param attr: contained node attribute to publish. Attribute should be listed as a plug:
    :type attr: str
    :param assetAttrName: Name used on the container. if node it will be auto generated from the node and attr name
    :type assetAttrName: str
    :param bind: bind the publish node to the container
    :type bind: bool
    """
    if not cmds.objExists(attr):
        raise RuntimeError("Attribute {} does not exist. Cannot publish attribute".format(attr))

    if not assetAttrName: assetAttrName = attr.replace('.', '_')

    node = cmds.ls(attr, o=True)
    containerNode = getContainerFromNode(node)

    cmds.container(containerNode, e=True, publishName=assetAttrName)
    if bind: cmds.container(containerNode, e=True, bindAttr=[attr, assetAttrName])

    return containerNode + '.' + assetAttrName


def addPublishNodes(nodes, container=None, bind=True):
    """
    Publish a node.
    :param nodes: contained node to publish.
    :type nodes: str | list
    :param container: Optional- specify a container to add nodes to if nodes are not in a container
    :type container: str
    :param bind: bind the publish node to the container
    :type bind: bool
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if not cmds.objExists(node):
            raise RuntimeError("Node {} does not exist. Cannot publish Node".format(node))

        assetNodeName = node

        containerNode = getContainerFromNode(node)
        if not containerNode:
            if not container: raise Exception("{} is not a part of a container and no container specified".format(node))
            addNodes(node, container)
            containerNode = container

        containedNodes = cmds.containerPublish(containerNode, q=True, publishNode=True)
        if not containedNodes:
            containedNodes = list()
        if node not in containedNodes:
            cmds.containerPublish(containerNode, publishNode=[node, 'transform'])
            if bind: cmds.containerPublish(containerNode, bindNode=[node, assetNodeName])


def addParentAnchor(node, container=None, assetNodeName=None):
    """
    Publish a node as the parent Anchor
    :param node:
    :param container: Optional- specify a container to add nodes to if nodes are not in a container
    :type container: str
    :param assetNodeName:
    :return:
    """
    node = common.getFirstIndex(node)
    if not cmds.objExists(node):
        raise RuntimeError("Node {} does not exist. Cannot publish Node".format(node))

    if not assetNodeName: assetNodeName = 'parent'

    containerNode = getContainerFromNode(node)
    if not containerNode:
        if not container: raise Exception("{} is not a part of a container and no container specified".format(node))
        addNodes(node, container)
        containerNode = container

    cmds.container(containerNode, e=True, publishAsParent=[node, assetNodeName])


def addChildAnchor(node, container=None, assetNodeName=None):
    """
    Publish a node as the child Anchor
    :param node:
    :param container: Optional- specify a container to add nodes to if nodes are not in a container
    :param assetNodeName:
    :return:
    """
    node = common.getFirstIndex(node)
    if not cmds.objExists(node):
        raise RuntimeError("Node {} does not exist. Cannot publish Node".format(node))

    if not assetNodeName: assetNodeName = 'child'

    containerNode = getContainerFromNode(node)
    if not containerNode:
        if not container: raise Exception("{} is not a part of a container and no container specified".format(node))
        addNodes(node, container)
        containerNode = container

    cmds.container(containerNode, e=True, publishAsChild=[node, assetNodeName])


def safeDeleteContainer(container):
    nodes = listNodes(container)
    removeNodes(nodes, container, removeShapes=False)
    cmds.delete(container)


def sainityCheck():
    """Run several checks to make sure maya is setup to work with containers.
     There are a couple 'gotcha's' to look out for """

    # ensure 'use assets' is OFF in the node editor
    cmds.nodeEditor('nodeEditorPanel1NodeEditorEd', e=True, useAssets=False)
    cmds.channelBox('mainChannelBox', e=True, containerAtTop=False)
    outliners = cmds.getPanel(typ='outlinerPanel')
    for outlinerPanel in outliners:
        cmds.outlinerEditor(outlinerPanel, e=True, showContainerContents=0)
        cmds.outlinerEditor(outlinerPanel, e=True, showContainedOnly=0)


class ActiveContainer(object):
    def __init__(self, container):
        """
        Set the current container to active
        :param container:
        """
        self.container = container

    def __enter__(self):
        cmds.container(self.container, e=True, c=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        cmds.container(self.container, e=True, c=False)
