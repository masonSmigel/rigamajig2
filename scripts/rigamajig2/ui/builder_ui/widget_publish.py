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

from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import core
# RIGAMAJIG2
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui import style
from rigamajig2.ui.builder_ui.widgets import builderSection, scriptRunner
from rigamajig2.ui.widgets import mayaMessageBox, pathSelector


class PublishWidget(builderSection.BuilderSection):
    """ Publish layout for the builder UI """

    WIDGET_TITLE = "Publish"

    def createWidgets(self):
        """ Create Widgets"""
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

    def createLayouts(self):
        """ Create Layouts"""
        self.mainWidget.addWidget(self.mergeDeformLayersButton)
        self.mainWidget.addSpacing(4)
        self.mainWidget.addWidget(self.pubScriptRunner)

        self.mainWidget.addSpacing(10)
        publishFileLayout = QtWidgets.QHBoxLayout()
        publishFileLayout.addWidget(QtWidgets.QLabel("suffix:"))
        publishFileLayout.addWidget(self.outFileSuffix)
        publishFileLayout.addSpacing(60)
        publishFileLayout.addWidget(self.outFileTypeComboBox)
        self.mainWidget.addLayout(publishFileLayout)
        self.mainWidget.addWidget(self.outPathSelector)
        self.mainWidget.addWidget(self.dryPublishButton)
        self.mainWidget.addWidget(self.publishButton)
        self.mainWidget.addWidget(self.saveFBXCheckbox)

    def createConnections(self):
        """ Create Connections """
        self.mergeDeformLayersButton.clicked.connect(self.mergeDeformLayers)
        self.dryPublishButton.clicked.connect(self.dryPublish)
        self.publishButton.clicked.connect(self.publish)

    def setBuilder(self, builder):
        """ Set the active builder """
        super().setBuilder(builder)
        self.outPathSelector.setRelativePath(self.builder.getRigEnviornment())

        # clear the ui
        self.pubScriptRunner.clearScript()

        # update data within the rig
        outFile = self.builder.getRigData(self.builder.getRigFile(), constants.OUTPUT_RIG)
        self.outPathSelector.selectPath(outFile)

        # update the script runner
        scripts = core.GetCompleteScriptList.getScriptList(self.builder.rigFile, constants.PUB_SCRIPT, asDict=True)
        self.pubScriptRunner.addScriptsWithRecursionData(scripts)

        # set the default output file type
        fileTypeText = self.builder.getRigData(self.builder.getRigFile(), constants.OUTPUT_RIG_FILE_TYPE)
        index = self.outFileTypeComboBox.findText(fileTypeText, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.outFileTypeComboBox.setCurrentIndex(index)

        # set the file selector
        self.outFileSuffix.clear()
        fileSuffix = self.builder.getRigData(self.builder.getRigFile(), constants.OUTPUT_FILE_SUFFIX)
        if fileSuffix:
            self.outFileSuffix.setText(fileSuffix)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.builder.mergeDeformLayers()
        self.pubScriptRunner.executeAllScripts()

    # CONNECTIONS

    @QtCore.Slot()
    def dryPublish(self):
        """ run all the _publish steps without saving the file"""
        self.builder.run(publish=True, savePublish=False)

    @QtCore.Slot()
    def mergeDeformLayers(self):
        """Merge the deformation layers"""
        self.builder.mergeDeformLayers()

    @QtCore.Slot()
    def publish(self):
        """ _publish the rig"""
        confirmPublishMessage = mayaMessageBox.MayaMessageBox(
            title="Publish the Rig",
            message="Proceeding will rebuild a fresh rig from saved data overwriting any existing published rigs.",
            icon="warning")
        confirmPublishMessage.setButtonsSaveDiscardCancel()

        res = confirmPublishMessage.exec_()

        if res == confirmPublishMessage.Save:
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
