#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: editComponentParametersDialog.py
    author: masonsmigel
    date: 08/2022
    discription: 

"""
# PYTHON
import sys
import time
import logging
import os
from collections import OrderedDict

# MAYA
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

# RIGAMJIG
from rigamajig2.ui.widgets import mayaListWidget
from rigamajig2.ui.widgets import mayaDictWidget
from rigamajig2.ui.widgets import mayaStringWidget

from rigamajig2.maya import meta


class EditComponentDialog(QtWidgets.QDialog):
    """Edit component dialog UI"""
    WINDOW_TITLE = "Edit Component: "

    dialogInstance = None

    windowClosedSignal = QtCore.Signal(bool)

    def __init__(self):
        """ Constructor for the builder dialog"""
        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(EditComponentDialog, self).__init__(mayaMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(280, 600)

        # store a list of all component level widgets
        self.componentWidgets = list()

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets"""
        self.nameLineEdit = QtWidgets.QLineEdit()
        self.typeLineEdit = QtWidgets.QLineEdit()
        self.typeLineEdit.setReadOnly(True)
        self.inputMayaList = mayaListWidget.MayaList()
        self.inputMayaList.setHeight(120)
        self.rigParentMayaString = mayaStringWidget.MayaString()

        self.applyButton = QtWidgets.QPushButton("Apply Parameters")
        self.applyButton.setFixedHeight(35)
        self.closeButton = QtWidgets.QPushButton("Close")

    def createLayouts(self):
        """ Create Layouts"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        # stuff for the common widget
        commonLayout = QtWidgets.QVBoxLayout()
        commonLayout.setContentsMargins(0, 0, 0, 0)
        commonLayout.addSpacing(4)

        # setup the form layout
        commonFormLayout = QtWidgets.QFormLayout()
        commonFormLayout.addRow(QtWidgets.QLabel("name"), self.nameLineEdit)
        commonFormLayout.addRow(QtWidgets.QLabel("type"), self.typeLineEdit)
        commonFormLayout.addRow(QtWidgets.QLabel("inputs"), self.inputMayaList)
        commonFormLayout.addRow(QtWidgets.QLabel("rigParent"), self.rigParentMayaString)
        commonLayout.addLayout(commonFormLayout)
        # add a tiny space at the bottom
        commonLayout.addSpacing(4)

        commonGroupBox = QtWidgets.QGroupBox("common")
        commonGroupBox.setLayout(commonLayout)
        # setup a size policy. We need this to make sure the group doesnt scale vertically but does horizontally
        sizePolicy = QtWidgets.QSizePolicy()
        sizePolicy.setHorizontalPolicy(QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setVerticalPolicy(QtWidgets.QSizePolicy.Fixed)
        commonGroupBox.setSizePolicy(sizePolicy)

        # stuff for the component level parameters
        componentLayout = QtWidgets.QVBoxLayout()
        componentLayout.addSpacing(4)
        componentLayout.setContentsMargins(0, 0, 0, 0)
        # setup the form layout
        componentFormLayout = QtWidgets.QFormLayout()
        componentLayout.addLayout(componentFormLayout)
        componentLayout.addStretch()
        # add a tiny space at the bottom
        componentLayout.addSpacing(4)

        # store the form layout to use later
        self.componentFormLayout = componentFormLayout

        componentGroupBox = QtWidgets.QGroupBox("component")
        componentGroupBox.setLayout(componentLayout)

        # scrollable widget for scrollable area
        bodyWidget = QtWidgets.QWidget()
        bodyLayout = QtWidgets.QVBoxLayout(bodyWidget)
        bodyLayout.setContentsMargins(0, 0, 0, 0)
        bodyLayout.addWidget(commonGroupBox)
        bodyLayout.addWidget(componentGroupBox)

        # scrollable area
        bodyScrollArea = QtWidgets.QScrollArea()
        bodyScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        bodyScrollArea.setWidgetResizable(True)
        bodyScrollArea.setWidget(bodyWidget)

        # lower buttons
        lowButtonsLayout = QtWidgets.QVBoxLayout()
        lowButtonsLayout.setSpacing(4)
        lowButtonsLayout.addWidget(self.applyButton)
        lowButtonsLayout.addWidget(self.closeButton)

        self.mainLayout.addWidget(bodyScrollArea)
        self.mainLayout.addLayout(lowButtonsLayout)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)

    def createConnections(self):
        """ Create Connections"""
        self.closeButton.clicked.connect(self.close)

    def setComponent(self, component):
        """ Set the widget to the given component """

        # ensure all maya component level changes are loaded onto the class
        component._loadComponentParametersToClass()

        # set the title of the window to reflect the active component
        title = self.WINDOW_TITLE + " " + component.name
        self.setWindowTitle(title)

        # # set the commmon parameters
        self.nameLineEdit.setText(component.name)
        self.typeLineEdit.setText(component.componentType)
        self.inputMayaList.setItems(component.input)
        self.rigParentMayaString.setText(component.rigParent)

        # clear the old parameters
        for i in reversed(range(self.componentFormLayout.count())):
            self.componentFormLayout.itemAt(i).widget().deleteLater()

        for item in component.cmptSettings:
            if item not in ['name', 'input', 'rigParent', 'type']:
                self.addWidgetFromParameter(item, component.container, parameterType=type(component.cmptSettings[item]))

    # TODO: finish this
    def addWidgetFromParameter(self, parameter, container, parameterType):
        """
        :return:
        """

        label = QtWidgets.QLabel(parameter)
        print parameterType

        if parameterType == int:
            # add an int widget
            widget = QtWidgets.QLineEdit()
            value = cmds.getAttr("{}.{}".format(container, parameter))
            widget.setText(str(value))
        elif parameterType == float:
            # add a float widget
            widget = QtWidgets.QLineEdit()
            value = cmds.getAttr("{}.{}".format(container, parameter))
            widget.setText(str(value))
        elif parameterType == dict:
            # add a maya dict widget
            widget = mayaDictWidget.MayaDict()

            # this should be de-serialized.
            metaNode = meta.MetaNode(container)
            data = metaNode.getData(parameter)
            widget.setItems(data)

        elif parameterType == list:
            # add a maya list widget
            widget = mayaListWidget.MayaList()
        elif parameterType == bool:
            widget = QtWidgets.QCheckBox()
            value = cmds.getAttr("{}.{}".format(container, parameter))
            widget.setChecked(value)
        else:
            widget = QtWidgets.QLineEdit()
            value = cmds.getAttr("{}.{}".format(container, parameter))
            widget.setText(value)

        # add the widget to the component layout
        self.componentFormLayout.addRow(label, widget)

        self.componentWidgets.append([label, widget])

    def closeEvent(self, *args, **kwargs):
        """ Add a close event to emit the signal whenever the window is closed"""
        self.windowClosedSignal.emit(True)
