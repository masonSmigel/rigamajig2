"""
This module contains skin cluster data
"""
import logging

import maya.cmds as cmds
from collections import OrderedDict
import rigamajig2.shared.common as common
import rigamajig2.maya.data.maya_data as maya_data
import rigamajig2.maya.skinCluster as skinCluster
import rigamajig2.maya.deformer as deformer

logger = logging.getLogger(__name__)


class SkinData(maya_data.MayaData):
    def __init__(self):
        super(SkinData, self).__init__()

    def gatherData(self, node):

        if cmds.nodeType(node) in {'nurbsCurve', 'nurbsSurface', 'mesh'}:
            skinCls = common.getFirstIndex(cmds.listRelatives(node, p=True))
        elif cmds.nodeType(node) == 'transform':
            skinCls = skinCluster.getSkinCluster(node)
        else:
            skinCls = node

        assert skinCls, "Mesh '{}' must be connected to a skinCluster".format(node)

        super(SkinData, self).gatherData(node)
        data = OrderedDict()

        data['namespace'] = skinCls.split(":")[0] if len(skinCls.split(":")) >= 2 else ''
        data['skinClusterName'] = skinCls

        skinningMethodNames = cmds.attributeQuery("skinningMethod", node=skinCls, le=True)[0].split(":")
        data['skinningMethod'] = skinningMethodNames[cmds.getAttr("{}.skinningMethod".format(skinCls))]
        data['normalizeWeights'] = cmds.getAttr("{}.normalizeWeights".format(skinCls))
        data['dqsSupportNonRigid'] = cmds.getAttr("{}.dqsSupportNonRigid".format(skinCls))
        data['objects'] = cmds.skinCluster(skinCls, q=True, g=True)

        skinClsPreBindAttr = "{}.bindPreMatrix".format(skinCls)
        preBindInputs = common.toList(cmds.listConnections(skinClsPreBindAttr, plugs=True, s=True, d=False))
        data['preBindInputs'] = preBindInputs if preBindInputs else None

        weights, vertexCount = skinCluster.getWeights(node)
        data['vertexCount'] = vertexCount
        data['weights'] = weights

        if data['skinningMethod'] == skinningMethodNames[-1]:
            data['dqBlendWeights'] = skinCluster.getBlendWeights(node)

        self._data[node].update(data)

    def applyData(self, nodes, rebind=True):
        nodes = common.toList(nodes)

        for node in nodes:
            meshShape = deformer.getDeformShape(node)
            mesh = cmds.listRelatives(meshShape, p=True)[0]
            mesh_skin = skinCluster.getSkinCluster(mesh)

            influenceObjects = self._data[node]['weights'].keys()

            if not rebind and mesh_skin:
                assert len(skinCluster.getInfluenceJoints(mesh_skin)) == len(
                    influenceObjects), "Influence counts do not match."

            if rebind and mesh_skin:
                cmds.delete(mesh_skin)
            if not rebind and not mesh_skin:
                raise RuntimeError("No skin assosicated with the given node. Use the rebind argument to re-bind.")
            # preform the rebind
            if rebind:
                cmds.select(influenceObjects, mesh, r=True)
                mesh_skin = cmds.skinCluster(tsb=True, mi=3, dr=1.0, wd=1,  n=mesh + "_skinCluster")[0]

            # connect the prebind inputs
            for index, bind_input in zip(range(len(influenceObjects)), self._data[node]['preBindInputs']):
                if bind_input:
                    cmds.connectAttr(bind_input, "{}.bindPreMatrix[{}]".format(mesh_skin, index), f=True)

            # set the skinweights
            skinCluster.setWeights(mesh, mesh_skin, self._data[node]['weights'])

            # set other the attributes
            cmds.setAttr("{}.{}".format(mesh_skin, "normalizeWeights"), self._data[node]['normalizeWeights'])

            skinningMethodNames = cmds.attributeQuery("skinningMethod", node=mesh_skin, le=True)[0].split(":")
            skinningMethod = skinningMethodNames.index(self._data[node]['skinningMethod'])
            cmds.setAttr("{}.{}".format(mesh_skin, "skinningMethod"), skinningMethod)
            if skinningMethod > 0:
                cmds.setAttr("{}.{}".format(mesh_skin, "dqsSupportNonRigid"), self._data[node]['dqsSupportNonRigid'])

            if skinningMethod ==2:
                skinCluster.setBlendWeights(mesh, mesh_skin, self._data[node]['dqBlendWeights'])

            logger.info("Loaded skinweights for '{}'".format(mesh))
