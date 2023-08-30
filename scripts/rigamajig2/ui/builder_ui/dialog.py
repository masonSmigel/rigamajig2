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
import time
import logging

# MAYA
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG
import rigamajig2
from rigamajig2.maya.builder import builder
from rigamajig2.maya.builder import constants
from rigamajig2.ui.widgets.workspace_control import DockableUI
from rigamajig2.ui.widgets import statusLine, QLine
from rigamajig2.ui.builder_ui.widgets import pathSelector
from rigamajig2.ui.builder_ui import recent_files

# Import the main widgets for the builder dialog
from rigamajig2.ui.builder_ui import widget_model
from rigamajig2.ui.builder_ui import widget_joints
from rigamajig2.ui.builder_ui import widget_controls
from rigamajig2.ui.builder_ui import widget_deformation
from rigamajig2.ui.builder_ui import widget_initialize
from rigamajig2.ui.builder_ui import widget_build
from rigamajig2.ui.builder_ui import widget_publish
from rigamajig2.ui.builder_ui import actions

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
        # utilsMenu.addAction(self.actions.devModeAction)
        utilsMenu.addSeparator()
        utilsMenu.addAction(self.actions.removeRigamajigCallbacksAction)
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

        self.modelWidget = widget_model.ModelWidget(self.rigBuilder)
        self.jointWidget = widget_joints.JointWidget(self.rigBuilder)
        self.controlsWidget = widget_controls.ControlsWidget(self.rigBuilder)
        self.intalizeWidget = widget_initialize.InitializeWidget(self.rigBuilder)
        self.buildWidget = widget_build.BuildWidget(self.rigBuilder)
        self.deformationWidget = widget_deformation.DeformationWidget(self.rigBuilder)
        self.publishWidget = widget_publish.PublishWidget(self.rigBuilder)

        self.mainWidgets = [self.modelWidget,
                            self.jointWidget,
                            self.intalizeWidget,
                            self.buildWidget,
                            self.controlsWidget,
                            self.deformationWidget,
                            self.publishWidget]

        self.runSelectedButton = QtWidgets.QPushButton(QtGui.QIcon(":execute.png"), "Run Selected")
        self.runSelectedButton.setToolTip("Run Rig steps up to the break point")
        self.runSelectedButton.setFixedSize(120, 22)

        self.runButton = QtWidgets.QPushButton(QtGui.QIcon(":executeAll.png"), "Run")
        self.runButton.setToolTip("Run all build steps.")
        self.runButton.setFixedSize(80, 22)

        self.publishButton = QtWidgets.QPushButton(QtGui.QIcon(":sourceScript.png"), "Publish")
        self.publishButton.setToolTip("Publish the rig. This will build the rig and save it.")
        self.publishButton.setFixedSize(80, 22)

        self.openScriptEditorButton = QtWidgets.QPushButton()
        self.openScriptEditorButton.setFixedSize(18, 18)
        self.openScriptEditorButton.setFlat(True)
        self.openScriptEditorButton.setIcon(QtGui.QIcon(":cmdWndIcon.png"))

        self.statusLine = statusLine.StatusLine()
        self.statusLine.setStatusMessage(f"Rigamajig2 version {rigamajig2.version}", "info")

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

        lowButtonsLayout.addWidget(QLine.QLine())
        lowButtonsLayout.addLayout(runButtonLayout)
        lowButtonsLayout.addWidget(self.statusLine)

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
        self.rigName = self.rigBuilder.getRigData(self.rigFile, constants.RIG_NAME)
        self.assetNameLineEdit.setText(self.rigName)

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

        if not confirmBuildRig():
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

        # add the confirm dialog
        if not confirmBuildRig():
            return

        # for the rig build we can put the publish into a try except block
        # if the publish fails we can add a message to the status line before raising the exception
        try:
            finalTime = self.rigBuilder.run()
            self.intalizeWidget.componentManager.loadFromScene()
            self.statusLine.setStatusMessage(
                message=f"Rig Build Sucessful: '{self.rigName}' -- Completed in {round(finalTime, 3)}", icon="success")
        except Exception as e:
            self.statusLine.setStatusMessage(message=f"Rig Build Failed: '{self.rigName}'", icon="failed")
            raise e

    def publish(self):
        """ Run builder and update the component manager"""
        self.initializeDevMode()
        # for the rig build we can put the publish into a try except block
        # if the publish fails we can add a message to the status line before raising the exception
        try:
            finalTime = self.publishWidget.publish()
            if finalTime:
                self.intalizeWidget.componentManager.loadFromScene()
                self.statusLine.setStatusMessage(
                    message=f"Rig Publish Sucessful: '{self.rigName}' -- Completed in {round(finalTime, 3)}",
                    icon="success")
        except Exception as e:
            self.statusLine.setStatusMessage(message=f"Rig Publish Failed: '{self.rigName}'", icon="failed")
            raise e

    def initializeDevMode(self):
        if self.actions.devModeAction.isChecked():
            logger.setLevel(logging.DEBUG)
            rigamajig2.reloadModule(log=True)

            # reload the rig file. This should refresh the builder
            self.setRigFile(self.rigFile)

            logger.info('rigamajig2 modules reloaded')

    def hideEvent(self, e):
        """override the hide event to delete the scripts jobs from the initialize widget"""
        # this is a bit of a pain instead of using the close event but since we're using
        # the workspace control the closeEvent is now owned by Maya. This is a nice work around to
        # ensure the script jobs are deleted when the main window is hidden (done my closing the 'X' button)
        # however when in development you should manually call the close() method BEFORE deleting the workspace control.
        super(BuilderDialog, self).hideEvent(e)
        self.intalizeWidget.componentManager.setScriptJobEnabled(False)


def confirmBuildRig():
    """
    This is to check if the scene is safe for a rig rebuild.
    Check if the scene has unsaved changes. If it does give the user a prompt to see if its safe to clear the scene.

    :return: Returns True or False depending on the scene state and user input
    """

    modified = cmds.file(q=True, anyModified=True)
    if modified:
        confirmPublishMessage = QtWidgets.QMessageBox()
        confirmPublishMessage.setText("Run Rig Build")

        confirmPublishMessage.setInformativeText(
            "Proceeding will rebuild the rig based on data you've saved. Unsaved in-scene changes will be lost!"
            )
        confirmPublishMessage.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
            )

        helpPixmap = QtGui.QIcon(":helpModal.png").pixmap(QtCore.QSize(64, 64))
        confirmPublishMessage.setIconPixmap(helpPixmap)

        confirmPublishMessage.setDefaultButton(QtWidgets.QMessageBox.Yes)
        res = confirmPublishMessage.exec_()

        if res == QtWidgets.QMessageBox.Yes:
            return True
        else:
            return False

    return True



if __name__ == '__main__':
    workspace_control_name = BuilderDialog.get_workspace_control_name()
    if cmds.window(workspace_control_name, exists=True):
        test_dialog.close()
        cmds.deleteUI(workspace_control_name)

    BuilderDialog.module_name_override = "dialog"
    test_dialog = BuilderDialog()
