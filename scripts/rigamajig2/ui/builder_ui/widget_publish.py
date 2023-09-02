#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: widget_publish.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

# RIGAMAJIG2
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui.widgets import pathSelector, collapseableWidget, scriptRunner
from rigamajig2.ui.widgets import mayaMessageBox
from rigamajig2.ui.builder_ui import style
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import core


class PublishWidget(QtWidgets.QWidget):
    """ Publish layout for the builder UI """

    def __init__(self, builder=None):
        super(PublishWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets"""
        self.mainCollapseableWidget = collapseableWidget.BuilderHeader('Publish', addCheckbox=True)
        self.pubScriptRunner = scriptRunner.ScriptRunner(title="Publish-Scripts:")

        self.outFileSuffix = QtWidgets.QLineEdit()
        self.outFileSuffix.setPlaceholderText("_rig")

        self.outPathSelector = pathSelector.PathSelector(
            "out file:",
            caption="Select a location to save",
            fileFilter=common.MAYA_FILTER,
            fileMode=2
            )
        self.mergeDeformLayersButton = QtWidgets.QPushButton("Merge Deform Layers")

        self.dryPublishButton = QtWidgets.QPushButton("Dry Publish Rig")
        # self.dryPublishButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.publishButton = QtWidgets.QPushButton("Publish Rig")
        self.publishButton.setFixedHeight(style.LARGE_BTN_HEIGHT)

        self.outFileTypeComboBox = QtWidgets.QComboBox()
        self.outFileTypeComboBox.addItem('ma')
        self.outFileTypeComboBox.addItem('mb')

        self.saveFBXCheckbox = QtWidgets.QCheckBox("Export FBX Skeletal Mesh")

        # self.runSelectedButton = QtWidgets.QPushButton("Run Selected")
        # self.runButton = QtWidgets.QPushButton("Run")
        # self.runButton.setFixedWidth(80)
        #
        # self.closeButton = QtWidgets.QPushButton("Close")

    def createLayouts(self):
        """ Create Layouts"""
        # setup the main layout.
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.mainCollapseableWidget.addWidget(self.pubScriptRunner)
        self.mainCollapseableWidget.addSpacing(4)
        self.mainCollapseableWidget.addWidget(self.mergeDeformLayersButton)

        self.mainCollapseableWidget.addSpacing(10)
        publishFileLayout = QtWidgets.QHBoxLayout()
        publishFileLayout.addWidget(QtWidgets.QLabel("suffix:"))
        publishFileLayout.addWidget(self.outFileSuffix)
        publishFileLayout.addSpacing(60)
        publishFileLayout.addWidget(self.outFileTypeComboBox)
        self.mainCollapseableWidget.addLayout(publishFileLayout)
        self.mainCollapseableWidget.addWidget(self.outPathSelector)
        self.mainCollapseableWidget.addWidget(self.dryPublishButton)
        self.mainCollapseableWidget.addWidget(self.publishButton)
        self.mainCollapseableWidget.addWidget(self.saveFBXCheckbox)

        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections """
        self.mergeDeformLayersButton.clicked.connect(self.mergeDeformLayers)
        self.dryPublishButton.clicked.connect(self.dryPublish)
        self.publishButton.clicked.connect(self.publish)

    def setBuilder(self, builder):
        """ Set the active builder """
        rigEnv = builder.getRigEnviornment()
        rigFile = builder.getRigFile()
        self.builder = builder
        self.outPathSelector.setRelativePath(rigEnv)

        # clear the ui
        self.pubScriptRunner.clearScript()

        # update data within the rig
        outFile = self.builder.getRigData(self.builder.getRigFile(), constants.OUTPUT_RIG)
        self.outPathSelector.selectPath(outFile)

        # update the script runner
        scripts = core.GetCompleteScriptList.getScriptList(self.builder.rigFile, constants.PUB_SCRIPT, asDict=True)
        self.pubScriptRunner.addScriptsWithRecursionData(scripts)

        # set the default output file type
        fileTypeText = self.builder.getRigData(rigFile, constants.OUTPUT_RIG_FILE_TYPE)
        index = self.outFileTypeComboBox.findText(fileTypeText, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.outFileTypeComboBox.setCurrentIndex(index)

        # set the file selector
        self.outFileSuffix.clear()
        fileSuffix = self.builder.getRigData(rigFile, constants.OUTPUT_FILE_SUFFIX)
        if fileSuffix:
            self.outFileSuffix.setText(fileSuffix)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.pubScriptRunner.executeAllScripts()
        self.builder.mergeDeformLayers()

    @property
    def isChecked(self):
        """ return the checked state of the collapseable widget"""
        return self.mainCollapseableWidget.isChecked()

    # CONNECTIONS

    @QtCore.Slot()
    def dryPublish(self):
        """ run all the publish steps without saving the file"""
        self.builder.run(publish=True, savePublish=False)

    @QtCore.Slot()
    def mergeDeformLayers(self):
        """Merge the deformation layers"""
        self.builder.mergeDeformLayers()

    @QtCore.Slot()
    def publish(self):
        """ publish the rig"""
        confirmPublishMessage = mayaMessageBox.MayaMessageBox()
        confirmPublishMessage.setText("Publish the rig")
        confirmPublishMessage.setWarning()

        confirmPublishMessage.setInformativeText(
            "Proceeding will rebuild a fresh rig from saved data overwriting any existing published rigs."
            )
        confirmPublishMessage.setStandardButtons(
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )

        confirmPublishMessage.setDefaultButton(QtWidgets.QMessageBox.Save)
        res = confirmPublishMessage.exec_()

        if res == QtWidgets.QMessageBox.Save:
            outputfile = self.outPathSelector.getPath()
            fileType = self.outFileTypeComboBox.currentText()
            suffix = self.outFileSuffix.text()
            saveFBX = self.saveFBXCheckbox.isChecked()

            finalTime = self.builder.run(publish=True,
                                         outputfile=outputfile,
                                         suffix=suffix,
                                         assetName=None,
                                         fileType=fileType,
                                         saveFBX=saveFBX)

            return finalTime
