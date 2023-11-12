"""
This is the json module for maya Deformer data
"""
import logging
import sys
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.data.mayaData as maya_data
import rigamajig2.maya.data.nodeData as node_data
from rigamajig2.maya import attr
from rigamajig2.maya import deformer
from rigamajig2.shared import common

logger = logging.getLogger(__name__)

if sys.version_info.major >= 3:
    basestring = str

IGNORE_TYPES = ['blendShape', 'skinCluster']

SPECIAL_DEFORMERS = ['ffd', 'cluster']

GATHER_ATTRS = {
    "ffd": [
        "localInfluenceS",
        "localInfluenceT",
        "localInfluenceU",
        "outsideLattice",
        "outsideFalloffDist",
        "usePartialResolution",
        "partialResolution",
        "bindToOriginalGeometry",
        "freezeGeometry"],
    "cluster": [
        "relative",
        "angleInterpolation"],
    "deltaMush": [
        "smoothingIterations",
        "smoothingStep",
        "pinBorderVertices",
        "displacement",
        "scaleX",
        "scaleY",
        "scaleZ",
        "inwardConstraint",
        "outwardConstraint",
        "distanceWeight"
        ],
    'tension': [
        "smoothingIterations",
        "smoothingStep",
        "pinBorderVertices",
        "inwardConstraint",
        "outwardConstraint",
        "squashConstraint",
        "stretchConstraint",
        "relative",
        "shearStrength",
        "bendStrength"]
    }


class DeformerData(maya_data.MayaData):
    """Subclass for Node Data"""

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute

        NOTE: Deformer data will save most deformer types but does not include blendShapes or skinClusters.
        :param node: Node to gather data from
        """
        if not deformer.isDeformer(node):
            nodes = deformer.getDeformerStack(node, ignoreTypes=IGNORE_TYPES)
        else:
            nodes = common.toList(node)

        for node in nodes:
            super(DeformerData, self).gatherData(node)

            data = OrderedDict()

            data['deformerType'] = cmds.nodeType(node)
            data['envelope'] = cmds.getAttr(f"{node}.envelope")
            data['affectedGeo'] = deformer.getAffectedGeo(node)

            gatherAttrs = GATHER_ATTRS.get(data['deformerType'])
            if not gatherAttrs:
                logger.warning(f"Deformers type '{data['deformerType']}' is not currently supported")
                gatherAttrs = list()

            for deformerAttr in gatherAttrs:
                data[deformerAttr] = cmds.getAttr(f"{node}.{deformerAttr}")

            deformerWeightsDict = dict()
            for affectedGeo in data['affectedGeo']:
                deformerWeightsDict[affectedGeo] = deformer.getWeights(node, affectedGeo)

            data['deformerWeights'] = deformerWeightsDict
            # now we can do some specialty Cases:
            if data['deformerType'] == 'ffd':
                lattice = cmds.listConnections(f"{node}.deformedLattice.deformedLatticePoints", s=True)[0]

                data['sDivisions'] = cmds.getAttr(f"{lattice}.sDivisions")
                data['tDivisions'] = cmds.getAttr(f"{lattice}.tDivisions")
                data['uDivisions'] = cmds.getAttr(f"{lattice}.uDivisions")

                base = cmds.listConnections(f"{node}.baseLattice.baseLatticeMatrix", s=True)[0]

                # gather nodeData for the lattice base
                nodeData = node_data.NodeData()
                nodeData.gatherData(base)
                data["baseData"] = nodeData.getData()[base]

                # gather nodeData for the lattice Shape
                nodeData = node_data.NodeData()
                nodeData.gatherData(lattice)
                data["latticeData"] = nodeData.getData()[lattice]

            if data['deformerType'] == 'cluster':
                clusterHandle = cmds.listConnections(f"{node}.clusterXforms", s=True)[0]
                data['origin'] = list(cmds.getAttr(f"{clusterHandle}.origin")[0])

                # gather nodeData for the lattice Shape
                nodeData = node_data.NodeData()
                nodeData.gatherData(clusterHandle)
                data["clusterHandleData"] = nodeData.getData()[clusterHandle]

            # TODO: maybe handle nonlinear deformers

            if data['deformerType'] == 'nonlinear':
                pass

            # gather deformer weights for each
            self._data[node].update(data)

    def applyData(self, nodes, create=True, attributes=None):
        """
        Applies the data for given nodes.
        :param nodes: Array of nodes to apply the data to
        :type nodes: list | tuple

        :param create: create the deformer if it doesnt exisit

        :param attributes: Array of attributes you want to apply the data to

        :return:
        """
        nodes = common.toList(nodes)
        for node in nodes:
            # if the deformer doesnt exist try to create one
            created = False
            deformerType = self._data[node]['deformerType']
            if not cmds.objExists(node):
                # if we dont want to create one print out a warning and
                if not create:
                    logger.warning(f"The deformer '{node}' does not exist in the scene. Please use the 'create' flag")
                    return

                created = True
                if deformerType not in SPECIAL_DEFORMERS:
                    node = cmds.deformer(type=deformerType, name=node, ignoreSelected=True)[0]
                else:
                    if deformerType == 'ffd':
                        node, lattice, latticeBase = cmds.lattice(n=node, ignoreSelected=True)
                    if deformerType == 'cluster':
                        node, clusterHandle = cmds.cluster(name=node, ignoreSelected=True)

            # setup the handle node data
            if deformerType == 'ffd':
                # if we did not create the deformer now we need to gather some data
                if not created:
                    lattice = cmds.listConnections(f"{node}.deformedLattice.deformedLatticePoints", s=True)[0]
                    latticeBase = cmds.listConnections(f"{node}.baseLattice.baseLatticeMatrix", s=True)[0]

                newData = dict()
                newData[latticeBase] = self._data[node]["baseData"]
                newData[lattice] = self._data[node]["latticeData"]

                # setup the lattice NodeData. This includeds the lattice and base.
                nodeData = node_data.NodeData()
                nodeData.setData(newData)
                nodeData.applyAllData()

            if deformerType == 'cluster':
                # if we did not create the deformer now we need to gather some data
                if not created:
                    # setup the cluster handle
                    clusterHandle = cmds.listConnections(f"{node}.clusterXforms", s=True)[0]

                    # setup the cluster origin
                    cmds.setAttr(f"{clusterHandle}.origin", *self._data[node]['origin'])

                    newData = dict()
                    newData[clusterHandle] = self._data[node]["clusterHandleData"]

                    # setup the cluster Handle data
                    nodeData = node_data.NodeData()
                    nodeData.setData(newData)
                    nodeData.applyAllData()

            # TODO: maybe handle non-linear deformers?

            # add all the geometry to the deformer and load the weights
            for geo in list(self._data[node]['affectedGeo']):
                # add the geometry to the deformer
                deformer.addGeoToDeformer(node, geo)
                # load the deformer weights
                deformer.setWeights(node, self._data[node]['deformerWeights'][geo], geometry=geo)

            # load the additional attributes from the deformer
            if not attributes:
                attributes = GATHER_ATTRS[deformerType]

            for attribute in attributes:
                attr.setPlugValue(f"{node}.{attribute}", self._data[node][attribute])
