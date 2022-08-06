"""
Namespace functions
"""
import maya.cmds as cmds


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
    :param nodes: nodes to add to the namespace
    :param namespace: namespace to add nodes to
    """
    if not cmds.namespace(exists=namespace):
        cmds.error("namespace {} does not exist".format(namespace))
        return

    for node in nodes:
        cmds.rename(node, ":{namespace}:{node}".format(namespace=namespace, node=node))
