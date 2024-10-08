#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: builder_dialog.py
    author: masonsmigel
    date: 07/2022
    description: This module contains the main dialog for the builder UI

"""
import logging
import time
from functools import partial

import maya.api.OpenMaya as om
# MAYA
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG
import rigamajig2
from rigamajig2.maya.builder import builder
from rigamajig2.maya.builder import constants
from rigamajig2.ui.builder import actions
from rigamajig2.ui.builder import recentFiles
from rigamajig2.ui.builder.sections import (
    modelSection,
    setupSection,
    deformationSection,
    controlsSection,
    skeletonSection,
    buildSection,
    publishSection,
)
from rigamajig2.ui.resources import Resources
from rigamajig2.ui.widgets import mayaMessageBox, pathSelector, stateImageWidget
from rigamajig2.ui.widgets.mayaDialog import MayaDialog

MAYA_FILTER = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
JSON_FILTER = "Json Files (*.json)"

LARGE_BTN_HEIGHT = 35
EDIT_BG_WIDGET_COLOR = QtGui.QColor(70, 70, 80)

logger = logging.getLogger(__name__)


class BuilderDialog(MayaDialog):
    """Builder dialog"""

    WINDOW_TITLE = "Rigamajig2 Builder  {}".format(rigamajig2.version)

    rigFileModifiedSignal = QtCore.Signal()
    rigFileSavedSignal = QtCore.Signal()

    def __init__(self):
        """Constructor for the builder dialog"""
        super(BuilderDialog, self).__init__()

        # Store a rig environment and rig builder variables.
        self.rigEnvironment = None
        self.rigBuilder = None

        self.callbackArray = om.MCallbackIdArray()

        self._rigFileIsModified = False

        self.setMinimumSize(420, 600)
        # with the maya mixin stuff the window comes in at a weird size. This ensures it's not a weird size.
        self.resize(420, 800)

        # if we don't provide a rig file load the most recent one from the recent files list
        recentFile = recentFiles.getMostRecentFile()
        if recentFile:
            self._setRigFile(recentFile)

    @property
    def rigFileIsModified(self):
        return self._rigFileIsModified

    def __menus__(self):
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
        utilsMenu.addAction(self.actions.removeRigamajigCallbacksAction)
        utilsMenu.addAction(self.actions.reloadRigamajigModulesAction)

        toolsMenu = self.mainMenu.addMenu("Tools")
        toolsMenu.addAction(self.actions.openGitVersionControlAction)
        toolsMenu.addSeparator()
        toolsMenu.addAction(self.actions.runPerformanceTestAction)
        toolsMenu.addAction(self.actions.generateRandomAnimationAction)
        toolsMenu.addSeparator()
        toolsMenu.addAction(self.actions.openProfilerAction)
        toolsMenu.addAction(self.actions.openEvaluationToolkitAction)

        helpMenu = self.mainMenu.addMenu("Help")
        helpMenu.addAction(self.actions.openBuilderLogFileAction)
        helpMenu.addSeparator()
        helpMenu.addAction(self.actions.showDocumentationAction)
        helpMenu.addAction(self.actions.showAboutAction)

    def __create__(self):
        """Create Widgets"""
        self.rigPathSelector = pathSelector.PathSelector(
            caption="Select a Rig File", fileFilter="Rig Files (*.rig)", fileMode=1
        )
        self.rigFileSaveStatus = stateImageWidget.StateImageWidget()

        self.assetNameLineEdit = QtWidgets.QLineEdit()
        self.assetNameLineEdit.setPlaceholderText("asset_name")
        self.archetypeBaseLabel = QtWidgets.QLabel("None")

        self.builderSections = [
            modelSection.ModelSection(self),
            skeletonSection.SkeletonSection(self),
            setupSection.SetupSection(self),
            buildSection.BuildSection(self),
            controlsSection.ControlsSection(self),
            deformationSection.DeformationSection(self),
            publishSection.PublishSection(self),
        ]

        self.scrollArea = QtWidgets.QScrollArea()
        self.rigEnvironmentGroupbox = QtWidgets.QGroupBox("Rig Environment")
        self.buildGroupBox = QtWidgets.QGroupBox("Build")

        self.runSelectedButton = QtWidgets.QPushButton("Run Selected")
        self.runButton = QtWidgets.QPushButton("Run")
        self.publishButton = QtWidgets.QPushButton("Publish")
        self.statusLine = QtWidgets.QStatusBar()

    def __layout__(self):
        rigFileLayout = QtWidgets.QHBoxLayout()
        rigFileLayout.addWidget(self.rigPathSelector)
        rigFileLayout.addWidget(self.rigFileSaveStatus)

        rigNameLayout = QtWidgets.QHBoxLayout()
        rigNameLayout.addWidget(QtWidgets.QLabel("Rig Name:"))
        rigNameLayout.addWidget(self.assetNameLineEdit)

        rigNameLayout.addSpacing(10)
        rigNameLayout.addWidget(QtWidgets.QLabel("rig archetype:"))
        rigNameLayout.addWidget(self.archetypeBaseLabel)

        rigEnvironmentLayout = QtWidgets.QVBoxLayout()
        rigEnvironmentLayout.addLayout(rigFileLayout)
        rigEnvironmentLayout.addLayout(rigNameLayout)

        # add the collapsable widgets
        buildLayout = QtWidgets.QVBoxLayout()
        for section in self.builderSections:
            buildLayout.addWidget(section)
        buildLayout.addStretch()

        # groups
        self.rigEnvironmentGroupbox.setLayout(rigEnvironmentLayout)
        self.buildGroupBox.setLayout(buildLayout)

        # lower persistent buttons (AKA close)
        lowButtonsLayout = QtWidgets.QVBoxLayout()
        lowButtonsLayout.setContentsMargins(0, 0, 0, 0)
        runButtonLayout = QtWidgets.QHBoxLayout()
        runButtonLayout.addWidget(self.publishButton)
        runButtonLayout.addWidget(self.runButton)
        runButtonLayout.addStretch()
        runButtonLayout.addWidget(self.runSelectedButton)

        lowButtonsLayout.addLayout(runButtonLayout)
        lowButtonsLayout.addWidget(self.statusLine)

        # scrollable area
        bodyWidget = QtWidgets.QWidget()
        bodyLayout = QtWidgets.QVBoxLayout(bodyWidget)
        bodyLayout.setContentsMargins(0, 0, 0, 0)
        bodyLayout.addWidget(self.rigEnvironmentGroupbox)
        bodyLayout.addWidget(self.buildGroupBox)

        self.scrollArea.setWidget(bodyWidget)

        # main layout
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(4, 4, 4, 4)
        mainLayout.setSpacing(4)
        mainLayout.setMenuBar(self.mainMenu)
        mainLayout.addWidget(self.scrollArea)
        mainLayout.addLayout(lowButtonsLayout)

    def __configure__(self):
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)

        self.runSelectedButton.setIcon(Resources.getIcon(":execute.png"))
        self.runSelectedButton.setToolTip("Run Rig steps up to the break point")
        self.runSelectedButton.setFixedSize(120, 22)

        self.runButton.setIcon(Resources.getIcon(":executeAll.png"))
        self.runButton.setToolTip("Run all build steps.")
        self.runButton.setFixedSize(80, 22)

        self.publishButton.setIcon(Resources.getIcon(":sourceScript.png"))
        self.publishButton.setToolTip("Publish the rig. This will build the rig and save it.")
        self.publishButton.setFixedSize(80, 22)

    def __connect__(self):
        """Create Connections"""

        # setup each widget with a connection to uncheck all over widgets when one is checked.
        # This ensures all setups until a breakpoint are run

        self.assetNameLineEdit.editingFinished.connect(self._setRigName)

        self.rigFileModifiedSignal.connect(partial(self._setRigFileModified, True))
        self.rigFileSavedSignal.connect(partial(self._setRigFileModified, False))

        for widget in self.builderSections:
            widget.mainWidget.headerWidget.checkbox.clicked.connect(partial(self.__handleBreakpoint, widget))

        self.rigPathSelector.selectPathButton.clicked.connect(self._pathSelectorLoadRigFile)
        self.runSelectedButton.clicked.connect(self._runSelected)
        self.runButton.clicked.connect(self._runAll)
        self.publishButton.clicked.connect(self._publish)

    def _pathSelectorLoadRigFile(self):
        """Load a rig file from the path selector"""
        newPath = self.rigPathSelector.getPath()
        if newPath:
            self.actions.loadRecentRigFile(newPath)

    def _setRigFile(self, path=None):
        """
        Set the rig file to the given path
        :param path: rig file to set
        """
        self.rigPathSelector.selectPath(path=path)
        fileInfo = QtCore.QFileInfo(self.rigPathSelector.getPath())
        self.rigEnvironment = fileInfo.path()
        self.rigFile = fileInfo.filePath()

        self.rigBuilder = builder.Builder(self.rigFile)

        if not self.rigFile:
            return

        # setup ui Data
        self.rigName = self.rigBuilder.getRigData(self.rigFile, constants.RIG_NAME)
        self.assetNameLineEdit.setText(self.rigName)

        # set the text of the archetype to the archetype. We need to check if it's a string and update the formatting
        archetype = self.rigBuilder.getRigData(self.rigFile, constants.BASE_ARCHETYPE)
        if isinstance(archetype, (list, tuple)):
            archetype = ", ".join(archetype)
        self.archetypeBaseLabel.setText(str(archetype))

        # set paths and widgets relative to the rig env
        for widget in self.builderSections:
            widget._setBuilder(builder=self.rigBuilder)

        # set the status icon back up to date
        self._setRigFileModified(False)

    # BUILDER FUNCTIONS
    def __handleBreakpoint(self, selectedWidget):
        """This function ensures only one build step is selected at a time. it is run whenever a checkbox is toggled."""
        for section in self.builderSections:
            if section is not selectedWidget:
                section.setChecked(False)

    def _runSelected(self):
        """run selected steps"""

        # ensure at least one breakpoint is selected
        breakpointSelected = False
        for section in self.builderSections:
            if section.isChecked():
                breakpointSelected = True

        if not breakpointSelected:
            logger.error("No breakpoint selected no steps to run")
            return

        if not confirmBuildRig():
            return

        startTime = time.time()

        # because widgets are added to the ui and the list in oder they can be run sequentially.
        # when we hit a widget that is checked then the loop stops.
        for widget in self.builderSections:
            widget._runWidget()

            if widget.isChecked():
                logger.debug(f"Reached selected breakpoint: {widget.__class__.__name__}")
                break

        runTime = time.time() - startTime
        print("Time Elapsed: {}".format(str(runTime)))

    def _runAll(self):
        """Run builder and update the component manager"""

        if not confirmBuildRig():
            return

        try:
            self.rigBuilder.run()

        except Exception as e:
            self.statusLine.showMessage(f"Rig Build Failed: '{self.rigName}'")
            raise e

    def _publish(self):
        """Run builder and update the component manager"""
        # for the rig build we can put the _publish into a try except block
        # if the _publish fails we can add a message to the status line before raising the exception
        try:
            self.publishSection._onPublishWithUiData()

        except Exception as e:
            self.statusLine.showMessage(f"Rig Publish Failed: '{self.rigName}'")
            raise e

    def _setRigFileModified(self, value=True):
        if value:
            self.rigFileSaveStatus.setState(stateImageWidget.State.WARNING, message="Rig file has unsaved changes")
        else:
            self.rigFileSaveStatus.setState(stateImageWidget.State.GOOD, message="Rig file up to date")
        self._rigFileIsModified = value

    def _setupCallbacks(self):
        """Setup required builder callbacks"""
        logger.debug(f"setup Callbacks: {self.callbackArray}")

    def _teardownCallbacks(self):
        """tear down builder callbacks"""
        logger.debug(f"Teardown Callbacks: {self.callbackArray}")

    def showEvent(self, event):
        """Show event for the Builder UI"""
        super().showEvent(event)
        logger.info("Builder UI launched")
        self._setupCallbacks()

    def hideEvent(self, event):
        """override the hide event to delete the scripts jobs from the initialize widget"""
        # this is a bit of a pain instead of using the close event but since we're using
        # the workspace control the closeEvent is now owned by Maya. This is a nice workaround to
        # ensure the script jobs are deleted when the main window is hidden (done my closing the 'X' button)
        # however when in development you should manually call the close() method BEFORE deleting the workspace control.
        super(BuilderDialog, self).hideEvent(event)

        self._teardownCallbacks()

        # call the close event for each builder section so the close logic is more localized
        # to each section. this will not get called by default when using the mayaMixin, so we need to call
        # it explicitly here.
        for section in self.builderSections:
            section.closeEvent()

        logger.info("Builder UI closed")

    def _setRigName(self):
        if self.rigBuilder:
            self.rigBuilder.rigName = self.assetNameLineEdit.text()


def confirmBuildRig():
    """
    This is to check if the scene is safe for a rig rebuild.
    Check if the scene has unsaved changes. If it does give the user a prompt to see if it's safe to clear the scene.

    :return: Returns True or False depending on the scene state and user input
    """

    modified = cmds.file(query=True, anyModified=True)
    if modified:
        confirmPublishMessage = mayaMessageBox.MayaMessageBox(
            title="Run Rig Build",
            message="Proceeding will rebuild the rig based on data you've saved. Unsaved in-scene changes will be lost!",
            icon="help",
        )
        confirmPublishMessage.setButtonsYesNoCancel()
        res = confirmPublishMessage.exec_()

        if res == confirmPublishMessage.Yes:
            return True
        else:
            return False
    return True


if __name__ == "__main__":
    workspace_control_name = BuilderDialog.get_workspace_control_name()
    if cmds.window(workspace_control_name, exists=True):
        # noinspection PyUnboundLocalVariable
        test_dialog.close()
        cmds.deleteUI(workspace_control_name)

    BuilderDialog.module_name_override = "dialog"
    test_dialog = BuilderDialog()
