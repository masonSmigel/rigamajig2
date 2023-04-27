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
import maya.api.OpenMaya as om2
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

        # store a list of all component level widgets.
        # The list stores items in a tuple of (parameter name, QWidget)
        # This allows us to keep track of what widget goes to which parameter so they can be re-applied.
        self.componentWidgets = list()

        # store the current component python instance
        self.currentComponent = None

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
        self.tagLineEdit = QtWidgets.QLineEdit()
        self.enabledCheckbox = QtWidgets.QCheckBox()

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
        commonFormLayout.addRow(QtWidgets.QLabel("name:"), self.nameLineEdit)
        commonFormLayout.addRow(QtWidgets.QLabel("type:"), self.typeLineEdit)
        commonFormLayout.addRow(QtWidgets.QLabel("inputs:"), self.inputMayaList)
        commonFormLayout.addRow(QtWidgets.QLabel("rigParent:"), self.rigParentMayaString)
        commonFormLayout.addRow(QtWidgets.QLabel("component Tag:"), self.tagLineEdit)
        commonFormLayout.addRow(QtWidgets.QLabel("enabled:"), self.enabledCheckbox)
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
        self.applyButton.clicked.connect(self.applyParameters)
        self.closeButton.clicked.connect(self.close)

    def setComponent(self, component):
        """ Set the widget to the given component """

        self.currentComponent = component

        # check to make sure the container exists
        if not self.currentComponent.getContainer() or not cmds.objExists(self.currentComponent.getContainer()):
            raise RuntimeError("Component is not initalized. Please initalize the component to continue.")

        # ensure all maya component level changes are loaded onto the class
        self.currentComponent._loadComponentParametersToClass()

        # set the title of the window to reflect the active component
        title = self.WINDOW_TITLE + " " + self.currentComponent.name
        self.setWindowTitle(title)

        # set the commmon parameters
        self.nameLineEdit.setText(self.currentComponent.name)
        self.typeLineEdit.setText(self.currentComponent.componentType)
        self.inputMayaList.setItems(self.currentComponent.input)
        self.rigParentMayaString.setText(self.currentComponent.rigParent)
        self.tagLineEdit.setText(self.currentComponent.componentTag or None)
        self.enabledCheckbox.setChecked(self.currentComponent.enabled)

        # clear the old parameter widgets
        self.componentWidgets = list()
        for i in reversed(range(self.componentFormLayout.count())):
            self.componentFormLayout.itemAt(i).widget().deleteLater()

        # add all the new widgets
        for item in self.currentComponent.cmptSettings:
            if item not in ['name', 'input', 'rigParent', 'type', 'enabled', 'componentTag']:
                self.addWidgetFromParameter(
                    parameter=item,
                    container=self.currentComponent.getContainer(),
                    parameterType=type(component.cmptSettings[item])
                    )

    def addWidgetFromParameter(self, parameter, container, parameterType):
        """
        :return:
        """

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

            metaNode = meta.MetaNode(container)
            data = metaNode.getData(parameter)
            widget.setItems(data)
        elif parameterType == bool:
            widget = QtWidgets.QCheckBox()
            value = cmds.getAttr("{}.{}".format(container, parameter))
            widget.setChecked(value)
        else:
            widget = QtWidgets.QLineEdit()
            value = cmds.getAttr("{}.{}".format(container, parameter))
            widget.setText(value)

        # add the widget to the component layout
        self.componentFormLayout.addRow("{}:".format(parameter), widget)
        self.componentWidgets.append([parameter, widget])

    def applyParameters(self):
        """ Apply the parameters back to the component"""

        container = self.currentComponent.getContainer()

        # select the container so we can instanly see the data applied
        cmds.select(container, r=True)

        metaNode = meta.MetaNode(container)

        # insert our common parameters into the top of the list
        commonWidgets = [["input", self.inputMayaList],
                         ["rigParent", self.rigParentMayaString],
                         ["componentTag", self.tagLineEdit],
                         ["enabled", self.enabledCheckbox]]
        allComponentWidgets = commonWidgets + self.componentWidgets

        for parameter, widget in allComponentWidgets:
            if isinstance(widget, mayaDictWidget.MayaDict):
                data = widget.getData()
            elif isinstance(widget, mayaListWidget.MayaList):
                data = widget.getData()
            elif isinstance(widget, mayaStringWidget.MayaString):
                data = widget.getText()
            elif isinstance(widget, QtWidgets.QCheckBox):
                data = widget.isChecked()
            elif isinstance(widget, QtWidgets.QLineEdit):
                data = widget.text()
            else:
                data = None

            # try to set the data
            try:
                metaNode.setData(attr=parameter, value=data)
                print("Set data {}.{}: {}".format(container, parameter, data))
            except:
                om2.MGlobal.displayWarning("Failed to set data on {}.{}".format(container, parameter))

    def closeEvent(self, *args, **kwargs):
        """ Add a close event to emit the signal whenever the window is closed"""
        self.windowClosedSignal.emit(True)
