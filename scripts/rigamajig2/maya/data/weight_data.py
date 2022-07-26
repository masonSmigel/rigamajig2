#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json module for anything that has weight data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""
import rigamajig2.maya.data.abstract_data as abstract_data


class WeightData(abstract_data.AbstractData):
    """ This class saves and loads weight data."""

    def __init__(self):
        super(WeightData, self).__init__()

    def gatherData(self, item):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute
        :param item: Node to gather weight data from.
        :return:
        """
        pass

    def applyData(self, nodes, attributes=None):
        """
        Applies the data for given nodes. Optional argument to create curves if no nodes are present
        :param nodes: Array of nodes to apply the data to
        :type nodes: list | tuple

        :param attributes: Array of attributes you want to apply the data to
        :type attributes: list | tuple
        """
        pass
