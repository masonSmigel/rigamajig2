#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json module for skin cluster data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""

import logging
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.data.mayaData as maya_data
import rigamajig2.maya.deformer as deformer
import rigamajig2.maya.skinCluster as skinCluster
import rigamajig2.shared.common as common

logger = logging.getLogger(__name__)


class SkinData(maya_data.MayaData):
    """ This class to save and load skinCluster data"""

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

        # get the preBind joints in the order they are listed on the skinCluster node
        preBindInputs = dict()
        for influence in skinCluster.getInfluenceJoints(skinCls):
            influenceIndex = skinCluster.getInfluenceIndex(skinCls, influence)
            preBindAttr = "{}[{}]".format(skinClsPreBindAttr, influenceIndex)
            preBindJoint = cmds.listConnections(preBindAttr, plugs=True, s=True, d=False)
            preBindInputs[influence] = preBindJoint[0] if preBindJoint else None

        data['preBindInputs'] = preBindInputs
        weights, vertexCount = skinCluster.getWeights(node)
        data['vertexCount'] = vertexCount
        data['weights'] = weights

        if data['skinningMethod'] == skinningMethodNames[-1]:
            data['dqBlendWeights'] = skinCluster.getBlendWeights(node)

        self._data[node].update(data)

    def getInfluences(self, nodes):
        """ get all the influence joints"""
        nodes = common.toList(nodes)
        for node in nodes:
            weights = self._data[node]['weights']

            influences = list(weights.keys())

        return influences

    def applyData(self, nodes, rebind=True):
        nodes = common.toList(nodes)

        for node in nodes:
            if not cmds.objExists(node):
                logger.error(f"'{node}' does not exist in scene. Cannot load skinweights")
                continue

            meshShape = deformer.getDeformShape(node)
            if not meshShape:
                logger.error(f"'{node}' has no deformable shape")
                continue

            mesh = cmds.listRelatives(meshShape, p=True)[0]
            meshSkin = skinCluster.getSkinCluster(mesh)

            influenceObjects = list(self._data[node]['weights'].keys())

            if not rebind and meshSkin:
                assert len(skinCluster.getInfluenceJoints(meshSkin)) == len(
                    influenceObjects), "Influence counts do not match."

            if rebind and meshSkin:
                cmds.delete(meshSkin)
            if not rebind and not meshSkin:
                raise RuntimeError("No skin assosicated with the given node. Use the rebind argument to re-bind.")
            # preform the rebind
            # check for missing influences
            realInfluences = [inf for inf in influenceObjects if cmds.objExists(inf)]

            if len(realInfluences) != len(influenceObjects):
                influenceDifferenge = set(influenceObjects) - set(realInfluences)
                missingInfluences = list(influenceDifferenge)
                logger.warning(f"Skin cluster {meshSkin} is missing {missingInfluences} influences.")

            if rebind:
                cmds.select(realInfluences, mesh, r=True)
                meshSkin = cmds.skinCluster(tsb=True, mi=3, dr=1.0, wd=1, n=mesh + "_skinCluster")[0]

            # set the skinweights
            skinCluster.setWeights(mesh, meshSkin, self._data[node]['weights'])

            # connect the prebind inputs
            # Here I have a check because in the inital implementation the preBindInputs were stored in a list.
            # however maya doesnt do a good job re-creating the skin cluster in a predicable order so I switched to a
            # dictionary where the index is re-found every time weights are loaded.
            if isinstance(self._data[node]['preBindInputs'], OrderedDict):
                for influence, bindInput in self._data[node]['preBindInputs'].items():
                    if bindInput:
                        influenceIndex = skinCluster.getInfluenceIndex(skinCluster=meshSkin, influence=influence)
                        cmds.connectAttr(bindInput, "{}.bindPreMatrix[{}]".format(meshSkin, influenceIndex), f=True)

            elif isinstance(self._data[node]['preBindInputs'], list):
                # # for complete ness this includes a depreciated workflow for a preBind inputs stored as a list.
                # TODO: this should be depreiciated.
                logger.warning(f"{node} is using a depreciated workflow. Please save the skin file to update!")
                for index, bindInput in zip(range(len(influenceObjects)), self._data[node]['preBindInputs']):
                    if bindInput:
                        cmds.connectAttr(bindInput, "{}.bindPreMatrix[{}]".format(meshSkin, index), f=True)

            # set other the attributes
            cmds.setAttr("{}.{}".format(meshSkin, "normalizeWeights"), self._data[node]['normalizeWeights'])
            # cmds.skinCluster(meshSkin, edit=True, recacheBindMatrices=True)

            skinningMethodNames = cmds.attributeQuery("skinningMethod", node=meshSkin, le=True)[0].split(":")
            skinningMethod = skinningMethodNames.index(self._data[node]['skinningMethod'])
            cmds.setAttr("{}.{}".format(meshSkin, "skinningMethod"), skinningMethod)
            if skinningMethod > 0:
                cmds.setAttr("{}.{}".format(meshSkin, "dqsSupportNonRigid"), self._data[node]['dqsSupportNonRigid'])

            if skinningMethod == 2:
                skinCluster.setBlendWeights(mesh, meshSkin, self._data[node]['dqBlendWeights'])
            logger.info(f"Loaded Skin Weights for: {node}")
