#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: newRigFileDialog.py
    author: masonsmigel
    date: 08/2023
    discription: 

"""
import sys

from PySide2 import QtWidgets, QtCore
from maya import OpenMayaUI as omui, cmds as cmds
from shiboken2 import wrapInstance

import rigamajig2.maya
from rigamajig2.ui.builder_ui.widgets import pathSelector


class CreateRigEnvDialog(QtWidgets.QDialog):
    """ Create new rig environment dialog"""
    WINDOW_TITLE = "Create Rig Enviornment"

    newRigEnviornmentCreated = QtCore.Signal(str)

    rigFileResult = None

    def showDialog(self):
        """ Show the dialog"""
        self.exec_()

    def __init__(self):
        """ Constructor for the rig file creation"""
        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(CreateRigEnvDialog, self).__init__(mayaMainWindow)
        self.rigEnviornment = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setFixedSize(375, 135)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.updateCreateMethod()

    def createWidgets(self):
        """ Create Widgets"""
        self.fromArchetypeRadioButton = QtWidgets.QRadioButton("New From Archetype")
        self.fromExistingRadioButton = QtWidgets.QRadioButton("Clone Existing")
        self.fromArchetypeRadioButton.setChecked(True)

        self.archetypeRadioButtonWidget = QtWidgets.QWidget()
        self.archetypeRadioButtonWidget.setFixedHeight(25)
        self.archetypeComboBox = QtWidgets.QComboBox()
        for archetype in rigamajig2.maya.builder.core.getAvailableArchetypes():
            self.archetypeComboBox.addItem(archetype)

        self.sourcePath = pathSelector.PathSelector("Source:", fileMode=2)
        self.destinationPath = pathSelector.PathSelector("New Env:", fileMode=2)
        self.rigNameLineEdit = QtWidgets.QLineEdit()
        self.rigNameLineEdit.setPlaceholderText("rig_name")

        self.createButton = QtWidgets.QPushButton("Create")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

    def createLayouts(self):
        """ Create Layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(4)

        radioButtonLayout = QtWidgets.QHBoxLayout()
        radioButtonLayout.addSpacing(15)
        radioButtonLayout.addWidget(self.fromArchetypeRadioButton)
        radioButtonLayout.addWidget(self.fromExistingRadioButton)

        archetypeRadioButtonLayout = QtWidgets.QHBoxLayout(self.archetypeRadioButtonWidget)
        archetypeRadioButtonLayout.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel("Archetype:")
        label.setFixedWidth(60)
        archetypeRadioButtonLayout.addWidget(label)
        archetypeRadioButtonLayout.addWidget(self.archetypeComboBox)

        rigNameLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Rig Name:")
        label.setFixedWidth(60)
        rigNameLayout.addWidget(label)
        rigNameLayout.addWidget(self.rigNameLineEdit)

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.createButton)

        mainLayout.addLayout(radioButtonLayout)
        mainLayout.addWidget(self.archetypeRadioButtonWidget)
        mainLayout.addWidget(self.sourcePath)
        mainLayout.addWidget(self.destinationPath)
        mainLayout.addLayout(rigNameLayout)
        mainLayout.addLayout(buttonLayout)

    def createConnections(self):
        """ Create Connections"""
        self.fromArchetypeRadioButton.toggled.connect(self.updateCreateMethod)
        self.fromExistingRadioButton.toggled.connect(self.updateCreateMethod)

        self.cancelButton.clicked.connect(self.close)
        self.createButton.clicked.connect(self.createNewRigEnviornment)

    def updateCreateMethod(self):
        """
        Update the UI creation method
        :return:
        """
        if self.fromArchetypeRadioButton.isChecked():
            self.archetypeRadioButtonWidget.setVisible(True)
            self.sourcePath.setVisible(False)
        else:
            self.archetypeRadioButtonWidget.setVisible(False)
            self.sourcePath.setVisible(True)

    def createNewRigEnviornment(self):
        """
        Create a new rig enviornment
        """

        destinationRigEnviornment = self.destinationPath.getPath()
        rigName = self.rigNameLineEdit.text()
        if self.fromArchetypeRadioButton.isChecked():
            archetype = self.archetypeComboBox.currentText()
            rigFile = rigamajig2.maya.builder.core.newRigEnviornmentFromArchetype(
                newEnv=destinationRigEnviornment,
                archetype=archetype,
                rigName=rigName)
        else:
            sourceEnviornment = self.sourcePath.getPath()
            rigFile = rigamajig2.maya.builder.core.createRigEnviornment(
                sourceEnviornment=sourceEnviornment,
                targetEnviornment=destinationRigEnviornment,
                rigName=rigName)
        self.newRigEnviornmentCreated.emit(rigFile)

        self.close()
