"""
This is the json module for maya specific data
"""
import logging
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.data.abstractData as abstract_data

logger = logging.getLogger(__name__)


class MayaData(abstract_data.AbstractData):
    """ Class to store  maya data"""
    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param node: Node to gather data from
        :type node: str
        """
        if not cmds.objExists(node):
            logger.warning("{0} does not exist in this Maya session".format(node))

        self._data[node] = OrderedDict(dagPath=cmds.ls(node, l=True)[0])
