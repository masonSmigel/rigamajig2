#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: builder_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
from rigamajig2.shared import common
from rigamajig2.ui.widgets import dataLoader, collapseableWidget, scriptRunner
from rigamajig2.maya.builder.constants import PSD, POST_SCRIPT
from rigamajig2.ui.builder_ui import constants
from rigamajig2.ui.builder_ui import controls_widget
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
        """ Create Widgets"""
        self.mainCollapseableWidget = collapseableWidget.CollapsibleWidget('Build Rig', addCheckbox=True)

        self.completeButton = QtWidgets.QPushButton("Build Rig")
        self.completeButton.setFixedHeight(45)

        self.buildButton = QtWidgets.QPushButton("Build")
        self.connectButton = QtWidgets.QPushButton("Connect")
        self.finalizeButton = QtWidgets.QPushButton("Finalize")

        self.psdDataLoader = dataLoader.DataLoader(
            "psd:",
            caption="Select a Pose Reader File",
            fileFilter=constants.JSON_FILTER,
            fileMode=1,
            dataFilteringEnabled=True,
            dataFilter=["PSDData"])

        self.loadPsdButton = QtWidgets.QPushButton("Load Pose Readers")
        self.loadPsdButton.setIcon(QtGui.QIcon(common.getIcon("loadPsd.png")))
        self.savePsdButton = QtWidgets.QPushButton("Save Pose Readers")
        self.savePsdButton.setIcon(QtGui.QIcon(common.getIcon("loadPsd.png")))

        self.loadPsdButton.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.savePsdButton.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.loadPsdButton.setIconSize(constants.LARGE_BTN_ICON_SIZE)
        self.savePsdButton.setIconSize(constants.LARGE_BTN_ICON_SIZE)

        self.loadPsdModeCheckbox = QtWidgets.QComboBox()
        self.loadPsdModeCheckbox.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.loadPsdModeCheckbox.addItem("append")
        self.loadPsdModeCheckbox.addItem("replace")

        # Post - script section
        self.postScriptRunner = scriptRunner.ScriptRunner(title="Post-Scripts:")

    def createLayouts(self):
        """ Create Layouts"""
        # setup the main layout.
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        buildLayout = QtWidgets.QHBoxLayout()
        buildLayout.addWidget(self.buildButton)
        buildLayout.addWidget(self.connectButton)
        buildLayout.addWidget(self.finalizeButton)

        # build_layout.addWidget(self.load_ctls_on_build)
        self.mainCollapseableWidget.addWidget(self.completeButton)
        self.mainCollapseableWidget.addLayout(buildLayout)

        # psd buttons
        psdButtonLayout = QtWidgets.QHBoxLayout()
        psdButtonLayout.setContentsMargins(0, 0, 0, 0)
        psdButtonLayout.setSpacing(4)
        psdButtonLayout.addWidget(self.loadPsdButton)
        psdButtonLayout.addWidget(self.savePsdButton)
        psdButtonLayout.addWidget(self.loadPsdModeCheckbox)

        # add widgets to the collapsable widget.
        self.mainCollapseableWidget.addSpacing(10)
        self.mainCollapseableWidget.addWidget(self.psdDataLoader)
        self.mainCollapseableWidget.addLayout(psdButtonLayout)

        # Post Script
        self.mainCollapseableWidget.addSpacing()
        self.mainCollapseableWidget.addWidget(self.postScriptRunner)

        # add the widget to the main layout
        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections """
        self.completeButton.clicked.connect(self.completeBuild)
        self.buildButton.clicked.connect(self.executeBuilderBuild)
        self.connectButton.clicked.connect(self.executeBuilderConnect)
        self.finalizeButton.clicked.connect(self.executeBuilderFinalize)
        self.loadPsdButton.clicked.connect(self.loadPoseReaders)
        self.savePsdButton.clicked.connect(self.savePoseReaders)

    def setBuilder(self, builder):
        """ Set the builder"""
        rigEnv = builder.getRigEnviornment()
        rigFile = builder.getRigFile()
        self.builder = builder
        self.psdDataLoader.clear()
        self.psdDataLoader.setRelativePath(rigEnv)

        # clear the ui
        self.postScriptRunner.clearScript()

        # setup the PSD path reader
        psdFiles = self.builder.getRigData(self.builder.getRigFile(), PSD)
        self.psdDataLoader.selectPaths(psdFiles)

        # self.postScriptScriptRunner.setRelativeDirectory(rigEnv)
        scripts = core.GetCompleteScriptList.getScriptList(self.builder.rigFile, POST_SCRIPT, asDict=True)
        self.postScriptRunner.addScriptsWithRecursionData(scripts)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.completeBuild()
        self.loadPoseReaders()
        self.postScriptRunner.executeAllScripts()

    @property
    def isChecked(self):
        """ return the checked state of the collapseable widget"""
        return self.mainCollapseableWidget.isChecked()

    def executeBuilderBuild(self):
        """ execute the builder build function """
        self.builder.build()

    def executeBuilderConnect(self):
        """ execute the builder connect function """
        self.builder.connect()

    def executeBuilderFinalize(self):
        """ execute the builder finalize function """
        self.builder.finalize()

    def loadPoseReaders(self):
        """ Save load pose reader setup from json using the builder """
        self.builder.loadPoseReaders(self.psdDataLoader.getFileList(), replace=self.loadPsdModeCheckbox.currentIndex())

    def savePoseReaders(self):
        """ Save pose reader setup to json using the builder """
        self.builder.savePoseReaders(self.psdDataLoader.getPath())

    def completeBuild(self):
        """ Execute a complete rig build (steps intialize - finalize)"""
        self.builder.initalize()
        self.builder.loadComponentSettings()
        self.builder.build()
        self.builder.connect()
        self.builder.finalize()
        # self.cmpt_manager.loadFromScene()
