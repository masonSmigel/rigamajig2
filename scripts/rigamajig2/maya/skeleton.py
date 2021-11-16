"""
Skeleton utilities
"""
import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.attr as attr


def connectChains(source, destination):
    """
    Connect two skeletons
    """

    source = common.toList(source)
    destination = common.toList(destination)
    if not len(source) == len(destination):
        raise RuntimeError('List mismatch. Source and destination must have equal lengths')

    for source_jnt, dest_jnt in zip(source, destination):
        cmds.parentConstraint(source_jnt, dest_jnt, mo=True)
        cmds.connectAttr("{}.s".format(source_jnt), "{}.s".format(dest_jnt))
        attr.lock(dest_jnt, attr.TRANSFORMS + ['v'])
