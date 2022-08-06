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
    """
    Create a cluster
    :return:
    """
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
        
        clusterGeometryMatrixAttr = "{}.{}[{}]".format(cluster, 'geomMatrix', i)
        if parentTransform:
            parentWorldMatrixAttr = "{}.{}".format(parentTransform[0], 'worldMatrix')
            cmds.connectAttr(parentWorldMatrixAttr, clusterGeometryMatrixAttr, f=True)
        else:
            modelWorldMatrixAttr = "{}.{}".format(modelTransform, 'worldMatrix')
            cmds.connectAttr(modelWorldMatrixAttr, clusterGeometryMatrixAttr, f=True)
        
        transformWorldMatrixAttr = "{}.{}".format(transform, 'worldInverseMatrix')
        clusterPreBindMatrixAttr = "{}.{}".format(cluster, 'bindPreMatrix')
        cmds.connectAttr(transformWorldMatrixAttr, clusterPreBindMatrixAttr, f=True)
        if weightedCompensation:
            transformWorldInverseMatrixAttr = "{}.{}".format(transform, 'worldInverseMatrix')
            weightedCompensationMatrixAttr = "{}.{}".format(cluster, 'weightedCompensationMatrix')
            cmds.connectAttr(transformWorldInverseMatrixAttr, weightedCompensationMatrixAttr, f=True)
