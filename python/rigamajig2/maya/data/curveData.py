#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json module for curve data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.curve as curve
import rigamajig2.maya.data.nodeData as node_data
import rigamajig2.shared.common as common


class CurveData(node_data.NodeData):
    """This class to save and load curve data"""

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        :type node: str
        """
        if cmds.nodeType(node) == "nurbsCurve":
            node = common.getFirst(cmds.listRelatives(node, p=True))
        super(CurveData, self).gatherData(node)

        # if the node has construction history... delete it
        if cmds.listHistory(node, lv=True):
            cmds.delete(node, ch=True)

        data = OrderedDict()
        shapeList = cmds.listRelatives(
            node, c=True, shapes=True, type="nurbsCurve", pa=True
        )
        data["shapes"] = OrderedDict()
        if shapeList:
            for shape in shapeList:
                data["shapes"][shape] = OrderedDict()
                data["shapes"][shape]["points"] = list()
                for i, _ in enumerate(cmds.ls("{0}.cv[*]".format(shape), fl=True)):
                    data["shapes"][shape]["points"].append(
                        cmds.getAttr("{}.controlPoints[{}]".format(shape, i))[0]
                    )

                formNames = cmds.attributeQuery("f", node=shape, le=True)[0].split(":")
                data["shapes"][shape]["form"] = formNames[
                    cmds.getAttr("{}.form".format(shape))
                ]
                data["shapes"][shape]["degree"] = cmds.getAttr(
                    "{}.degree".format(shape)
                )
        self._data[node].update(data)

    def applyData(self, nodes, attributes=None, create=False, applyColor=True):
        """
        Applies the data for given nodes. Optional argument to create curves if no nodes are present
        :param nodes: Array of nodes to apply the data to
        :type nodes: list | tuple | str

        :param attributes: Array of attributes you want to apply the data to
        :type attributes: list | tuple

        :param create: Create curves for curves without nodes in the scene
        :type create: bool

        :param replace: Replace existing curves in the scene
        :type replace: bool

        :param applyColor: apply color to created curves
        :type applyColor: bool
        """
        nodes = common.toList(nodes)
        result = list()
        for node in nodes:
            if node not in self._data:
                continue
            if not attributes:
                attributes = list(self._data[node].keys()) + ["points"]

            for attribute in attributes:
                if attribute == "points":
                    form = "Open"
                    if "shapes" not in self._data[node]:
                        continue

                    connections = None
                    for shape in self._data[node]["shapes"].keys():
                        created = False
                        if create:
                            # if the node does not exist in the scene. Create it.
                            if not cmds.objExists(node):
                                cmds.createNode("transform", n=node)

                            # check if the shape exists but there is a mismatch in the number of cvs
                            numSourceCvs = len(
                                self._data[node]["shapes"][shape][attribute]
                            )
                            if (
                                cmds.objExists(shape)
                                and len(curve.getCvs(shape)) != numSourceCvs
                            ):
                                # get the input connections to the shape
                                shapeVisiable = "{}.v".format(shape)
                                connections = cmds.listConnections(
                                    shapeVisiable, d=False, s=True, p=True
                                )
                                cmds.delete(shape)

                            if not cmds.objExists(shape):
                                if "form" in self._data[node]["shapes"][shape]:
                                    form = self._data[node]["shapes"][shape]["form"]
                                curveTrs = curve.createCurve(
                                    points=self._data[node]["shapes"][shape][attribute],
                                    degree=self._data[node]["shapes"][shape]["degree"],
                                    name=node + "_temp",
                                    transformType="transform",
                                    form=form,
                                )
                                shapeNode = cmds.listRelatives(
                                    curveTrs, c=True, s=True, type="nurbsCurve"
                                )[0]
                                cmds.rename(shapeNode, shape)
                                cmds.parent(shape, node, r=True, s=True)
                                cmds.delete(curveTrs)

                                # rebuild the connections if the original node had any
                                if connections:
                                    for connection in connections:
                                        cmds.connectAttr(
                                            connection, "{}.v".format(shape), f=True
                                        )

                                created = True

                        if not created and cmds.objExists(shape):
                            for i, position in enumerate(
                                self._data[node]["shapes"][shape][attribute]
                            ):
                                cmds.setAttr(
                                    "{}.controlPoints[{}]".format(shape, i), *position
                                )
                result.append(node)

        if applyColor:
            super(CurveData, self).applyData(
                nodes,
                attributes=[
                    "overrideEnabled",
                    "overrideRGBColors",
                    "overrideColorRGB",
                    "overrideColor",
                ],
            )
        return result
