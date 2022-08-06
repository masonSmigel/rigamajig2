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
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
from rigamajig2.ui.builder_ui import constants
from rigamajig2.maya.builder.builder import POST_SCRIPT
from rigamajig2.ui.builder_ui import controls_widget


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
        self.mainCollapseableWidget  = collapseableWidget.CollapsibleWidget('Build Rig', addCheckbox=True)

        self.completeButton = QtWidgets.QPushButton("Build Rig")
        self.completeButton.setFixedHeight(45)

        self.buildButton = QtWidgets.QPushButton("Build")
        self.connectButton = QtWidgets.QPushButton("Connect")
        self.finalizeButton = QtWidgets.QPushButton("Finalize")

        # Post - script section
        self.postScriptScriptRunner = scriptRunner.ScriptRunner(title="Post-Scripts:")

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
        self.mainCollapseableWidget .addWidget(self.completeButton)
        self.mainCollapseableWidget .addLayout(buildLayout)

        # Post Script
        self.mainCollapseableWidget .addSpacing()
        self.mainCollapseableWidget .addWidget(self.postScriptScriptRunner)

        # add the widget to the main layout
        self.mainLayout.addWidget(self.mainCollapseableWidget )

    def createConnections(self):
        """ Create Connections """
        self.completeButton.clicked.connect(self.completeBuild)
        self.buildButton.clicked.connect(self.executeBuilderBuild)
        self.connectButton.clicked.connect(self.executeBuilderConnect)
        self.finalizeButton.clicked.connect(self.executeBuilderFinalize)

    def setBuilder(self, builder):
        """ Set the builder"""
        rigEnv = builder.getRigEnviornment()
        rigFile = builder.getRigFile()
        self.builder = builder

        # clear the ui
        self.postScriptScriptRunner.clearScript()

        self.postScriptScriptRunner.setRelativeDirectory(rigEnv)
        for path in self.builder.getRigData(rigFile, POST_SCRIPT):
            self.postScriptScriptRunner.addScripts(self.builder.getAbsoultePath(path))

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.completeBuild()
        self.postScriptScriptRunner.executeAllScripts()

    @property
    def isChecked(self):
        """ return the checked state of the collapseable widget"""
        return self.mainCollapseableWidget .isChecked()

    def executeBuilderBuild(self):
        """ execute the builder build function """
        self.builder.build()

    def executeBuilderConnect(self):
        """ execute the builder connect function """
        self.builder.connect()

    def executeBuilderFinalize(self):
        """ execute the builder finalize function """
        self.builder.finalize()

    def completeBuild(self):
        """ Execute a complete rig build (steps intialize - finalize)"""
        self.builder.initalize()
        self.builder.loadComponentSettings()
        self.builder.build()
        self.builder.connect()
        self.builder.finalize()
        # self.cmpt_manager.loadFromScene()
