#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: widget_model.py
    author: masonsmigel
    date: 07/2022
    description:
"""
# PYTHON
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtCore

# MAYA
import maya.cmds as cmds

# RIGAMAJIG2
import rigamajig2.maya.builder.constants
import rigamajig2.shared.common
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui.widgets import pathSelector, collapseableWidget, scriptRunner
from rigamajig2.ui.builder_ui import style as ui_constants
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import core


class ModelWidget(QtWidgets.QWidget):
    """ Model layout for the builder UI """

    def __init__(self, builder=None):
        super(ModelWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets """
        self.mainCollapseableWidget = collapseableWidget.CollapsibleWidget(text='Model/ Setup Scene', addCheckbox=True)
        self.modelPathSelector = pathSelector.PathSelector(
            label="model:",
            caption="Select a Model file",
            fileFilter=rigamajig2.shared.common.MAYA_FILTER,
            fileMode=1
            )
        self.importModelButton = QtWidgets.QPushButton('Import Model')
        self.importModelButton.setIcon(QtGui.QIcon(common.getIcon('importCharacter.png')))
        self.openModelButton = QtWidgets.QPushButton('Open Model')
        self.openModelButton.setIcon(QtGui.QIcon(common.getIcon('openCharacter.png')))
        self.openModelButton.setFixedWidth(100)

        for button in [self.importModelButton, self.openModelButton]:
            button.setFixedHeight(ui_constants.LARGE_BTN_HEIGHT)
            button.setIconSize(ui_constants.LARGE_BTN_ICON_SIZE)

        self.preScriptRunner = scriptRunner.ScriptRunner(title="Pre-Scripts:")

    def createLayouts(self):
        """ Create Layouts """
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.mainCollapseableWidget.addWidget(self.preScriptRunner)

        # setup the button layout
        modelButtonLayout = QtWidgets.QHBoxLayout()
        modelButtonLayout.setContentsMargins(0, 0, 0, 0)
        modelButtonLayout.setSpacing(4)
        modelButtonLayout.addWidget(self.importModelButton)
        modelButtonLayout.addWidget(self.openModelButton)

        # add widgets to the collapsable widget.
        self.mainCollapseableWidget.addSpacing(10)
        self.mainCollapseableWidget.addWidget(self.modelPathSelector)
        self.mainCollapseableWidget.addLayout(modelButtonLayout)

        # add the widget to the main layout
        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections """
        self.importModelButton.clicked.connect(self.importModel)
        self.openModelButton.clicked.connect(self.openModel)

    def setBuilder(self, builder):
        """ Set a builder for the model widget """
        rigEnv = builder.getRigEnviornment()
        self.builder = builder
        self.modelPathSelector.setRelativePath(rigEnv)

        # clear the ui
        self.preScriptRunner.clearScript()

        # update data within the rig
        modelFile = self.builder.getRigData(self.builder.getRigFile(), constants.MODEL_FILE)
        self.modelPathSelector.selectPath(modelFile)

        # update the script runner
        scripts = core.GetCompleteScriptList.getScriptList(self.builder.rigFile, constants.PRE_SCRIPT, asDict=True)
        self.preScriptRunner.addScriptsWithRecursionData(scripts)

    @QtCore.Slot()
    def runWidget(self):
        """ Run this widget from the builder breakpoint runner """
        self.preScriptRunner.executeAllScripts()
        self.builder.importModel(self.modelPathSelector.getPath())

    @property
    def isChecked(self):
        """ Check if the widget is checked """
        return self.mainCollapseableWidget.isChecked()

    @QtCore.Slot()
    def importModel(self):
        """ Import model from builder """
        self.builder.importModel(self.modelPathSelector.getPath())

    @QtCore.Slot()
    def openModel(self):
        """ Open the model file """
        cmds.file(self.modelPathSelector.getPath(), o=True, f=True)