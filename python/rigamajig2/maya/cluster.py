"""
Functions for clusters
"""

import maya.cmds as cmds

import rigamajig2.shared.common as common


def isCluster(cluster):
    """
    check if the cluster is a valid cluster

    :param str cluster: name of cluster to check
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    cluster = common.getFirst(cluster)
    if not cmds.objExists(cluster) or not cmds.nodeType(cluster) == "cluster":
        return False
    return True


def create():
    """
    Create a cluster
    """
    pass


def localize(cluster, transform, modelTransform, weightedCompensation=False):
    """
    Localize a cluster deformation to another transform

    :param str cluster: name of the cluster node to localize
    :param str transform: name of the transorm to localize the cluster to
    :param modelTransform: name of the node to use as the model transform
    :param bool weightedCompensation: Turn on the weigh compensation. Default is false.
    """
    for i, geometry in enumerate(cmds.cluster(cluster, q=True, geometry=True)):
        parentTransform = common.toList(cmds.listRelatives(geometry, p=True))
        clusterGeometryMatrixAttr = "{}.{}[{}]".format(cluster, "geomMatrix", i)
        if parentTransform:
            parentWorldMatrixAttr = "{}.{}".format(parentTransform[0], "worldMatrix")
            cmds.connectAttr(parentWorldMatrixAttr, clusterGeometryMatrixAttr, f=True)
        else:
            modelWorldMatrixAttr = "{}.{}".format(modelTransform, "worldMatrix")
            cmds.connectAttr(modelWorldMatrixAttr, clusterGeometryMatrixAttr, f=True)

        transformWorldMatrixAttr = "{}.{}".format(transform, "worldInverseMatrix")
        clusterPreBindMatrixAttr = "{}.{}".format(cluster, "bindPreMatrix")
        cmds.connectAttr(transformWorldMatrixAttr, clusterPreBindMatrixAttr, f=True)
        if weightedCompensation:
            transformWorldInverseMatrixAttr = "{}.{}".format(
                transform, "worldInverseMatrix"
            )
            weightedCompensationMatrixAttr = "{}.{}".format(
                cluster, "weightedCompensationMatrix"
            )
            cmds.connectAttr(
                transformWorldInverseMatrixAttr, weightedCompensationMatrixAttr, f=True
            )
