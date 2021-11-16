import rigamajig2.shared.common as common
import maya.cmds as cmds


def showLocalRotationAxis(nodes):
    """
    Show the local rotation axis for the given nodes
    :param nodes: list of nodes to display local rotation axis
    :return: None
    """
    if not common.DEBUG:
        return

    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.objExists(node):
            cmds.setAttr("{}.displayLocalAxis".format(node), 1)


def hide(nodes):
    """
    Hide nodes if we are not in debug mode
    :param nodes: nodes to hide
    :return:
    """
    if not common.DEBUG:
        cmds.hide(nodes)
