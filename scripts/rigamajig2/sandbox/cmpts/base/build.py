#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: base/build.py
    author: masonsmigel
    date: 07/2022

"""
import maya.cmds as cmds
from collections import OrderedDict
from rigamajig2.shared.logger import Logger

import rigamajig2.maya.meta as meta
import rigamajig2.maya.container as container
import rigamajig2.maya.transform as transform


class ComponentBuild(object):

    def __init__(self, container):
        self.container = container
        self.loadMetaData()

    def build(self):
        """build the guide"""
        with container.ActiveContainer(self.container):
            self.createBindJoints()
            self.createRigSetup()

    def createRigSetup(self):
        """ create the rig setup """
        pass

    def connect(self):
        """connect the guide to other components"""
        pass

    def loadMetaData(self):
        metaNode = meta.MetaNode(self.container)
        data = metaNode.getAllData()

        # set the key and value onto the class attribute
        for key in list(data.keys()):
            setattr(self, key, data[key])

    def getGuides(self):
        """
        Get all guides from the component.
        The function will return the guides IN THE SAME ORDER as they were created
        """
        allNodes = container.listNodes(self.container)

        guides = list()
        for node in allNodes:
            if meta.hasTag(node, "guide"):
                guides.append(node)

        return guides

    def addDefaultHeirarchy(self):
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.params_hrc = cmds.createNode('transform', n=self.name + '_params', parent=self.root_hrc)
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)



if __name__ == '__main__':
    b = Build("demoGuide_container")

    print b.getGuides()
    b.loadMetaData()
    b.build()
