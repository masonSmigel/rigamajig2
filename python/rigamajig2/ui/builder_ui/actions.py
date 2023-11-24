#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: actions.py
    author: masonsmigel
    date: 07/2022
    description: 
"""
import logging
from functools import partial

import maya.mel as mel
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import rigamajig2
import rigamajig2.maya.qc as qc
from rigamajig2.maya.rig import rigcallbacks
from rigamajig2.ui.builder_ui import recentFiles
from rigamajig2.ui.builder_ui.dialogs import gitDialog
from rigamajig2.ui.builder_ui.dialogs import mergeRigsDialog
from rigamajig2.ui.builder_ui.dialogs import newRigFileDialog
from rigamajig2.ui.resources import Resources


class Actions(object):
    """ Setup the actions for the builder dialog"""

    def __init__(self, dialog):
        """
        This class will setup the actions for the the builder Dialog.
        You must pass in the dialog as the self.dialog parameter

        :param dialog: dialog to connect the actions to
        """
        self.dialog = dialog
        self.createActions()

    def createActions(self):
        """ Create the Actions"""
        # FILE
        self.newRigFileAction = QtWidgets.QAction("New Rig File", self.dialog)
        self.newRigFileAction.setIcon(Resources.getIcon(":fileNew.png"))
        self.newRigFileAction.triggered.connect(self.createRigEnvironment)

        self.loadRigFileAction = QtWidgets.QAction("Load Rig File", self.dialog)
        self.loadRigFileAction.setIcon(Resources.getIcon(":folder-open.png"))
        self.loadRigFileAction.triggered.connect(self.loadRigFile)

        self.saveRigFileAction = QtWidgets.QAction("Save Rig File", self.dialog)
        self.saveRigFileAction.setIcon(Resources.getIcon(":save.png"))
        self.saveRigFileAction.triggered.connect(self.saveRigFile)

        # add a submenu to load recent rigFiles
        self.recentRigFileMenu = QtWidgets.QMenu("Recent Rig Files ...", self.dialog)
        self.recentRigFileMenu.setIcon(Resources.getIcon(":out_time.png"))
        self.updateRecentFiles()

        self.reloadRigFileAction = QtWidgets.QAction("Reload Rig File", self.dialog)
        self.reloadRigFileAction.setIcon(Resources.getIcon(":refresh.png"))
        self.reloadRigFileAction.triggered.connect(self.reloadRigFile)

        # UTILS
        self.reloadRigamajigModulesAction = QtWidgets.QAction("Reload Rigamajig2 Modules", self.dialog)
        self.reloadRigamajigModulesAction.triggered.connect(self.reloadRigamajigModules)

        self.removeRigamajigCallbacksAction = QtWidgets.QAction("Remove Rigamajig Callbacks", self.dialog)
        self.removeRigamajigCallbacksAction.triggered.connect(self.removeRigamajigCallbacks)

        self.mergeRigFilesAction = QtWidgets.QAction("Merge Rig Files", self.dialog)
        self.mergeRigFilesAction.triggered.connect(self.showMergeRigFilesDialog)

        self.devModeAction = QtWidgets.QAction("Dev Mode", self.dialog)
        self.devModeAction.setCheckable(True)

        # TOOLS
        self.openGitVersionControlAction = QtWidgets.QAction("Git Version Control", self.dialog)
        self.openGitVersionControlAction.triggered.connect(self.openGitVersionControlDialog)

        self.runPerformanceTestAction = QtWidgets.QAction("Run Performance Test", self.dialog)
        self.runPerformanceTestAction.triggered.connect(self.runPerformanceTest)

        self.generateRandomAnimationAction = QtWidgets.QAction("Generate Random Animation", self.dialog)
        self.generateRandomAnimationAction.triggered.connect(self.generateRandomAnimation)

        self.openProfilerAction = QtWidgets.QAction("Profiler", self.dialog)
        self.openProfilerAction.triggered.connect(self.openProfiler)

        self.openEvaluationToolkitAction = QtWidgets.QAction("Evaluation Toolkit", self.dialog)
        self.openEvaluationToolkitAction.triggered.connect(self.openEvaluationToolkit)

        # HELP
        self.openBuilderLogFileAction = QtWidgets.QAction("Open Log file", self.dialog)
        self.openBuilderLogFileAction.triggered.connect(self._openLogFile)

        self.showDocumentationAction = QtWidgets.QAction("Documentation", self.dialog)
        self.showDocumentationAction.triggered.connect(self.showDocumentation)

        self.showAboutAction = QtWidgets.QAction("About", self.dialog)
        self.showAboutAction.triggered.connect(self.showAbout)

    def createRigEnvironment(self):
        """ Create Rig Environment"""
        createDialog = newRigFileDialog.CreateRigEnvDialog()
        createDialog.newRigEnviornmentCreated.connect(self.dialog._setRigFile)
        createDialog.showDialog()

    def loadRigFile(self):
        """ Load a rig file"""
        fileDialog = QtWidgets.QFileDialog()
        fileDialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
        fileDialog.setNameFilters(["Rig Files (*.rig)"])

        result = fileDialog.exec_()

        if result:
            rigfile = fileDialog.selectedFiles()[0]
            self.dialog._setRigFile(rigfile)
            recentFiles.addRecentFile(rigfile)
            self.updateRecentFiles()

    def loadRecentRigFile(self, rigfile):
        self.dialog._setRigFile(rigfile)

        # lets re-add the recent file. This will just move it to the top of the list. Then update the list
        recentFiles.addRecentFile(rigfile)
        self.updateRecentFiles()

    def saveRigFile(self):
        """ Save out a rig file """
        self.dialog.rigBuilder.saveRigFile()
        self.dialog.rigFileSavedSignal.emit()

    def reloadRigFile(self):
        """ Reload rig file"""
        self.dialog._setRigFile(self.dialog.rigFile)

    def updateRecentFiles(self):
        """Update the recent file menu based on our recent file list"""

        # clear the recent file menu
        self.recentRigFileMenu.clear()

        # add any new recent files to the submenu
        for recentFile in recentFiles.getRecentFileList():
            openRecentFileAction = QtWidgets.QAction(recentFile, self.recentRigFileMenu)
            openRecentFileAction.triggered.connect(partial(self.loadRecentRigFile, recentFile))

            self.recentRigFileMenu.addAction(openRecentFileAction)

    # TOOLS MENU
    def runPerformanceTest(self):
        """ Run Performance tests"""
        qc.runPerformanceTest()

    def generateRandomAnimation(self):
        """ Generate Random animation"""
        qc.generateRandomAnim()

    def openProfiler(self):
        mel.eval("ProfilerTool;")

    def openEvaluationToolkit(self):
        mel.eval("openEvaluationToolkit;")

    def openGitVersionControlDialog(self):
        rigEnv = self.dialog.rigEnvironment
        gitDialog.GitDialog.showDialog()

        # set the rig repo
        gitDialog.GitDialog.dlg_instance.setRepo(rigEnv)

    def reloadRigamajigModules(self):
        """ Reload riamajig modules"""
        rigamajig2.reloadModule(log=True)

    def removeRigamajigCallbacks(self):
        rigcallbacks.clearRigamajigCallbacks()

    def showMergeRigFilesDialog(self):
        """ Show the merge rig files dialog"""
        mergeRigsDialog.MergeRigsDialog.showDialog()

    # SHOW HELP

    def _openLogFile(self):
        """Open the log file by getting the first handler of the root rigamajig logger."""
        rigamajig2RootLogger = logging.getLogger("rigamajig2")
        logFile = rigamajig2RootLogger.handlers[0].baseFilename

        url = QtCore.QUrl.fromLocalFile(logFile)
        QtGui.QDesktopServices.openUrl(url)

    def showDocumentation(self):
        """ Open Documentation"""
        pass

    def showAbout(self):
        """ Show about"""
        pass
