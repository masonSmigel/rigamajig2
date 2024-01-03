#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: createComponentDialog.py
    author: masonsmigel
    date: 01/2024
    description: 

"""
import re
import sys

import maya.OpenMayaUI as omui
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2.shiboken2 import wrapInstance

from rigamajig2.maya.builder import builder
from rigamajig2.maya.builder import componentManager
from rigamajig2.ui.resources import Resources


# TODO: simplify this. This voilates DRY!!!
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


class CreateComponentDialog(QtWidgets.QDialog):
    """
    Create new component dialog
    """

    WINDOW_TITLE = "Create New Component"

    newComponentCreatedSignal = QtCore.Signal(str, str, str, str)

    def __init__(self):
        """
        constructor for the create component dialog
        """
        if sys.version_info.major < 3:
            mainMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mainMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(CreateComponentDialog, self).__init__(mainMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(400, 180)
        self.resize(400, 440)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

        self.updateComboBox()

    def createWidgets(self):
        """Create widgets"""
        self.nameLineEdit = QtWidgets.QLineEdit()

        self.componentTypeComboBox = QtWidgets.QComboBox()
        self.componentTypeComboBox.setMinimumHeight(30)
        self.componentTypeComboBox.setMaxVisibleItems(30)

        self.inputLineEdit = QtWidgets.QLineEdit()
        self.inputLineEdit.setPlaceholderText("[]")
        self.loadSelectedAsInput = QtWidgets.QPushButton("<")
        self.loadSelectedAsInput.setMaximumWidth(30)

        self.rigParentLineEdit = QtWidgets.QLineEdit()
        self.rigParentLineEdit.setPlaceholderText("None")
        self.loadSelectedAsRigParent = QtWidgets.QPushButton("<")
        self.loadSelectedAsRigParent.setMaximumWidth(30)

        self.discriptionTextEdit = QtWidgets.QTextEdit()
        self.discriptionTextEdit.setReadOnly(True)

        self.applyAndCloseButton = QtWidgets.QPushButton("Create and Close")
        self.applyButton = QtWidgets.QPushButton("Create")
        self.closeButton = QtWidgets.QPushButton("Cancel")

    def createLayouts(self):
        """Create Layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(4)

        nameLayout = QtWidgets.QHBoxLayout()
        nameLayout.addWidget(QtWidgets.QLabel("name:"))
        nameLayout.addWidget(self.nameLineEdit)
        nameLayout.addSpacing(30)
        nameLayout.addWidget(QtWidgets.QLabel("type:"))
        nameLayout.addWidget(self.componentTypeComboBox)

        inputLayout = QtWidgets.QHBoxLayout()
        inputLayout.addWidget(self.inputLineEdit)
        inputLayout.addWidget(self.loadSelectedAsInput)

        rigParentLayout = QtWidgets.QHBoxLayout()
        rigParentLayout.addWidget(self.rigParentLineEdit)
        rigParentLayout.addWidget(self.loadSelectedAsRigParent)

        widgetLayout = QtWidgets.QFormLayout()
        widgetLayout.addRow(QtWidgets.QLabel("input:"), inputLayout)
        widgetLayout.addRow(QtWidgets.QLabel("rigParent:"), rigParentLayout)

        applyButtonLayout = QtWidgets.QHBoxLayout()
        applyButtonLayout.addWidget(self.applyAndCloseButton)
        applyButtonLayout.addWidget(self.applyButton)
        applyButtonLayout.addWidget(self.closeButton)

        mainLayout.addLayout(nameLayout)
        mainLayout.addLayout(widgetLayout)
        mainLayout.addSpacing(5)
        mainLayout.addWidget(self.discriptionTextEdit)
        mainLayout.addLayout(applyButtonLayout)

    def createConnections(self):
        """Create Connections"""
        self.loadSelectedAsInput.clicked.connect(self.addSelectionAsInput)
        self.loadSelectedAsRigParent.clicked.connect(self.addSelectionAsRigParent)
        self.componentTypeComboBox.currentIndexChanged.connect(self.updateDiscription)
        self.closeButton.clicked.connect(self.close)
        self.applyButton.clicked.connect(self.apply)
        self.applyAndCloseButton.clicked.connect(self.applyAndClose)

    def updateComboBox(self):
        """Update the combobox with the exisitng component types"""
        self.componentTypeComboBox.clear()
        tempBuilder = builder.Builder()
        for i, componentType in enumerate(sorted(tempBuilder.getAvailableComponents())):
            self.componentTypeComboBox.addItem(componentType)
            self.componentTypeComboBox.setItemIcon(i, _getComponentIcon(componentType))

            # get the UI Color
            uiColor = _getComponentColor(componentType)
            self.componentTypeComboBox.setItemData(i, QtGui.QColor(*uiColor), QtCore.Qt.TextColorRole)

    def updateDiscription(self):
        """
        Update the UI discription based on the currently selection component type
        """
        self.discriptionTextEdit.clear()

        componentType = self.componentTypeComboBox.currentText()
        componentObject = componentManager.createComponentClassInstance(componentType)

        classDocs = componentObject.__doc__ or ""
        initDocs = componentObject.__init__.__doc__ or ""
        docstring = classDocs + "\n---- parameters ----\n" + initDocs
        if docstring:
            docstring = re.sub(" {4}", "", docstring.strip())

        self.discriptionTextEdit.setText(docstring)

    def addSelectionAsInput(self):
        """Add the selection as the input"""
        self.inputLineEdit.clear()
        sel = cmds.ls(sl=True)
        selList = list()
        for s in sel:
            selList.append(str(s))

        self.inputLineEdit.setText(str(selList))

    def addSelectionAsRigParent(self):
        """Add the selection as the rigParent"""
        self.rigParentLineEdit.clear()
        sel = cmds.ls(sl=True)

        if len(sel) > 0:
            self.rigParentLineEdit.setText(str(sel[0]))

    def apply(self):
        """
        Apply (create the component and widget) but keep the UI open
        :return:
        """
        componentType = self.componentTypeComboBox.currentText()

        name = self.nameLineEdit.text() or None
        input = self.inputLineEdit.text() or []
        rigParent = self.rigParentLineEdit.text() or None

        # emit the data to the createComponent mehtod of the component manager.
        # if the type is main then we can ignore the input.
        if name and componentType == "main.Main":
            self.newComponentCreatedSignal.emit(name, componentType, "[]", rigParent)
        elif name and input:
            self.newComponentCreatedSignal.emit(name, componentType, input, rigParent)

    def applyAndClose(self):
        """Apply and close the Ui"""
        self.apply()
        self.close()
