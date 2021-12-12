"""
Functions to Navigate the Directed Acyclic Graph (hirarchy)
"""

import maya.cmds as cmds

import rigamajig2.shared.common as common
import rigamajig2.maya.naming as naming


def create(node, hierarchy=None, above=True, matchTransform=True, nodeType='transform'):
    """
    Build a hirachy of transforms around a given node
    :param node: node to build hirachy around
    :param hierarchy: list of names to add into a hirachy
    :param above: If True the hirachy will added above the node. False is below.
    :param matchTransform: match the newly created nodes to the position of the node
    :param nodeType: Type of node to create
    """

    node = common.getFirstIndex(node)

    if not cmds.objExists(node):
        cmds.error("Node '{}' does not exist. cannot create a hierarchy".format(node))
        return

    if not cmds.nodeType(node) in ['transform', 'joint']:
        cmds.error("{} must be a transform".format(node))
        return

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

    if parent and above: cmds.parent(newHierachy[0], parent)

    if above:
        cmds.parent(node, newHierachy[-1])
    else:
        cmds.parent(newHierachy[0], node)


class hierarchyFromDict(object):
    def __init__(self, hierarchy=dict(), parent=None, prefix=None, suffix=None, nodeType='transform'):
        self.hierarchy = hierarchy
        self.parent = parent
        self.prefix = prefix or ""
        self.suffix = "_hrc" if suffix is None else suffix
        self.nodeType = nodeType

        self._nodes = list()

    def create(self, hierarchy=None, parent=None):
        """
        Create a Node hiearchy from a dictionary
        :param hierarchy:
        :param parent=None
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
        return self._nodes


def getTopParent(node):
    """
    Get the top parent of a hirarchy
    :param node: input node to search
    :return: top parent of the node
    """
    return cmds.ls(node, long=True)[0].split('|')[1]


def getAllParents(node):
    """
    return a list of all a nodes parents
    :param node:
    :return:
    """
    parents = cmds.ls(node, long=True)[0].split('|')[1:-1]
    parents.reverse()
    return parents


def getParent(node):
    """
    return a the parent nodes parents
    :param node:
    :return:
    """
    return cmds.listRelatives(node, p=True)[0] if cmds.listRelatives(node, p=True) else None


def getChildren(node):
    """
    Get all children of a node
    :param node: input node to search
    :return: all children of the node
    """
    return cmds.listRelatives(node, c=True)


def getAllChildren(node):
    """
    Get all children and decendents of a node
    :param node:  input node to search
    :return: all children of the node
    """
    children = cmds.listRelatives(node, ad=True)
    children.reverse()
    return children


def getChild(node):
    """
    Get the first child of a given node
    :param node: input node to search
    :return: the
    """
    return cmds.listRelatives(node, c=True)[0] if len(cmds.listRelatives(node, c=True)) > 0 else list()
