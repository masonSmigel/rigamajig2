#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: builder_widget.py
    author: masonsmigel
    date: 07/2022
    description:
"""
# PYTHON
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui.widgets import dataLoader, collapseableWidget, scriptRunner
from rigamajig2.maya.builder.constants import PSD, POST_SCRIPT
from rigamajig2.ui.builder_ui import style
from rigamajig2.maya.builder import core


class BuildWidget(QtWidgets.QWidget):
    """ Build layout for the builder UI """

    def __init__(self, builder=None):
        super(BuildWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets """
        self.mainCollapseableWidget = collapseableWidget.CollapsibleWidget(text='Build Rig', addCheckbox=True)

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
        self.loadPsdButton.setIcon(QtGui.QIcon(common.getIcon("loadPsd.png")))
        self.savePsdButton = QtWidgets.QPushButton("Save Pose Readers")
        self.savePsdButton.setIcon(QtGui.QIcon(common.getIcon("loadPsd.png")))

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
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        buildLayout = QtWidgets.QHBoxLayout()
        buildLayout.addWidget(self.buildButton)
        buildLayout.addWidget(self.connectButton)
        buildLayout.addWidget(self.finalizeButton)

        self.mainCollapseableWidget.addWidget(self.completeButton)
        self.mainCollapseableWidget.addLayout(buildLayout)

        psdButtonLayout = QtWidgets.QHBoxLayout()
        psdButtonLayout.setContentsMargins(0, 0, 0, 0)
        psdButtonLayout.setSpacing(4)
        psdButtonLayout.addWidget(self.loadPsdButton)
        psdButtonLayout.addWidget(self.savePsdButton)
        psdButtonLayout.addWidget(self.loadPsdModeCheckbox)

        self.mainCollapseableWidget.addSpacing(10)
        self.mainCollapseableWidget.addWidget(self.psdDataLoader)
        self.mainCollapseableWidget.addLayout(psdButtonLayout)

        self.mainCollapseableWidget.addSpacing()
        self.mainCollapseableWidget.addWidget(self.postScriptRunner)

        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections """
        self.completeButton.clicked.connect(self.completeBuild)
        self.buildButton.clicked.connect(self.doBuilderBuild)
        self.connectButton.clicked.connect(self.doBuilderConnect)
        self.finalizeButton.clicked.connect(self.doBuilderFinalize)
        self.loadPsdButton.clicked.connect(self.loadPoseReaders)
        self.savePsdButton.clicked.connect(self.savePoseReaders)

    def setBuilder(self, builder):
        """ Set the builder """
        rigEnv = builder.getRigEnviornment()
        self.builder = builder
        self.psdDataLoader.clear()
        self.psdDataLoader.setRelativePath(rigEnv)

        self.postScriptRunner.clearScript()
        scripts = core.GetCompleteScriptList.getScriptList(self.builder.rigFile, POST_SCRIPT, asDict=True)
        self.postScriptRunner.addScriptsWithRecursionData(scripts)

        psdFiles = self.builder.getRigData(self.builder.getRigFile(), PSD)
        self.psdDataLoader.selectPaths(psdFiles)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner """
        self.completeBuild()
        self.loadPoseReaders()
        self.postScriptRunner.executeAllScripts()

    @property
    def isChecked(self):
        """ Return the checked state of the collapsible widget """
        return self.mainCollapseableWidget.isChecked()

    @QtCore.Slot()
    def doBuilderBuild(self):
        """ Execute the builder build function """
        self.builder.build()

    @QtCore.Slot()
    def doBuilderConnect(self):
        """ Execute the builder connect function """
        self.builder.connect()

    @QtCore.Slot()
    def doBuilderFinalize(self):
        """ Execute the builder finalize function """
        self.builder.finalize()

    @QtCore.Slot()
    def loadPoseReaders(self):
        """ Load pose reader setup from JSON using the builder """
        self.builder.loadPoseReaders(self.psdDataLoader.getFileList(), replace=self.loadPsdModeCheckbox.currentIndex())

    @QtCore.Slot()
    def savePoseReaders(self):
        """ Save pose reader setup to JSON using the builder """
        self.builder.savePoseReaders(self.psdDataLoader.getFileList(absolute=True))

    @QtCore.Slot()
    def completeBuild(self):
        """ Execute a complete rig build (steps initialize - finalize) """
        self.builder.initalize()
        self.builder.loadComponentSettings()
        self.builder.build()
        self.builder.connect()
        self.builder.finalize()
