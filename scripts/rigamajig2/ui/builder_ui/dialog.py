#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: dialog.py
    author: masonsmigel
    date: 07/2022
    discription: This module contains the main dialog for the builder UI

"""
# PYTHON
import sys
import time
import logging
import os
from collections import OrderedDict

# MAYA
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

# RIGAMAJIG
import rigamajig2
from rigamajig2.maya.builder import builder
from rigamajig2.maya.builder import constants
from rigamajig2.shared import common
from rigamajig2.ui.widgets.workspace_control import DockableUI
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
from rigamajig2.ui.builder_ui import recent_files

# Import the main widgets for the builder dialog
from rigamajig2.ui.builder_ui import model_widget
from rigamajig2.ui.builder_ui import joint_widget
from rigamajig2.ui.builder_ui import controls_widget
from rigamajig2.ui.builder_ui import deformation_widget
from rigamajig2.ui.builder_ui import initalize_widget
from rigamajig2.ui.builder_ui import build_widget
from rigamajig2.ui.builder_ui import publish_widget
from rigamajig2.ui.builder_ui import actions

import rigamajig2.maya.data.abstract_data as abstract_data
from rigamajig2.maya.builder import deform

logger = logging.getLogger(__name__)
logger.setLevel(5)

MAYA_FILTER = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
JSON_FILTER = "Json Files (*.json)"

LARGE_BTN_HEIGHT = 35
EDIT_BG_WIDGET_COLOR = QtGui.QColor(70, 70, 80)


# this is a long function allow more instance attributes for the widgets.
# pylint: disable = too-many-instance-attributes
class BuilderDialog(DockableUI):
    """ Builder dialog"""
    WINDOW_TITLE = "Rigamajig2 Builder  {}".format(rigamajig2.version)

    def __init__(self, rigFile=None):
        """ Constructor for the builder dialog"""
        super(BuilderDialog, self).__init__()

        # Store a rig enviornment and rig builder variables.
        self.rigEnviornment = None
        self.rigBuilder = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.setMinimumSize(420, 600)

        # with the maya mixin stuff the window comes in at a weird size. This ensures its not a weird size.
        self.resize(420, 800)

        self.createMenus()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

        # if we dont provide a rig file load the most recent one from the recent files list
        recentFile = recent_files.getMostRecentFile()
        if recentFile:
            self.setRigFile(recentFile)

    def createMenus(self):
        """create menu actions"""
        self.mainMenu = QtWidgets.QMenuBar()

        fileMenu = self.mainMenu.addMenu("File")
        self.actions = actions.Actions(self)
        fileMenu.addAction(self.actions.newRigFileAction)
        fileMenu.addAction(self.actions.loadRigFileAction)
        fileMenu.addAction(self.actions.saveRigFileAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.actions.reloadRigFileAction)
        fileMenu.addSeparator()
        fileMenu.addMenu(self.actions.recentRigFileMenu)

        utilsMenu = self.mainMenu.addMenu("Utils")
        utilsMenu.addAction(self.actions.mergeRigFilesAction)
        utilsMenu.addSeparator()
        utilsMenu.addMenu(self.actions.setLoggingLevelMenu)
        utilsMenu.addAction(self.actions.devModeAction)
        utilsMenu.addAction(self.actions.reloadRigamajigModulesAction)

        qcMenu = self.mainMenu.addMenu("QC")
        qcMenu.addAction(self.actions.runPerformanceTestAction)
        qcMenu.addAction(self.actions.generateRandomAnimationAction)
        qcMenu.addSeparator()
        qcMenu.addAction(self.actions.openProfilerAction)
        qcMenu.addAction(self.actions.openEvaluationToolkitAction)

        helpmenu = self.mainMenu.addMenu("Help")
        helpmenu.addAction(self.actions.showDocumentationAction)
        helpmenu.addAction(self.actions.showAboutAction)

    def createWidgets(self):
        """ Create Widgets"""
        self.rigPathSelector = pathSelector.PathSelector(caption='Select a Rig File', fileFilter="Rig Files (*.rig)",
                                                         fileMode=1)

        self.assetNameLineEdit = QtWidgets.QLineEdit()
        self.assetNameLineEdit.setPlaceholderText("asset_name")

        self.archetypeBaseLabel = QtWidgets.QLabel("None")

        self.mainWidgets = list()

        self.modelWidget = model_widget.ModelWidget(self.rigBuilder)
        self.jointWidget = joint_widget.JointWidget(self.rigBuilder)
        self.controlsWidget = controls_widget.ControlsWidget(self.rigBuilder)
        self.intalizeWidget = initalize_widget.InitializeWidget(self.rigBuilder)
        self.buildWidget = build_widget.BuildWidget(self.rigBuilder)
        self.deformationWidget = deformation_widget.DeformationWidget(self.rigBuilder)
        self.publishWidget = publish_widget.PublishWidget(self.rigBuilder)

        self.mainWidgets = [self.modelWidget,
                            self.jointWidget,
                            self.intalizeWidget,
                            self.buildWidget,
                            self.controlsWidget,
                            self.deformationWidget,
                            self.publishWidget]

        self.runSelectedButton = QtWidgets.QPushButton(QtGui.QIcon(":execute.png"), "Run Selected")
        self.runSelectedButton.setFixedSize(120, 22)
        self.runButton = QtWidgets.QPushButton(QtGui.QIcon(":executeAll.png"), "Run")
        self.runButton.setFixedSize(80, 22)
        self.publishButton = QtWidgets.QPushButton(QtGui.QIcon(":newPreset.png"), "Publish")
        self.publishButton.setFixedSize(80, 22)

        self.openScriptEditorButton = QtWidgets.QPushButton()
        self.openScriptEditorButton.setFixedSize(18, 18)
        self.openScriptEditorButton.setFlat(True)
        self.openScriptEditorButton.setIcon(QtGui.QIcon(":cmdWndIcon.png"))

        self.rigamajigVersionLabel = QtWidgets.QLabel(f"Rigamajig2 version {rigamajig2.version}")

        versionFont = QtGui.QFont()
        versionFont.setPointSize(10)

        self.rigamajigVersionLabel.setFont(versionFont)

    def createLayouts(self):
        """ Create Layouts"""
        rigNameLayout = QtWidgets.QHBoxLayout()
        rigNameLayout.addWidget(QtWidgets.QLabel("Rig Name:"))
        rigNameLayout.addWidget(self.assetNameLineEdit)

        rigNameLayout.addSpacing(10)
        rigNameLayout.addWidget(QtWidgets.QLabel("rig archetype:"))
        rigNameLayout.addWidget(self.archetypeBaseLabel)

        rigEnviornmentLayout = QtWidgets.QVBoxLayout()
        rigEnviornmentLayout.addWidget(self.rigPathSelector)
        rigEnviornmentLayout.addLayout(rigNameLayout)

        # add the collapseable widgets
        buildLayout = QtWidgets.QVBoxLayout()
        buildLayout.addWidget(self.modelWidget)
        buildLayout.addWidget(self.jointWidget)
        buildLayout.addWidget(self.intalizeWidget)
        buildLayout.addWidget(self.buildWidget)
        buildLayout.addWidget(self.controlsWidget)
        buildLayout.addWidget(self.deformationWidget)
        buildLayout.addWidget(self.publishWidget)
        buildLayout.addStretch()

        # groups
        rigEnvornmentGroup = QtWidgets.QGroupBox('Rig Enviornment')
        rigEnvornmentGroup.setLayout(rigEnviornmentLayout)

        buildGroup = QtWidgets.QGroupBox('Build')
        buildGroup.setLayout(buildLayout)

        # lower persistant buttons (AKA close)
        lowButtonsLayout = QtWidgets.QVBoxLayout()
        lowButtonsLayout.setContentsMargins(0, 0, 0, 0)
        runButtonLayout = QtWidgets.QHBoxLayout()
        runButtonLayout.addWidget(self.publishButton)
        runButtonLayout.addWidget(self.runButton)
        runButtonLayout.addStretch()
        runButtonLayout.addWidget(self.runSelectedButton)

        statusLineLayout = QtWidgets.QHBoxLayout()
        statusLineLayout.addWidget(self.rigamajigVersionLabel)
        statusLineLayout.addStretch()
        statusLineLayout.addWidget(self.openScriptEditorButton)

        lowButtonsLayout.addLayout(runButtonLayout)
        lowButtonsLayout.addLayout(statusLineLayout)

        # scrollable area
        bodyWidget = QtWidgets.QWidget()
        bodyLayout = QtWidgets.QVBoxLayout(bodyWidget)
        bodyLayout.setContentsMargins(0, 0, 0, 0)
        bodyLayout.addWidget(rigEnvornmentGroup)
        bodyLayout.addWidget(buildGroup)

        bodyScrollArea = QtWidgets.QScrollArea()
        bodyScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        bodyScrollArea.setWidgetResizable(True)
        bodyScrollArea.setWidget(bodyWidget)

        # main layout
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(4, 4, 4, 4)
        mainLayout.setSpacing(4)
        mainLayout.setMenuBar(self.mainMenu)
        mainLayout.addWidget(bodyScrollArea)
        mainLayout.addLayout(lowButtonsLayout)

    def createConnections(self):
        """ Create Connections"""

        # setup each widget with a connection to uncheck all over widgets when one is checked.
        # This ensures all setups until a breakpoint are run
        self.modelWidget.mainCollapseableWidget.headerWidget.checkbox.clicked.connect(
            lambda x: self.updateWidgetChecks(self.modelWidget))
        self.jointWidget.mainCollapseableWidget.headerWidget.checkbox.clicked.connect(
            lambda x: self.updateWidgetChecks(self.jointWidget))
        self.intalizeWidget.mainCollapseableWidget.headerWidget.checkbox.clicked.connect(
            lambda x: self.updateWidgetChecks(self.intalizeWidget))
        self.buildWidget.mainCollapseableWidget.headerWidget.checkbox.clicked.connect(
            lambda x: self.updateWidgetChecks(self.buildWidget))
        self.controlsWidget.mainCollapseableWidget.headerWidget.checkbox.clicked.connect(
            lambda x: self.updateWidgetChecks(self.controlsWidget))
        self.deformationWidget.mainCollapseableWidget.headerWidget.checkbox.clicked.connect(
            lambda x: self.updateWidgetChecks(self.deformationWidget))
        self.publishWidget.mainCollapseableWidget.headerWidget.checkbox.clicked.connect(
            lambda x: self.updateWidgetChecks(self.publishWidget))

        self.rigPathSelector.selectPathButton.clicked.connect(self.pathSelectorLoadRigFile)
        self.runSelectedButton.clicked.connect(self.runSelected)
        self.runButton.clicked.connect(self.runAll)
        self.publishButton.clicked.connect(self.publish)
        self.openScriptEditorButton.clicked.connect(self.openScriptEditor)

    # --------------------------------------------------------------------------------
    # Connections
    # --------------------------------------------------------------------------------

    def pathSelectorLoadRigFile(self):
        """ Load a rig file from the path selector """
        newPath = self.rigPathSelector.getPath()
        if newPath:
            self.actions.loadRecentRigFile(newPath)

    def setRigFile(self, path=None):
        """
        Set the rig file to the given path
        :param path: rig file to set
        """
        self.rigPathSelector.selectPath(path=path)
        fileInfo = QtCore.QFileInfo(self.rigPathSelector.getPath())
        self.rigEnviornment = fileInfo.path()
        self.rigFile = fileInfo.filePath()

        self.rigBuilder = builder.Builder(self.rigFile)

        if not self.rigFile:
            return

        # setup ui Data
        self.assetNameLineEdit.setText(self.rigBuilder.getRigData(self.rigFile, constants.RIG_NAME))

        # set the text of the archetype to the archetype. We need to check if its a string and update the formatting
        archetype = self.rigBuilder.getRigData(self.rigFile, constants.BASE_ARCHETYPE)
        if isinstance(archetype, (list, tuple)):
            archetype = ", ".join(archetype)
        self.archetypeBaseLabel.setText(str(archetype))

        # set paths and widgets relative to the rig env
        for widget in self.mainWidgets:
            widget.setBuilder(builder=self.rigBuilder)

    # BULDER FUNCTIONS
    def updateWidgetChecks(self, selectedWidget):
        """ This function ensures only one build step is selected at a time. it is run whenever a checkbox is toggled."""
        for widget in self.mainWidgets:
            if widget is not selectedWidget:
                widget.mainCollapseableWidget.setChecked(False)

    def runSelected(self):
        """run selected steps"""

        # ensure at least one breakpoint is selected
        breakpointSelected = False
        for widget in self.mainWidgets:
            if widget.mainCollapseableWidget.isChecked():
                breakpointSelected = True

        if not breakpointSelected:
            logger.error("No breakpoint selected no steps to run")
            return

        self.initializeDevMode()

        startTime = time.time()

        # because widgets are added to the ui and the list in oder they can be run sequenctially.
        # when we hit a widget that is checked then the loop stops.
        for widget in self.mainWidgets:
            widget.runWidget()

            if widget.isChecked:
                break

        runTime = time.time() - startTime
        print("Time Elapsed: {}".format(str(runTime)))

    def runAll(self):
        """ Run builder and update the component manager"""
        self.initializeDevMode()
        self.rigBuilder.run()
        self.intalizeWidget.componentManager.loadFromScene()

    def publish(self):
        """ Run builder and update the component manager"""
        self.initializeDevMode()
        self.publishWidget.publish()

    def initializeDevMode(self):
        if self.actions.devModeAction.isChecked():
            logger.setLevel(logging.DEBUG)
            rigamajig2.reloadModule(log=True)

            # reload the rig file. This should refresh the builder
            self.setRigFile(self.rigFile)

            logger.info('rigamajig2 modules reloaded')

    def openScriptEditor(self):
        """Open the script Editor"""

        if cmds.pluginInfo("CharcoalEditor2", q=True, loaded=True):
            mel.eval("charcoalEditor2;")
        else:
            mel.eval("ScriptEditor;")

    def hideEvent(self, e):
        """override the hide event to delete the scripts jobs from the initialize widget"""
        # this is a bit of a pain instead of using the close event but since we're using
        # the workspace control the closeEvent is now owned by Maya. This is a nice work around to
        # ensure the script jobs are deleted when the main window is hidden (done my closing the 'X' button)
        # however when in development you should manually call the close() method BEFORE deleting the workspace control.
        super(BuilderDialog, self).hideEvent(e)
        self.intalizeWidget.componentManager.setScriptJobEnabled(False)


if __name__ == '__main__':
    workspace_control_name = BuilderDialog.get_workspace_control_name()
    if cmds.window(workspace_control_name, exists=True):
        test_dialog.close()
        cmds.deleteUI(workspace_control_name)

    BuilderDialog.module_name_override = "dialog"
    test_dialog = BuilderDialog()
