#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: componentItem.py
    author: masonsmigel
    date: 01/2024
    description: 

"""
import typing

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from rigamajig2.maya.builder import componentManager
from rigamajig2.ui.resources import Resources

COMPONENT_ROW_HEIGHT = 20


class ComponentTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """Tree Widget Item for components"""

    def __init__(self, name, componentType, buildStep="unbuilt", container=None):
        super().__init__()

        self.setSizeHint(0, QtCore.QSize(0, COMPONENT_ROW_HEIGHT))  # set height

        uiColor = _getComponentColor(componentType)

        self.setText(0, name)
        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(0, font)
        self.setTextColor(0, QtGui.QColor(*uiColor))

        self.setText(1, componentType)
        self.setText(2, buildStep)

        if container:
            self.setData(0, QtCore.Qt.UserRole, container)

        # set the desaturated color
        desaturatedColor = [v * 0.78 for v in uiColor]
        self.setTextColor(1, QtGui.QColor(*desaturatedColor))
        self.setTextColor(2, QtGui.QColor(156, 156, 156))

        # set the icon
        icon = _getComponentIcon(componentType)
        self.setIcon(0, icon)

    def getData(self) -> typing.Dict[str, typing.Any]:
        """
        return a dictionary of data for the selected item.
        :return: a dictionary of component data
        """
        itemData = dict()
        itemData["name"] = self.text(0)
        itemData["type"] = self.text(1)
        itemData["step"] = self.text(2)
        itemData["container"] = self.data(QtCore.Qt.UserRole, 0)

        return itemData


def _getComponentIcon(componentType):
    """get the component icon from the module.Class of the component"""
    return Resources.getIcon(":icons/components/{}".format(componentType.split(".")[0]))


def _getComponentColor(cmpt):
    """get the ui color for the component"""
    tmpComponentObj = componentManager.createComponentClassInstance(cmpt)
    uiColor = tmpComponentObj.UI_COLOR
    # after we get the UI color we can delete the tmp component instance
    del tmpComponentObj
    return uiColor
