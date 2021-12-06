"""
Functions for clusters
"""

import maya.cmds as cmds
import rigamajig2.shared.common as common


def isCluster(cluster):
    """
    check if the cluster is a valid cluster
    :param cluster: name of cluster to check
    :return: True if Valid. False is invalid.
    """
    cluster = common.getFirstIndex(cluster)
    if not cmds.objExists(cluster) or not cmds.nodeType(cluster) == 'cluster': return False
    return True


def create():
    pass


def localize(cluster, transform, modelTransform, weightedCompensation=False):
    """
    :param cluster:
    :param transform:
    :param modelTransform:
    :param weightedCompensation:
    :return:
    """
    for i, geometry in enumerate(cmds.cluster(cluster, q=True, geometry=True)):
        parentTransform = cmds.listRelatives(geometry, p=True) or list()
        if parentTransform:
            cmds.connectAttr("{}.{}".format(parentTransform[0], 'worldMatrix'), "{}.{}[{}]".format(cluster, 'geomMatrix', i), f=True)
        else:
            cmds.connectAttr("{}.{}".format(modelTransform, 'worldMatrix'), "{}.{}[{}]".format(cluster, 'geomMatrix', i), f=True)
        cmds.connectAttr("{}.{}".format(transform, 'worldInverseMatrix'),"{}.{}".format(cluster, 'bindPreMatrix'), f=True)
        if weightedCompensation:
            cmds.connectAttr("{}.{}".format(transform, 'worldInverseMatrix'), "{}.{}".format(cluster, 'weightedCompensationMatrix'), f=True)
