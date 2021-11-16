from collections import OrderedDict
import rigamajig2.maya.data.node_data as node_data
import maya.cmds as cmds


class JointData(node_data.NodeData):
    def __init__(self):
        """
        constructor for the joint data class
        """
        super(JointData, self).__init__()

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        :type node: str
        """
        super(JointData, self).gatherData(node)

        data = OrderedDict()
        data['jointOrient'] = [round(value, 4) for value in cmds.getAttr("{0}.jo".format(node))[0]]
        data['preferredAngle'] = [round(value, 4) for value in cmds.getAttr("{0}.preferredAngle".format(node))[0]]
        data['drawStyle'] = cmds.getAttr("{0}.drawStyle".format(node))

        self._data[node].update(data)
