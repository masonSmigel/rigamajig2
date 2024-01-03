#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: builderSection.py
    author: masonsmigel
    date: 07/2022
    description:
"""

# PYTHON
from PySide2 import QtCore
from PySide2 import QtWidgets

from rigamajig2.maya.builder import dataIO
from rigamajig2.maya.builder import scriptManager
from rigamajig2.maya.builder.constants import PSD, POST_SCRIPT
# RIGAMAJIG2
from rigamajig2.shared import common
from rigamajig2.ui.builder import style
from rigamajig2.ui.builder.customs import dataLoader, builderSection, scriptRunner
from rigamajig2.ui.resources import Resources


class BuildSection(builderSection.BuilderSection):
    """ Build layout for the builder UI """

    WIDGET_TITLE = "Build Rig"

    def createWidgets(self):
        """ Create Widgets """

        self.completeButton = QtWidgets.QPushButton("Build Rig")
        self.completeButton.setFixedHeight(45)

        self.buildButton = QtWidgets.QPushButton("Build")
        self.connectButton = QtWidgets.QPushButton("Connect")
        self.finalizeButton = QtWidgets.QPushButton("Finalize")

        self.psdDataLoader = dataLoader.DataLoader(
            label="PSD Readers:",
            caption="Select a Pose Reader File",
            fileFilter=common.JSON_FILTER,
            fileMode=1,
            dataFilteringEnabled=True,
            dataFilter=["PSDData"])

        self.loadPsdButton = QtWidgets.QPushButton("Load Pose Readers")
        self.loadPsdButton.setIcon(Resources.getIcon(":loadPsd.png"))
        self.savePsdButton = QtWidgets.QPushButton("Save Pose Readers")
        self.savePsdButton.setIcon(Resources.getIcon(":savePsd.png"))

        self.loadPsdButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.savePsdButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadPsdButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.savePsdButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.loadPsdModeCheckbox = QtWidgets.QComboBox()
        self.loadPsdModeCheckbox.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadPsdModeCheckbox.addItems(["append", "replace"])

        self.postScriptRunner = scriptRunner.ScriptRunner(title="Post-Scripts:")

    def createLayouts(self):
        """ Create Layouts """

        buildLayout = QtWidgets.QHBoxLayout()
        buildLayout.addWidget(self.buildButton)
        buildLayout.addWidget(self.connectButton)
        buildLayout.addWidget(self.finalizeButton)

        self.mainWidget.addWidget(self.completeButton)
        self.mainWidget.addLayout(buildLayout)

        psdButtonLayout = QtWidgets.QHBoxLayout()
        psdButtonLayout.setContentsMargins(0, 0, 0, 0)
        psdButtonLayout.setSpacing(4)
        psdButtonLayout.addWidget(self.loadPsdButton)
        psdButtonLayout.addWidget(self.savePsdButton)
        psdButtonLayout.addWidget(self.loadPsdModeCheckbox)

        self.mainWidget.addSpacing(10)
        self.mainWidget.addWidget(self.psdDataLoader)
        self.mainWidget.addLayout(psdButtonLayout)

        self.mainWidget.addSpacing()
        self.mainWidget.addWidget(self.postScriptRunner)

    def createConnections(self):
        """ Create Connections """
        self.postScriptRunner.scriptsUpdated.connect(self._setLocalPostScripts)
        self.psdDataLoader.filesUpdated.connect(self._setPoseReadersFiles)
        self.completeButton.clicked.connect(self._onCompleteBuild)
        self.buildButton.clicked.connect(self._onBuilderBuild)
        self.connectButton.clicked.connect(self._onBuilderConnect)
        self.finalizeButton.clicked.connect(self._onBuilderFinalize)
        self.loadPsdButton.clicked.connect(self._onLoadPoseReaders)
        self.savePsdButton.clicked.connect(self._onSavePoseReaders)

    @QtCore.Slot()
    def _setBuilder(self, builder):
        """ Set the builder """
        super()._setBuilder(builder)
        self.psdDataLoader.clear()
        self.postScriptRunner.clearScript()
        self.psdDataLoader.setRelativePath(self.builder.getRigEnvironment())

        scripts = scriptManager.GetCompleteScriptList.getScriptList(self.builder.rigFile, POST_SCRIPT)
        self.postScriptRunner.addScriptsWithRecursionData(scripts)

        psdFiles = self.builder.getRigData(self.builder.getRigFile(), PSD)
        self.psdDataLoader.selectPaths(psdFiles)

    @QtCore.Slot()
    def _runWidget(self):
        """ Run this widget from the builder breakpoint runner """
        self._onCompleteBuild()
        self._onLoadPoseReaders()
        self.postScriptRunner.executeAllScripts()

    @QtCore.Slot()
    def _onBuilderBuild(self):
        """ Execute the builder build function """
        self.builder.build()

    @QtCore.Slot()
    def _onBuilderConnect(self):
        """ Execute the builder connect function """
        self.builder.connect()

    @QtCore.Slot()
    def _onBuilderFinalize(self):
        """ Execute the builder finalize function """
        self.builder.finalize()

    @QtCore.Slot()
    def _onLoadPoseReaders(self):
        """ Load pose reader setup from JSON using the builder """
        self.builder.loadPoseReaders(replace=self.loadPsdModeCheckbox.currentIndex())

    @QtCore.Slot()
    def _onSavePoseReaders(self):
        """ Save pose reader setup to JSON using the builder """
        dataIO.savePoseReaders(self.psdDataLoader.getFileList(absolute=True))

    @QtCore.Slot()
    def _onCompleteBuild(self):
        """ Execute a complete rig build (steps initialize - finalize) """
        self.builder.initialize()
        self.builder.build()
        self.builder.connect()
        self.builder.finalize()

    @QtCore.Slot()
    def _setPoseReadersFiles(self, fileList):
        if self.builder:
            self.builder.poseReadersFiles = fileList
            self.postRigFileModifiedEvent()

    @QtCore.Slot()
    def _setLocalPostScripts(self, scriptData):
        if not self.builder:
            return

        localPostScripts = list()
        for key, scriptItemData in scriptData.items():
            if scriptItemData.get(scriptRunner.CUSTOM_DATA_KEY) == 0:
                filePath = scriptItemData.get(scriptRunner.FILEPATH_DATA_KEY)
                localPostScripts.append(filePath)

        self.builder.localPostScripts = localPostScripts
        self.postRigFileModifiedEvent()

