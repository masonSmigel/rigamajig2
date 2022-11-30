"""
This is the json module for maya transform data
"""
from collections import OrderedDict
import rigamajig2.maya.data.maya_data as maya_data
import maya.cmds as cmds
import sys

if sys.version_info.major >= 3:
    basestring = str


class NodeData(maya_data.MayaData):
    """Subclass for Node Data"""

    def __init__(self):
        """
        constructor for the node data class
        """
        super(NodeData, self).__init__()

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        """
        super(NodeData, self).gatherData(node)

        data = OrderedDict()
        for attr in ['translate', 'rotate', 'scale']:
            data[attr] = [round(value, 4) for value in cmds.getAttr("{0}.{1}".format(node, attr))[0]]

        if cmds.about(api=True) > 20200000:
            data['offsetParentMatrix'] = cmds.getAttr("{0}.offsetParentMatrix".format(node))
        data['world_translate'] = cmds.xform(node, q=True, ws=True, t=True)
        data['world_rotate'] = cmds.xform(node, q=True, ws=True, ro=True)
        data['rotateOrder'] = cmds.getAttr("{0}.rotateOrder".format(node))
        data['overrideEnabled'] = cmds.getAttr("{}.overrideEnabled".format(node))
        if cmds.getAttr("{}.overrideEnabled".format(node)):
            data['overrideRGBColors'] = cmds.getAttr("{}.overrideRGBColors".format(node))
            if data['overrideRGBColors']:
                data['overrideColorRGB'] = cmds.getAttr("{}.overrideColorRGB".format(node))[0]
            else:
                data['overrideColor'] = cmds.getAttr("{}.overrideColor".format(node))

        self._data[node].update(data)

    def gatherDataIterate(self, items):
        """
        This method will iterate through the list of items and use the gatherData method to store the
        data on the self._data attribute
        """
        for item in items:
            self.gatherData(item)

    def applyData(self, nodes, attributes=None, worldSpace=False, applyColorOverrides=True):
        """
        Applies the data for given nodes.
        :param nodes: Array of nodes to apply the data to
        :type nodes: list | tuple

        :param attributes: Array of attributes you want to apply the data to
        :type attributes: list | tuple

        :param worldSpace: If True apply translate and rotate in world space.

        :param applyColorOverrides: If True color overrides will be applied. otherwise this is false.

        :return:
        """
        gatherAttrsFromFile = False
        for node in nodes:
            if node not in self._data:
                continue
            if not cmds.objExists(node):
                continue
            if not attributes:
                gatherAttrsFromFile = True
                attributes = list(self._data[node].keys())

            if worldSpace:
                if 'translate' not in attributes or 'world_translate' not in self._data[node]:
                    cmds.xform(node, ws=True, t=self._data[node]['world_translate'])
                    attributes.remove('translate')
                if 'rotate' in attributes and 'world_rotate' in self._data[node]:
                    cmds.xform(node, ws=True, ro=self._data[node]['world_rotate'])
                    attributes.remove('rotate')

            # get set the offset parent matrix
            if cmds.about(api=True) > 20200000:
                if 'offsetParentMatrix' in attributes:
                    offsetParentMatrix = self._data[node]['offsetParentMatrix']
                    cmds.setAttr("{}.offsetParentMatrix".format(node), offsetParentMatrix, type='matrix')
                    attributes.remove('offsetParentMatrix')

            for attribute in attributes:
                if not applyColorOverrides:
                    if attribute in ['overrideEnabled', 'overrideRGBColors', 'overrideColorRGB','overrideColor']:
                        continue

                if attribute in self._data[node] and attribute in cmds.listAttr(node):
                    setAttr = True
                    for attr in cmds.listAttr("{0}.{1}".format(node, attribute)):
                        if cmds.listConnections("{0}.{1}".format(node, attr), d=False, s=True) or \
                                cmds.getAttr("{0}.{1}".format(node, attr), l=True):
                            setAttr = False
                            break
                    if not setAttr:
                        continue

                    value = self._data[node][attribute]
                    if isinstance(value, (list, tuple)):
                        cmds.setAttr("{0}.{1}".format(node, attribute), *value)
                    elif isinstance(value, basestring):
                        cmds.setAttr("{0}.{1}".format(node, attribute), value, type="string")
                    else:
                        cmds.setAttr("{0}.{1}".format(node, attribute), value)

            # clear out attributes if getting from file
            if gatherAttrsFromFile:
                attributes = None
