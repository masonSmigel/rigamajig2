#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: mergeRigs_dialog.py.py
    author: masonsmigel
    date: 01/2023
    discription: 

"""
# PYTHON
import sys
import time
import logging
import os
from collections import OrderedDict

# MAYA
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

# WIDGETS
from rigamajig2.ui.widgets import pathSelector
from rigamajig2.ui import showInFolder

# RIGAMAJIG
from rigamajig2.maya.builder import merge


class MergeRigsDialog(QtWidgets.QDialog):
    """Edit component dialog UI"""
    WINDOW_TITLE = "Rigamajig2: Merge Rig Files"

    dialogInstance = None

    @classmethod
    def showDialog(cls):
        """Show the dialog"""
        if not cls.dialogInstance:
            cls.dialogInstance = MergeRigsDialog()

        if cls.dialogInstance.isHidden():
            cls.dialogInstance.show()
        else:
            cls.dialogInstance.raise_()
            cls.dialogInstance.activateWindow()

    def __init__(self):
        """ Constructor for the builder dialog"""
        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(MergeRigsDialog, self).__init__(mayaMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(420, 220)

        self.rigFile=None

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets"""
        self.rigFile1PathSelector = pathSelector.PathSelector(
            label='Rig File 1:',
            caption='Select a rig File',
            fileFilter="Rig Files (*.rig)",
            fileMode=1,
            relativePath=None,
            parent=None
            )

        self.rigFile2PathSelector = pathSelector.PathSelector(
            label='Rig File 2:',
            caption='Select a rig File',
            fileFilter="Rig Files (*.rig)",
            fileMode=1,
            relativePath=None,
            parent=None
            )

        self.rigNameLineEdit = QtWidgets.QLineEdit()
        self.outputRigSuffix = QtWidgets.QLineEdit()

        self.outputRigSuffix.setPlaceholderText("_rig-deliver")

        self.outputPathSelector = pathSelector.PathSelector(
            label='Output:',
            caption='Select a folder to place the new rig enviornment',
            fileMode=2,
            relativePath=None,
            parent=None
            )

        self.mergeMethodComboBox = QtWidgets.QComboBox()
        self.mergeMethodComboBox.addItem("game")
        self.mergeMethodComboBox.addItem("film")

        self.mergeButton = QtWidgets.QPushButton("Merge Rigs")

        self.showInFolderButton = QtWidgets.QPushButton("Show New Rig file")
        self.showInFolderButton.setHidden(True)

    def createLayouts(self):
        """ Create Layouts"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        mergeMessage = """Merge two rig files into a single rig file. The order of rig files in vital! the first one will be used when there are discrepencies!
        \nFor feilds such as blendshapes, skins and SHAPES only both rig files must be set to none OR a Directory, individual files cannot be used!
        \nPlease be aware that you will likely need to cleanup the merged file. This is not meant to provide a completed rig but rather provide a starting point."""

        mergeInfoLayout = QtWidgets.QVBoxLayout()
        mergePlainText = QtWidgets.QPlainTextEdit(mergeMessage)
        mergePlainText.setFixedHeight(150)
        mergeInfoLayout.addWidget(mergePlainText)

        mergeLayout = QtWidgets.QVBoxLayout()

        mergeLayout.addWidget(self.rigFile1PathSelector)
        mergeLayout.addWidget(self.rigFile2PathSelector)
        mergeLayout.addWidget(self.outputPathSelector)

        # outputInfo form layout
        outputFormLayout = QtWidgets.QFormLayout()

        outputFormLayout.addRow(QtWidgets.QLabel("New Rig Name:"), self.rigNameLineEdit)
        outputFormLayout.addRow(QtWidgets.QLabel("New Rig Suffix:"), self.outputRigSuffix)
        outputFormLayout.addRow(QtWidgets.QLabel("Skin Merge Method:"), self.mergeMethodComboBox)
        mergeLayout.addLayout(outputFormLayout)

        # build the final layout
        mergeInfoGroup = QtWidgets.QGroupBox('Merge Info')
        mergeInfoGroup.setLayout(mergeInfoLayout)

        mergeDataGroup = QtWidgets.QGroupBox('Merge')
        mergeDataGroup.setLayout(mergeLayout)

        self.mainLayout.addWidget(mergeInfoGroup)
        self.mainLayout.addWidget(mergeDataGroup)

        self.mainLayout.addWidget(self.mergeButton)
        self.mainLayout.addWidget(self.showInFolderButton)

    def createConnections(self):
        """ Create Connections"""
        self.mergeButton.clicked.connect(self.mergeRigs)
        self.showInFolderButton.clicked.connect(self.showNewRigFile)

    def mergeRigs(self):
        """
        connection to merge the two rigs
        """

        rigFile1 = self.rigFile1PathSelector.getPath()
        rigFile2 = self.rigFile2PathSelector.getPath()

        outputPath = self.outputPathSelector.getPath()

        rigName = self.rigNameLineEdit.text()

        rigSuffix = self.outputRigSuffix.text()

        if rigSuffix is None:
            rigSuffix = self.outputRigSuffix.placeholderText()

        mergeMethod = self.mergeMethodComboBox.currentText()

        # with all this we can now merge the rigs
        rigFile = merge.mergeRigs(
            rigFile1=rigFile1,
            rigFile2=rigFile2,
            rigName=rigName,
            mergedPath=outputPath,
            outputSuffix=rigSuffix,
            method=mergeMethod
            )

        # unhide the rig show in folder button and store the rig file to show
        self.showInFolderButton.setHidden(False)
        self.rigFile = rigFile

    def showNewRigFile(self):
        """Show the new rig file"""
        showInFolder.showInFolder(self.rigFile)

if __name__ == '__main__':
    dialog = MergeRigsDialog()
    dialog.showDialog()
