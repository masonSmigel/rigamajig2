"""
Functions to Navigate the Directed Acyclic Graph (DAG)
"""
import logging
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.naming as naming
import rigamajig2.shared.common as common

logger = logging.getLogger(__name__)


def create(node, hierarchy=None, above=True, matchTransform=True, nodeType="transform"):
    """
    Build a hirachy of transforms around a given node

    :param str node: node to build hirachy around
    :param list hierarchy: list of names to add into a hirachy
    :param bool above: If True the hirachy will added above the node. False is below.
    :param bool matchTransform: match the newly created nodes to the position of the node
    :param str nodeType: Type of node to create
    """

    node = common.getFirst(node)

    if not cmds.objExists(node):
        logger.error("Node '{}' does not exist. cannot create a hierarchy".format(node))
        return None

    if not cmds.nodeType(node) in ["transform", "joint"]:
        logger.error("{} must be a transform".format(node))
        return None

    parent = getParent(node)

    newHierachy = list()
    for i, name in enumerate(hierarchy):
        if cmds.objExists(name):
            name = naming.getUniqueName(name)
        new = cmds.createNode(nodeType, n=name)
        newHierachy.append(new)
        # Optionally match the transformation of the node in the hirachy
        if matchTransform:
            cmds.delete(cmds.parentConstraint(node, new, mo=False))
        # if were past the first node in the hirachy, create a new one
        if i > 0:
            cmds.parent(new, newHierachy[i - 1])

    if parent and above:
        cmds.parent(newHierachy[0], parent)

    if above:
        cmds.parent(node, newHierachy[-1])
    else:
        cmds.parent(newHierachy[0], node)

    return newHierachy


class DictHierarchy(object):
    """
    Hierarchy Dictionary class.
    """

    def __init__(
        self,
        hierarchy=None,
        parent=None,
        prefix=None,
        suffix=None,
        nodeType="transform",
    ):
        """
        Constructor for the DictHierarchy class

        :param list hierarchy: Existing hierarchy dictionary
        :param str parent: parent of the hierarchy
        :param str prefix: prefix to add to all items of the hierarchy
        :param str suffix: suffix to add to all items of the hierarchy
        :param str nodeType: type of node to create the hierarchy with.
        """
        hierarchy = hierarchy or dict()
        self.hierarchy = hierarchy
        self.parent = parent
        self.prefix = prefix or ""
        self.suffix = "" if suffix is None else suffix
        self.nodeType = nodeType

        self._nodes = list()

    def create(self, hierarchy=None, parent=None):
        """
        Create a Node hiearchy from a dictionary

        :param dict hierarchy: dictonary to create the hierachy from
        :param str parent: parent the newly created hierarchy
        """
        if not hierarchy:
            hierarchy = self.hierarchy
        if not parent:
            parent = self.parent

        for name, children in hierarchy.items():
            node = "{}{}{}".format(self.prefix, name, self.suffix)
            self._nodes.append(node)
            if not cmds.objExists(node):
                node = cmds.createNode(self.nodeType, name=node)
            if parent:
                currentParent = cmds.listRelatives(node, parent=True, path=True)
                if currentParent:
                    currentParent = currentParent[0]
                if currentParent != parent:
                    cmds.parent(node, parent)

            if children:
                self.create(children, node)

    def getNodes(self):
        """return the nodes in the heirarchy"""
        return self._nodes

    @staticmethod
    def getHirarchy(node):
        """
        save a heirarchy of nodes into a dictionary

        :param node: get the hierarchy below a node
        :return: hierarchy dictionary:
        :rtype: dict
        """
        node = common.getFirst(node)
        hierarchyDict = OrderedDict()

        def getChildren(node, hierarchyDict):
            """
            get children of a hierachy
            :param node: node
            :param hierarchyDict: hierarchy dict
            :return: dict
            """
            children = cmds.listRelatives(node, c=True, pa=True, type="transform")
            if children:
                hierarchyDict[node] = OrderedDict()
                for child in children:
                    hierarchyDict[node][child] = OrderedDict()
                    getChildren(child, hierarchyDict[node])
            else:
                hierarchyDict[node] = None

        getChildren(node, hierarchyDict)

        return hierarchyDict


def getTopParent(node):
    """
    Get the top parent of a hirarchy

    :param str node: input node to search
    :return: top parent of the node
    :rtype: str
    """
    return cmds.ls(node, long=True)[0].split("|")[1]


def getAllParents(node):
    """
    return a list of all a nodes parents

    :param str node: name of the input node to get all parents for
    :return: list of all parents above a node
    :rtype: List
    """
    parents = cmds.ls(node, long=True)[0].split("|")[1:-1]
    parents.reverse()
    return parents


def getParent(node):
    """
    return a the nodes parent

    :param str node: name of the node to get the parent of
    :return: name of parent of the given node
    :rtype: str None
    """
    return (
        cmds.listRelatives(node, p=True)[0]
        if cmds.listRelatives(node, p=True)
        else None
    )


def getChildren(node):
    """
    Get all children of a node

    :param str node: input node to search
    :return: all children of the node
    :rtype: list
    """
    return cmds.listRelatives(node, c=True)


def getAllChildren(node):
    """
    Get all children and decendents of a node

    :param str node:  input node to search
    :return: all children of the node
    :rtype: list
    """
    children = cmds.listRelatives(node, ad=True)
    children.reverse()
    return children


def getChild(node):
    """
    Get the first child of a given node

    :param str node: input node to search
    :return: the first child of a given node
    """
    children = cmds.listRelatives(node, children=True)
    return common.getFirst(children) if children else None
