#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: guide.py
    author: masonsmigel
    date: 07/2022

"""
import maya.cmds as cmds
from collections import OrderedDict
from rigamajig2.shared.logger import Logger

import rigamajig2.maya.container as container
import rigamajig2.maya.meta as meta
import rigamajig2.maya.rig.control as control


class ComponentGuide(object):
    """"""

    def __init__(self, name, side=None, jointNames=[], size=1, rigParent=None):
        """
        constructor for the class.
        :param name:
        :param side: 
        :param size:
        :param rigParent:
        """
        self._data = OrderedDict()

        self.addParameter("name", value=name, type="string")
        self.addParameter("side", value=side, type="string")

        cmpt_type = ".".join([self.__module__.split('cmpts.')[-1], self.__class__.__name__])
        self.addParameter("cmpt_type", value=cmpt_type, type="string")

        self.addParameter("jointNames", value=jointNames, type="list")
        self.addParameter("size", value=size, type="float")
        self.addParameter("rigParent", value=rigParent, type="string")

        self.container = name + "_container"

    def initalize(self):
        """
        initalize the guide.
        This includes building the guides and storing metadata onto the container
        """
        self.createContainer()
        with container.ActiveContainer(self.container):
            self.createGuides()
        self.createMetaData()

    def createContainer(self):
        """Create a Container for the component"""
        if not cmds.objExists(self.container):
            containerNode = container.create(self.container)
            meta.tag(containerNode, 'component')
            Logger.debug("Created Container: {}".format(containerNode))

    def createGuides(self):
        """
        create the build guides
        """
        pass

    def createMetaData(self):

        metaNode = meta.MetaNode(self.container)

        for key in list(self._data.keys()):
            metaNode.setData(key, self._data[key]["value"])
            # TODO: store the metadata onto the container

    def addParameter(self, label, value, type="string"):
        """
        Add data to this class.

        Values added here are added to the class.
        They can be accesed by self.label to return the value

        :param label: label of the data. This is the key to retreive it and will appear in the ui
        :param value: the value of the data
        :param type: type of parameter to store the data.
                     valid types are "string", "float" , "int, "list"
        :return:
        """
        dataDict = OrderedDict()

        dataDict["value"]  = value
        dataDict["dataType"]  = type

        setattr(self, label, value)
        self._data[label] = dataDict



if __name__ == '__main__':
    g = ComponentGuide("demoGuide", size=1, rigParent="yourMom")
    g.initalize()