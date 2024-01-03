#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: newRigFile_dialog.py
    author: masonsmigel
    date: 08/2023
    description: 
"""

from PySide2 import QtWidgets, QtCore

from rigamajig2.maya.builder import core
from rigamajig2.ui.widgets import mayaDialog
from rigamajig2.ui.widgets import pathSelector


class CreateRigEnvDialog(mayaDialog.MayaDialog):
    """Create new rig environment dialog"""

    WINDOW_TITLE = "Create Rig Enviornment"
    WINDOW_SIZE = (375, 135)

    newRigEnviornmentCreated = QtCore.Signal(str)

    rigFileResult = None

    def __init__(self):
        """Constructor for the rig file creation"""
        super(CreateRigEnvDialog, self).__init__()
        self.rigEnvironment = None

    def __create__(self):
        """Create Widgets"""
        self.fromArchetypeRadioButton = QtWidgets.QRadioButton("New From Archetype")
        self.fromExistingRadioButton = QtWidgets.QRadioButton("Clone Existing")
        self.fromArchetypeRadioButton.setChecked(True)

        self.archetypeRadioButtonWidget = QtWidgets.QWidget()
        self.archetypeRadioButtonWidget.setFixedHeight(25)
        self.archetypeComboBox = QtWidgets.QComboBox()
        for archetype in core.getAvailableArchetypes():
            self.archetypeComboBox.addItem(archetype)

        self.sourcePath = pathSelector.PathSelector("Source:", fileMode=2)
        self.destinationPath = pathSelector.PathSelector("New Env:", fileMode=2)
        self.rigNameLineEdit = QtWidgets.QLineEdit()
        self.rigNameLineEdit.setPlaceholderText("rig_name")

        self.createButton = QtWidgets.QPushButton("Create")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

    def __layout__(self):
        """Create Layouts"""
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

    def __connect__(self):
        """Create Connections"""
        self.fromArchetypeRadioButton.toggled.connect(self.updateCreateMethod)
        self.fromExistingRadioButton.toggled.connect(self.updateCreateMethod)

        self.cancelButton.clicked.connect(self.close)
        self.createButton.clicked.connect(self.createNewRigEnvironment)

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

    def createNewRigEnvironment(self):
        """
        Create a new rig environment
        """

        destinationRigEnvironment = self.destinationPath.getPath()
        rigName = self.rigNameLineEdit.text()
        if self.fromArchetypeRadioButton.isChecked():
            archetype = self.archetypeComboBox.currentText()
            rigFile = core.newRigEnvironmentFromArchetype(
                newEnv=destinationRigEnvironment, archetype=archetype, rigName=rigName
            )
        else:
            sourceEnvironment = self.sourcePath.getPath()
            rigFile = core.createRigEnvironment(
                sourceEnvironment=sourceEnvironment, targetEnvironment=destinationRigEnvironment, rigName=rigName
            )
        # noinspection PyUnresolvedReferences
        self.newRigEnviornmentCreated.emit(rigFile)

        self.close()
