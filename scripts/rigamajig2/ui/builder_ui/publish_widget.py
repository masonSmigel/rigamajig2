#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: publish_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
from rigamajig2.ui.builder_ui import constants as ui_constants
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
        self.mainCollapseableWidget = collapseableWidget.CollapsibleWidget('Publish', addCheckbox=True)
        self.publishScriptRunner = scriptRunner.ScriptRunner(title="Publish-Scripts:")
        self.outPathSelector = pathSelector.PathSelector(
            "out file:",
            caption="Select a location to save",
            fileFilter=ui_constants.MAYA_FILTER,
            fileMode=2
            )
        self.publishButton = QtWidgets.QPushButton("Publish Rig")
        self.publishButton.setFixedHeight(ui_constants.LARGE_BTN_HEIGHT)

        self.outFileTypeComboBox = QtWidgets.QComboBox()
        self.outFileTypeComboBox.addItem('ma')
        self.outFileTypeComboBox.addItem('mb')

        self.runSelectedButton = QtWidgets.QPushButton("Run Selected")
        self.runButton = QtWidgets.QPushButton("Run")
        self.runButton.setFixedWidth(80)

        self.closeButton = QtWidgets.QPushButton("Close")

    def createLayouts(self):
        """ Create Layouts"""
        # setup the main layout.
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.mainCollapseableWidget.addWidget(self.publishScriptRunner)
        self.mainCollapseableWidget.addSpacing(10)
        publishFileLayout = QtWidgets.QHBoxLayout()
        publishFileLayout.addWidget(self.outPathSelector)
        publishFileLayout.addWidget(self.outFileTypeComboBox)
        self.mainCollapseableWidget.addLayout(publishFileLayout)
        self.mainCollapseableWidget.addWidget(self.publishButton)

        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections """
        self.publishButton.clicked.connect(self.publish)

    def setBuilder(self, builder):
        """ Set the active builder """
        rigEnv = builder.getRigEnviornment()
        rigFile = builder.getRigFile()
        self.builder = builder
        self.outPathSelector.setRelativePath(rigEnv)

        # clear the ui
        self.publishScriptRunner.clearScript()

        # update data within the rig
        outFile = self.builder.getRigData(self.builder.getRigFile(), constants.OUTPUT_RIG)
        if outFile:
            self.outPathSelector.setPath(outFile)

        # update the script runner
        scripts = core.GetCompleteScriptList.getScriptList(self.builder.rigFile, constants.PUB_SCRIPT)
        self.publishScriptRunner.addScripts(scripts)

        # set the default output file type
        fileTypeText = self.builder.getRigData(rigFile, constants.OUTPUT_RIG_FILE_TYPE)
        index = self.outFileTypeComboBox.findText(fileTypeText, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.outFileTypeComboBox.setCurrentIndex(index)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.publishScriptRunner.executeAllScripts()

    @property
    def isChecked(self):
        """ return the checked state of the collapseable widget"""
        return self.mainCollapseableWidget.isChecked()

    # CONNECTIONS
    def publish(self):
        """ publish the rig"""
        confirmPublishMessage = QtWidgets.QMessageBox()
        confirmPublishMessage.setText("Publish the rig")

        confirmPublishMessage.setInformativeText(
            "Proceeding will rebuild a fresh rig from saved data overwriting any existing any published rigs."
            )
        confirmPublishMessage.setStandardButtons(
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )

        confirmPublishMessage.setDefaultButton(QtWidgets.QMessageBox.Save)
        res = confirmPublishMessage.exec_()

        if res == QtWidgets.QMessageBox.Save:
            outputfile = self.outPathSelector.getPath()
            fileType = self.outFileTypeComboBox.currentText()

            self.builder.run(publish=True, outputfile=outputfile, assetName=None, fileType=fileType)
