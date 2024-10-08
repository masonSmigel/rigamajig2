#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: publish_section.py
    author: masonsmigel
    date: 07/2022
    description: 
"""
# PYTHON
from PySide2 import QtCore
from PySide2 import QtWidgets

from rigamajig2.maya.builder import builder
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import scriptManager
# RIGAMAJIG2
from rigamajig2.shared import common
from rigamajig2.ui.builder import style
from rigamajig2.ui.builder.customs import section, scriptRunner
from rigamajig2.ui.widgets import mayaMessageBox, pathSelector


class PublishSection(section.BuilderSection):
    """Publish layout for the builder UI"""

    WIDGET_TITLE = "Publish"

    def createWidgets(self):
        """Create Widgets"""
        self.pubScriptRunner = scriptRunner.ScriptRunner(title="Publish-Scripts:")

        self.outFileSuffix = QtWidgets.QLineEdit()
        self.outFileSuffix.setPlaceholderText("_rig")

        self.outPathSelector = pathSelector.PathSelector(
            "out file:", caption="Select a location to save", fileFilter=common.MAYA_FILTER, fileMode=2
        )
        self.dryPublishButton = QtWidgets.QPushButton("Dry Publish Rig")
        self.publishButton = QtWidgets.QPushButton("Publish Rig")
        self.publishButton.setFixedHeight(style.LARGE_BTN_HEIGHT)

        self.outFileTypeComboBox = QtWidgets.QComboBox()
        self.outFileTypeComboBox.addItem("ma")
        self.outFileTypeComboBox.addItem("mb")

    def createLayouts(self):
        """Create Layouts"""
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
        self.mainWidget.addWidget(self.outPathSelector)
        self.mainWidget.addWidget(self.dryPublishButton)
        self.mainWidget.addWidget(self.publishButton)

    def createConnections(self):
        """Create Connections"""
        self.pubScriptRunner.scriptsUpdated.connect(self._setLocalPubScripts)
        self.outPathSelector.pathUpdated.connect(self._setOutputFilePath)
        self.outFileSuffix.textChanged.connect(self._setOutputFileSuffix)
        self.outFileTypeComboBox.currentTextChanged.connect(self._setOutputFileType)

        self.dryPublishButton.clicked.connect(self._onDryPublish)
        self.publishButton.clicked.connect(self._onPublishWithUiData)

    @QtCore.Slot()
    def _setBuilder(self, builder):
        """Set the active builder"""
        super()._setBuilder(builder)
        self.outPathSelector.setRelativePath(self.builder.getRigEnvironment())

        # clear the ui
        self.pubScriptRunner.clearScript()

        # update data within the rig
        outFile = self.builder.getRigData(self.builder.getRigFile(), constants.OUTPUT_RIG)
        self.outPathSelector.selectPath(outFile)

        # update the script runner
        scripts = scriptManager.GetCompleteScriptList.getScriptList(self.builder.rigFile, constants.PUB_SCRIPT)
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

    @QtCore.Slot()
    def _runWidget(self):
        """Run this widget from the builder breakpoint runner"""
        self.pubScriptRunner.executeAllScripts()

    @QtCore.Slot()
    def _onDryPublish(self):
        """run all the _publish steps without saving the file"""
        self.builder.run(publish=True, savePublish=False)

    @QtCore.Slot()
    def _onPublishWithUiData(self) -> float or None:
        """
        publish the rig with the data from the ui
        :returns: time taken to export the rig.
        """
        confirmPublishMessage = mayaMessageBox.MayaMessageBox(
            title="Publish the Rig",
            message="Proceeding will rebuild a fresh rig from saved data overwriting any existing published rigs.",
            icon="warning",
        )
        confirmPublishMessage.setButtonsSaveDiscardCancel()

        # if the user escapes from the publish
        if not confirmPublishMessage.getResult():
            return None

        # publish with a new builder instance.
        publishBuilder = builder.Builder()
        publishBuilder.setRigFile(self.builder.getRigFile())

        # override the builder
        publishBuilder.outputFilePath = self.outPathSelector.getPath()
        publishBuilder.outputFileSuffix = self.outFileSuffix.text()
        publishBuilder.outputFileType = self.outFileTypeComboBox.currentText()

        publishBuilder.run(publish=True, savePublish=True)

    def _setOutputFilePath(self, filepath):
        if self.builder:
            self.builder.outputFilePath = filepath
            self.postRigFileModifiedEvent()

    def _setOutputFileSuffix(self):
        if self.builder:
            self.builder.outputFileSuffix = self.outFileSuffix.text()
            self.postRigFileModifiedEvent()

    def _setOutputFileType(self, fileType):
        if self.builder:
            self.builder.outputFileType = fileType
            self.postRigFileModifiedEvent()

    @QtCore.Slot()
    def _setLocalPubScripts(self, scriptData):
        if not builder:
            return

        localPubScripts = list()
        for key, scriptItemData in scriptData.items():
            if scriptItemData.get(scriptRunner.CUSTOM_DATA_KEY) == 0:
                filePath = scriptItemData.get(scriptRunner.FILEPATH_DATA_KEY)
                localPubScripts.append(filePath)

        self.builder.localPubScripts = localPubScripts
        self.postRigFileModifiedEvent()
