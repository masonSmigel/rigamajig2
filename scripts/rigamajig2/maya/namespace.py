"""
Namespace functions
"""
import logging

import maya.cmds as cmds

logger = logging.getLogger(__name__)

def deleteAllNamespace():
    """
    Delete all namespaces from a scene
    """
    toExclude = ('UI', 'shared')
    namespaceDict = {}

    namespacesFound = cmds.namespaceInfo(':', listOnlyNamespaces=True, recurse=True, fn=True)
    for namespace in namespacesFound:
        if namespace in toExclude:
            continue
        namespaceDict.setdefault(len(namespace.split(":")), []).append(namespace)

    for i, lvl in enumerate(reversed(namespaceDict.keys())):
        for namespace in namespaceDict[lvl]:
            cmds.namespace(removeNamespace=namespace, mergeNamespaceWithParent=True)


def addToNamespace(nodes, namespace):
    """
    Add nodes to a namespace

    :param list nodes: nodes to add to the namespace
    :param namespace: namespace to add nodes to
    """
    if not isinstance(nodes, (tuple, list)):
        nodes = [nodes]

    if not cmds.namespace(exists=namespace):
        logger.error("namespace {} does not exist".format(namespace))
        return

    for node in nodes:
        cmds.rename(node, ":{namespace}:{node}".format(namespace=namespace, node=node))


def removeNamespace(nodes, namespace):
    """
    Remove the given namespace from nodes

    :param nodes: nodes to add to the namespace
    :param namespace: namespace to remove from nodes
    """
    if not isinstance(nodes, (tuple, list)):
        nodes = [nodes]
    for node in nodes:
        if namespace in node.split(":"):
            namespaceList = node.split(":")
            namespaceList.remove(namespace)
            newName = ":".join(namespaceList)
            cmds.rename(node, newName)


def getNamespace(node):
    """
    Get the namespace of the node

    :param node: node to get the namespace from
    :return: namespace of the current node
    :rtype: str
    """
    namespaces = node.split(":")[:-1]

    if len(namespaces) > 0:
        return namespaces[0]
    return None
