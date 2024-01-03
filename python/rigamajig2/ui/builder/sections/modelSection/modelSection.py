#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: model_section.py
    author: masonsmigel
    date: 07/2022
    description:
"""
from PySide2 import QtCore
from PySide2 import QtWidgets

import rigamajig2.maya.file as file
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import scriptManager
from rigamajig2.shared import common
from rigamajig2.ui.builder import style as ui_constants
from rigamajig2.ui.builder.customs import section, scriptRunner
from rigamajig2.ui.resources import Resources
from rigamajig2.ui.widgets import pathSelector


# MAYA


class ModelSection(section.BuilderSection):
    """Model layout for the builder UI"""

    WIDGET_TITLE = "Model/ Setup Scene"

    def createWidgets(self):
        """Create Widgets"""
        self.modelPathSelector = pathSelector.PathSelector(
            label="model:", caption="Select a Model file", fileFilter=common.MAYA_FILTER, fileMode=1
        )
        self.importModelButton = QtWidgets.QPushButton("Import Model")
        self.importModelButton.setIcon(Resources.getIcon(":importModel.png"))
        self.openModelButton = QtWidgets.QPushButton("Open Model")
        self.openModelButton.setIcon(Resources.getIcon(":openModel.png"))
        self.openModelButton.setFixedWidth(100)

        for button in [self.importModelButton, self.openModelButton]:
            button.setFixedHeight(ui_constants.LARGE_BTN_HEIGHT)
            button.setIconSize(ui_constants.LARGE_BTN_ICON_SIZE)

        self.preScriptRunner = scriptRunner.ScriptRunner(title="Pre-Scripts:")

    def createLayouts(self):
        """Create Layouts"""
        self.mainWidget.addWidget(self.preScriptRunner)

        # setup the button layout
        modelButtonLayout = QtWidgets.QHBoxLayout()
        modelButtonLayout.setContentsMargins(0, 0, 0, 0)
        modelButtonLayout.setSpacing(4)
        modelButtonLayout.addWidget(self.importModelButton)
        modelButtonLayout.addWidget(self.openModelButton)

        # add widgets to the collapsable widget.
        self.mainWidget.addSpacing(10)
        self.mainWidget.addWidget(self.modelPathSelector)
        self.mainWidget.addLayout(modelButtonLayout)

    def createConnections(self):
        """Create Connections"""
        self.preScriptRunner.scriptsUpdated.connect(self._setLocalPreScripts)
        self.modelPathSelector.pathUpdated.connect(self._setModelFile)
        self.importModelButton.clicked.connect(self._onImportModel)
        self.openModelButton.clicked.connect(self._onOpenModel)

    def _setBuilder(self, builder):
        """Set a builder for the model widget"""
        super()._setBuilder(builder)

        # clear the ui
        self.preScriptRunner.clearScript()
        self.modelPathSelector.setRelativePath(self.builder.getRigEnvironment())

        # update data within the rig
        modelFile = self.builder.getRigData(self.builder.getRigFile(), constants.MODEL_FILE)
        self.modelPathSelector.selectPath(modelFile)

        # update the script runner
        scripts = scriptManager.GetCompleteScriptList.getScriptList(self.builder.getRigFile(), constants.PRE_SCRIPT)
        self.preScriptRunner.addScriptsWithRecursionData(scripts)

    @QtCore.Slot()
    def _runWidget(self):
        """Run this widget from the builder breakpoint runner"""
        self.preScriptRunner.executeAllScripts()
        self._onImportModel()

    @QtCore.Slot()
    def _onImportModel(self):
        """Import model from builder"""
        self.builder.importModel()

    @QtCore.Slot()
    def _onOpenModel(self):
        """Open the model file"""
        file.open_(self.modelPathSelector.getPath(), f=True)

    @QtCore.Slot()
    def _setModelFile(self, modelFile):
        if self.builder:
            self.builder.modelFile = modelFile
            self.postRigFileModifiedEvent()

    @QtCore.Slot()
    def _setLocalPreScripts(self, scriptData):
        if not self.builder:
            return

        localPreScripts = list()
        for key, scriptItemData in scriptData.items():
            if scriptItemData.get(scriptRunner.CUSTOM_DATA_KEY) == 0:
                filePath = scriptItemData.get(scriptRunner.FILEPATH_DATA_KEY)
                localPreScripts.append(filePath)

        self.builder.localPreScripts = localPreScripts
        self.postRigFileModifiedEvent()
