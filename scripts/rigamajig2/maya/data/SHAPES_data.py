#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: SHAPES_data.py
    author: masonsmigel
    date: 03/2023
    discription: 

"""
from collections import OrderedDict
import maya.cmds as cmds
import maya.mel as mel

import rigamajig2.maya.data.maya_data as maya_data
from rigamajig2.maya import blendshape
from rigamajig2.maya import mesh


class SHAPESData(maya_data.MayaData):
    """ Class to store maya data"""

    def __init__(self):
        super(SHAPESData, self).__init__()

        # if we could loaded SHAPES then source the required mel scripts.
        # SHAPES has a built in proc to do this so we can just source the main file and call those procs.
        if self.__validateSHAPES():
            mel.eval("source SHAPES;"
                     "shapesSourceScripts;"
                     "shapesLoadScripts;")

    def __validateSHAPES(self):
        """validate that the SHAPES plugin is available and loaded"""
        SHAPESLoaded = False
        try:
            loadedPlugins = cmds.pluginInfo(query=True, listPlugins=True)
            if "SHAPESTools" not in loadedPlugins:
                cmds.loadPlugin("SHAPESTools")
            if cmds.pluginInfo("SHAPESTools", q=True, r=True):
                SHAPESLoaded = True
        except:
            pass

        return SHAPESLoaded

    def gatherData(self, node):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute

        :param node: blendshape node to gather data from
        :type node: str
        """

        if not self.__validateSHAPES():
            cmds.warning(
                "SHAPES plugin is not available. SHAPES data can still be loaded, but you cannot save new data")
            return

        if cmds.nodeType(node) == 'transform':
            blendshapeNodes = blendshape.getBlendshapeNodes(node)
        else:
            blendshapeNodes = [node]

        for blendshapeNode in blendshapeNodes:
            super(SHAPESData, self).gatherData(blendshapeNode)

            # now we need to save the data we need.
            self._data[blendshapeNode]['setupFile'] = None
            self._data[blendshapeNode]['deltasFile'] = None

    def applyData(self, nodes, attributes=None, loadDeltas=True):
        """
        Rebuild the SHAPES data from the given nodes.

        :param nodes: Array of nodes to apply the data to
        :param attributes: Array of attributes you want to apply the data to
        :param loadDeltas: If True then load the deltas back. Otherwise exact shapes will be used as blendshape targets.
        :return:
        """
        super(SHAPESData, self).applyData()

    def write(self, filepath, createDirectory=True):

        for blendshapeNode in self.getKeys():
            # for each blendshape export its setup and a optionally a delta's file
            # do the setup export

            # set the setup file data to be the path to the mel file for the blendshape!
            self._data[blendshapeNode]['setupFile'] = None

            # export the deltas too

            # set the file path in the json file
            self._data[blendshapeNode]['deltasFile'] = "newPath"

            # TODO: come back to this to update it!

        super(SHAPESData, self).write(filepath=filepath)


if __name__ == '__main__':
    d = SHAPESData()

    d.gatherData('body_hi')

    print d.getData()
    print d.write("/Users/masonsmigel/Desktop/SHAPES_WRITE_TEST/test.json")
