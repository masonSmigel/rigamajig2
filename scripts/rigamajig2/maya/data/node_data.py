"""
This is the json module for maya transform data
"""
from collections import OrderedDict
import rigamajig2.maya.data.maya_data as maya_data
import maya.cmds as cmds


class NodeData(maya_data.MayaData):
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
        :type node: str
        """
        super(NodeData, self).gatherData(node)

        data = OrderedDict()
        for attr in ['translate', 'rotate', 'scale']:
            data[attr] = [round(value, 4) for value in cmds.getAttr("{0}.{1}".format(node, attr))[0]]

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

    def applyData(self, nodes, attributes=None, worldSpace=False):
        """
        Applies the data for given nodes.
        :param nodes: Array of nodes to apply the data to
        :type nodes: list | tuple

        :param attributes: Array of attributes you want to apply the data to
        :type attributes: list | tuple

        :param worldSpace: If True apply translate and rotate in world space.
        :return:
        """
        gather_attrs_from_file = False
        for node in nodes:
            if not self._data.has_key(node):
                continue
            if not attributes:
                gather_attrs_from_file = True
                attributes = self._data[node].keys()

            if worldSpace:
                if not (not ('translate' in attributes) or not self._data[node].has_key('world_translate')):
                    cmds.xform(node, ws=True, t=self._data[node]['world_translate'])
                    attributes.pop(attributes.index('translate'))
                if 'rotate' in attributes and self._data[node].has_key('world_rotate'):
                    cmds.xform(node, ws=True, ro=self._data[node]['world_rotate'])
                    attributes.pop(attributes.index('rotate'))

            for attribute in attributes:
                if self._data[node].has_key(attribute) and attribute in cmds.listAttr(node):
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
        if gather_attrs_from_file:
            attributes = None
