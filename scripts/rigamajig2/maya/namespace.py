"""
Namespace functions
"""
import maya.cmds as cmds


def deleteAllNamespace():
    """
    Delete all namespaces from a scene
    """
    toExclude = ('UI', 'shared')
    ns_dict = {}
    for ns_find in (x for x in cmds.namespaceInfo(':', listOnlyNamespaces=True, recurse=True, fn=True) if
                    x not in toExclude):
        ns_dict.setdefault(len(ns_find.split(":")), []).append(ns_find)

    for i, lvl in enumerate(reversed(ns_dict.keys())):
        for namespace in ns_dict[lvl]:
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
