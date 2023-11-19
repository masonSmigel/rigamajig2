#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: component_data.py
    author: masonsmigel
    date: 09/2023
    description: 

"""
import rigamajig2.maya.data.abstractData as abstract_data
from rigamajig2.maya import container
from rigamajig2.maya.builder import componentManager
from rigamajig2.maya.components import base
from rigamajig2.shared import common


class ComponentData(abstract_data.AbstractData):
    """ Class to gather and store component data """

    def __init__(self):
        """
        constructor for the curve data class
        """
        super(ComponentData, self).__init__()

    def gatherData(self, node):
        """
        Gather component data from the class
        :param node:
        """
        if not issubclass(type(node), base.BaseComponent):
            if container.isContainer(name=node):
                raise NotImplementedError
            else:
                raise TypeError(
                    f"{node} Failed: Component Data can only be gathered from a component class or a container")
        data = node.getComponentData()
        componentName = data["name"]
        # add the component data to the main dictionary
        self._data[componentName] = data

    def applyData(self, nodes):
        """
        Create class instances for the components
        :param nodes:
        :return:
        """
        nodes = common.toList(nodes)

        createdInstances = []
        for node in nodes:
            moduleType = self._data[node]['type']

            componentClass = componentManager.createComponentClassInstance(moduleType)
            componentInstance = componentClass.fromData(self._data[node])

            createdInstances.append(componentInstance)

        return createdInstances
