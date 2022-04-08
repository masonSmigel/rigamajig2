"""
This module contains curve data
"""

from collections import OrderedDict
import rigamajig2.maya.data.node_data as node_data
import rigamajig2.shared.common as common
import rigamajig2.maya.curve as curve
import maya.cmds as cmds


class CurveData(node_data.NodeData):
    def __init__(self):
        """
        constructor for the curve data class
        """
        super(CurveData, self).__init__()

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        :type node: str
        """
        if cmds.nodeType(node) == 'nurbsCurve':
            node = common.getFirstIndex(cmds.listRelatives(node, p=True))
        super(CurveData, self).gatherData(node)

        # if the node has construction history... delete it
        if cmds.listHistory(node, lv=True):
            cmds.delete(node, ch=True)

        data = OrderedDict()
        shape_list = cmds.listRelatives(node, c=True, shapes=True, type="nurbsCurve", pa=True)
        data['shapes'] = OrderedDict()
        if shape_list:
            for shape in shape_list:
                data['shapes'][shape] = OrderedDict()
                data['shapes'][shape]['points'] = list()
                for i, cv in enumerate(cmds.ls("{0}.cv[*]".format(shape), fl=True)):
                    data['shapes'][shape]['points'].append(cmds.getAttr("{}.controlPoints[{}]".format(shape, i))[0])

                formNames = cmds.attributeQuery("f", node=shape, le=True)[0].split(":")
                data['shapes'][shape]['form'] = formNames[cmds.getAttr("{}.form".format(shape))]
                data['shapes'][shape]['degree'] = cmds.getAttr("{}.degree".format(shape))
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
                if attribute == 'points':
                    form = 'Open'
                    if 'shapes' not in self._data[node]:
                        continue
                    for shape in self._data[node]['shapes'].keys():
                        created = False
                        if create:
                            # if the node does not exist in the scene. Create it.
                            if not cmds.objExists(node):
                                cmds.createNode('transform', n=node)

                            if not cmds.objExists(shape):
                                if 'form' in self._data[node]['shapes'][shape]:
                                    form = self._data[node]['shapes'][shape]['form']
                                curveTrs = curve.createCurve(points=self._data[node]['shapes'][shape][attribute],
                                                             degree=self._data[node]['shapes'][shape]['degree'],
                                                             name=node + '_temp',
                                                             transformType='transform',
                                                             form=form)
                                shapeNode = cmds.listRelatives(curveTrs, c=True, s=True, type='nurbsCurve')[0]
                                cmds.rename(shapeNode, shape)
                                cmds.parent(shape, node, r=True, s=True)
                                cmds.delete(curveTrs)
                                created = True

                        if not created and cmds.objExists(shape):
                            for i, position in enumerate(self._data[node]['shapes'][shape][attribute]):
                                cmds.setAttr('{}.controlPoints[{}]'.format(shape, i), *position)
                result.append(node)

        if applyColor:
            super(CurveData, self).applyData(nodes, attributes=["overrideEnabled", "overrideRGBColors",
                                                                "overrideColorRGB", "overrideColor"])
        return result


if __name__ == '__main__':
    # d = CurveData()
    # for obj in cmds.ls(sl=True):
    #     print obj
    #     d.gatherData(obj)
    # d.write('/Users/masonsmigel/Documents/projects/2021/neko/libby_rig/Rig/ctls/libby_ctls.json')

    d = CurveData()
    d.read('/Users/masonsmigel/Documents/projects/2021/neko/libby_rig/Rig/ctls/libby_ctls.json')
    d.applyData(cmds.ls(sl=True), create=True)
