#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: actions.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
import sys
import os

# MAYA
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from shiboken2 import wrapInstance

# RIGAMJIG
import rigamajig2.maya.qc as qc
import rigamajig2.maya.data.abstract_data as abstract_data
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
import rigamajig2.maya.builder
import rigamajig2.maya.builder.builder as builder


class Actions(object):
    """ Setup the actions for the builder dialog"""
    def __init__(self, dialog):
        """
        This class will setup the actions for the the builder Dialog.
        You must pass in the dialog as the self.dialog parameter

        :param dialog: dialog to connect the actions to
        """
        self.dialog = dialog
        self.createActions()

    def createActions(self):
        """ Create the Actions"""
        # FILE
        self.newRigFileAction = QtWidgets.QAction("New Rig File", self.dialog)
        self.newRigFileAction.setIcon(QtGui.QIcon(":fileNew.png"))
        self.newRigFileAction.triggered.connect(self.createRigEnviornment)

        self.loadRigFileAction = QtWidgets.QAction("Load Rig File", self.dialog)
        self.loadRigFileAction.setIcon(QtGui.QIcon(":folder-open.png"))
        self.loadRigFileAction.triggered.connect(self.loadRigFile)

        self.saveRigFileAction = QtWidgets.QAction("Save Rig File", self.dialog)
        self.saveRigFileAction.setIcon(QtGui.QIcon(":save.png"))
        self.saveRigFileAction.triggered.connect(self.saveRigFile)

        self.reloadRigFileAction = QtWidgets.QAction("Reload Rig File", self.dialog)
        self.reloadRigFileAction.setIcon(QtGui.QIcon(":refresh.png"))
        self.reloadRigFileAction.triggered.connect(self.reloadRigFile)

        # UTILS
        self.reloadRigamajigModulesAction = QtWidgets.QAction("Reload Rigamajig2 Modules", self.dialog)
        self.reloadRigamajigModulesAction.triggered.connect(self.reloadRigamajigModules)

        # TOOLS
        self.runPerformanceTestAction = QtWidgets.QAction("Run Performance Test", self.dialog)
        self.runPerformanceTestAction.triggered.connect(self.runPerformanceTest)

        self.generateRandomAnimationAction = QtWidgets.QAction("Generate Random Animation", self.dialog)
        self.generateRandomAnimationAction.triggered.connect(self.generateRandomAnimation)

        # HELP
        self.showDocumentationAction = QtWidgets.QAction("Documentation", self.dialog)
        self.showDocumentationAction.triggered.connect(self.showDocumentation)

        self.showAboutAction = QtWidgets.QAction("About", self.dialog)
        self.showAboutAction.triggered.connect(self.showAbout)

    def createRigEnviornment(self):
        """ Create Rig Enviornment"""
        createDialog = CreateRigEnvDialog()
        createDialog.newRigEnviornmentCreated.connect(self.dialog.setRigFile)
        createDialog.showDialog()

    def loadRigFile(self):
        """ Load a rig file"""
        fileDialog = QtWidgets.QFileDialog()
        fileDialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
        fileDialog.setNameFilters(["Rig Files (*.rig)"])

        fileDialog.exec_()

        if fileDialog.selectedFiles():
            self.dialog.setRigFile(fileDialog.selectedFiles()[0])

    def saveRigFile(self):
        """ Save out a rig file """
        data = abstract_data.AbstractData()
        data.read(self.dialog.rigFile)
        newData = data.getData()

        # Save the main feilds
        newData[builder.RIG_NAME] = self.dialog.assetNameLineEdit.text()
        preScripts = self.dialog.modelWidget.preScriptRunner.getCurrentScriptList(relativePaths=True)
        newData[builder.PRE_SCRIPT] = preScripts

        postScripts = self.dialog.buildWidget.postScriptScriptRunner.getCurrentScriptList(relativePaths=True)
        newData[builder.POST_SCRIPT] = postScripts

        pubScripts = self.dialog.publishWidget.publishScriptRunner.getCurrentScriptList(relativePaths=True)
        newData[builder.PUB_SCRIPT] = pubScripts

        newData[builder.MODEL_FILE] = self.dialog.modelWidget.modelPathSelector.getPath()
        newData[builder.SKELETON_POS] = self.dialog.jointWidget.jointPositionPathSelector.getPath()
        newData[builder.GUIDES] = self.dialog.intalizeWidget.guidePathSelector.getPath()
        newData[builder.COMPONENTS] = self.dialog.intalizeWidget.componentsPathSelector.getPath()
        newData[builder.CONTROL_SHAPES] = self.dialog.controlsWidget.controlPathSelector.getPath()
        newData[builder.SKINS] = self.dialog.deformationWidget.skinPathSelector.getPath()
        newData[builder.PSD] = self.dialog.deformationWidget.psdPathSelector.getPath()
        newData[builder.OUTPUT_RIG] = self.dialog.publishWidget.outPathSelector.getPath()
        newData[builder.OUTPUT_RIG_FILE_TYPE] = self.dialog.publishWidget.outFileTypeComboBox.currentText()

        data.setData(newData)
        data.write(self.dialog.rigFile)
        builder.logger.info("data saved to : {}".format(self.dialog.rigFile))

    def reloadRigFile(self):
        """ Reload rig file"""
        self.dialog.setRigFile(self.dialog.rigFile)

    # TOOLS MENU
    def runPerformanceTest(self):
        """ Run Performance tests"""
        qc.runPerformanceTest()

    def generateRandomAnimation(self):
        """ Generate Random animation"""
        qc.generateRandomAnim()

    def reloadRigamajigModules(self):
        """ Reload riamajig modules"""
        import rigamajig2
        rigamajig2.reloadModule(log=True)

    # SHOW HELP
    def showDocumentation(self):
        """ Open Documentation"""
        pass

    def showAbout(self):
        """ Show about"""
        pass


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
