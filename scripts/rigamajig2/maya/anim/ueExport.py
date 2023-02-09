#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: ue.py
    author: masonsmigel
    date: 02/2023
    discription: Functions for working with rigamajig and unreal within maya

"""
import os
import sys
import logging
from collections import OrderedDict
import maya.cmds as cmds
import maya.mel as mel
from rigamajig2.maya import meta
from rigamajig2.maya import decorators

import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

from rigamajig2.ui.widgets import pathSelector


logger = logging.getLogger(__name__)

try:
    if "fbxmaya" not in cmds.pluginInfo(q=True, ls=True):
        cmds.loadPlugin("fbxmaya")
except:
    raise Exception("Failed to load maya FBX plugin")


def formatFBXOptions(options):
    """
    Format a dictonary of keywords and values into a string to be used as the 'options' argument in the file comman
    :param options: dictionary of keywords and values to set in the string formatting
    :return: string of options
    """

    resultString = str()
    for option in options:
        value = options[option]
        if value == True or value == False:
            value = 1 if value == True else 0

        print '{} -v {}'.format(option, value)
        mel.eval('{} -v {}'.format(option, value))

        resultString += "{}={};".format(option, value)
    return resultString


@decorators.preserveSelection
def exportSkeletalMesh(mainNode, outputPath=None):
    """
    Export the selected rig as an FBX without animation. This is used to make the Skeletal mesh for unreal
    :param mainNode: main node of the rig. This is the highest node or 'rig_root' of the rig.
    :param outputPath: path to save the output file to.

    :return:
    """

    if not cmds.objExists(mainNode):
        raise Exception("The main node {} does not exist in the scene".format(mainNode))

    bind = meta.getMessageConnection("{}.bind".format(mainNode))
    model = meta.getMessageConnection("{}.model".format(mainNode))

    # TODO: add some stuff to build the file path

    # in order to export only the right nodes we need to select them.
    # using the preserve selection decorator will help to ensure we keep the selction we started with
    cmds.select(bind, model)

    # before exporting it we need to setup the export options

    mel.eval('FBXResetExport')
    options = OrderedDict(FBXExportSkins=True,
                          FBXExportShapes=True,
                          FBXExportCameras=False,
                          FBXExportSmoothMesh=True,
                          FBXExportSmoothingGroups=True,
                          FBXExportLights=False,
                          # FBXExportAnimation=False,
                          FBXExportBakeComplexAnimation=False,
                          # FBXExportBakeResampleAll=False,
                          FBXExportConstraints=False,
                          FBXExportInputConnections=False
                          )

    # finally we can do the export. Here we also want to pass in kwargs to allow the user to add any additional options
    cmds.file(outputPath,
              exportSelected=True,
              force=True,
              type="FBX export",
              preserveReferences=True,
              options=formatFBXOptions(options=options))


def gatherRigsFromScene():
    """ Gather a list of all rigs in the scene"""

    # list all nodes associated as a rigamajig root
    rootNodes = meta.getTagged("rigamajigVersion", type=None, namespace="*")
    return rootNodes


@decorators.preserveSelection
def exportAnimationClip(mainNode, outputPath=None):
    """
    Export the selected rig as an FBX without animation. This is used to make the Skeletal mesh for unreal
    :param mainNode: main node of the rig. This is the highest node or 'rig_root' of the rig.
    :param outputPath: path to save the output file to.

    :return:
    """

    if not cmds.objExists(mainNode):
        raise Exception("The main node {} does not exist in the scene".format(mainNode))

    bind = meta.getMessageConnection("{}.bind".format(mainNode))
    model = meta.getMessageConnection("{}.model".format(mainNode))

    # TODO: add some stuff to build the file path

    # in order to export only the right nodes we need to select them.
    # using the preserve selection decorator will help to ensure we keep the selction we started with
    cmds.select(bind, model)

    # before exporting it we need to setup the export options
    minFrame = cmds.playbackOptions(q=True, min=True)
    maxFrame = cmds.playbackOptions(q=True, max=True)

    mel.eval('FBXResetExport')
    options = OrderedDict(FBXExportSkins=True,
                          FBXExportShapes=True,
                          FBXExportCameras=False,
                          FBXExportSmoothMesh=True,
                          FBXExportSmoothingGroups=True,
                          FBXExportLights=False,
                          # FBXExportAnimation=True,
                          FBXExportBakeComplexAnimation=True,
                          FBXExportBakeComplexStart=int(minFrame),
                          FBXExportBakeComplexEnd=int(maxFrame),
                          # FBXExportBakeResampleAll=True,
                          FBXExportConstraints=False,
                          FBXExportUseSceneName=True,
                          )

    # finally we can do the export. Here we also want to pass in kwargs to allow the user to add any additional options
    cmds.file(outputPath,
              exportSelected=True,
              force=True,
              type="FBX export",
              preserveReferences=True,
              options=formatFBXOptions(options=options))


class BatchExportFBX(QtWidgets.QDialog):
    """ Dialog for the mocap import """
    WINDOW_TITLE = "Batch FBX Exporter "

    dlg_instance = None

    @classmethod
    def showDialog(cls):
        """Show the dialog"""
        if not cls.dlg_instance:
            cls.dlg_instance = BatchExportFBX()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
            cls.dlg_instance.refreshList()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self):
        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(BatchExportFBX, self).__init__(mayaMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(600, 400)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """Create widgets"""
        self.refreshButton = QtWidgets.QPushButton("Refresh Scene")

        self.outputPath = pathSelector.PathSelector(
            label='Output Dir:',
            caption="Select a Directory to Save files to",
            fileMode=2,
            relativePath=None,
            parent=None)

        self.rigsList = QtWidgets.QTreeWidget()
        self.rigsList.setIndentation(10)
        self.rigsList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.rigsList.setHeaderLabels(["", "Rig", "FileName"])
        self.rigsList.setColumnWidth(0, 40)
        self.rigsList.setColumnWidth(1, 180)
        self.rigsList.setHeaderHidden(True)
        self.rigsList.setUniformRowHeights(True)
        self.rigsList.setAlternatingRowColors(True)

        self.rigsList.setStyleSheet("QTreeView::indicator::unchecked {background-color: rgb(70, 70, 70)}}")

        self.cancelButton = QtWidgets.QPushButton("Close")
        self.exportButton = QtWidgets.QPushButton("Export")
        self.exportButton.setFixedWidth(160)

    def createLayouts(self):
        """Create layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(4)

        # setup the buttons along the top
        topLayout = QtWidgets.QHBoxLayout()
        topLayout.addWidget(self.refreshButton)
        topLayout.addSpacing(40)
        topLayout.addWidget(self.outputPath)

        # setup the list widget

        # setup the bottom buttons
        botLayout = QtWidgets.QHBoxLayout()
        botLayout.setAlignment(QtCore.Qt.AlignRight)
        botLayout.addWidget(self.cancelButton)
        botLayout.addWidget(self.exportButton)

        # add all widgets to the main layout
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.rigsList)
        mainLayout.addLayout(botLayout)

    def createConnections(self):
        """Create Pyside connections"""
        self.refreshButton.clicked.connect(self.refreshList)
        self.cancelButton.clicked.connect(self.close)
        self.exportButton.clicked.connect(self.exportSelected)

    def addToList(self, rigName, mainNode):
        """ Add a new item to the list """

        # create the item snd set the item side
        item = QtWidgets.QTreeWidgetItem(self.rigsList)
        item.setSizeHint(0, QtCore.QSize(25, 25))

        # setup the checkbox
        item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(0, QtCore.Qt.Unchecked)

        # setup the rig name
        item.setText(1, str(rigName))
        print mainNode
        item.setData(1, QtCore.Qt.UserRole, str(mainNode))

        # setup the file name
        fileName = cmds.file(q=True, sn=True, shn=True)
        baseName = fileName.split('.')[0]
        oututFileName = "{}_{}.fbx".format(baseName, rigName)
        item.setData(1, QtCore.Qt.UserRole, mainNode)
        item.setText(2, str(oututFileName))
        item.setTextColor(2, QtGui.QColor(125, 125, 125))

    def refreshList(self):
        """ Gather a list of all rigs in the scene"""
        self.rigsList.clear()

        # ... then add new items based on the info gathered in the scene
        for item in sorted(gatherRigsFromScene()):
            rigName = item.split(":")[0]
            self.addToList(rigName=rigName, mainNode=item)

    def exportSelected(self):
        """Export all the selected items"""

        outputFilePath = self.outputPath.getPath(absoultePath=True)
        print outputFilePath
        if outputFilePath is None:
            cmds.error("Please select an output path before exporting FBXs")
            return

        # for each item export all the fbx files.
        for i in range(self.rigsList.topLevelItemCount()):
            # get informaiton associated with the mainNode
            item = self.rigsList.topLevelItem(i)
            mainNode = item.data(1, QtCore.Qt.UserRole)
            fileName = item.text(2)

            # export the FBX file
            fullFilePath = os.path.join(outputFilePath, fileName)
            exportAnimationClip(mainNode, outputPath=fullFilePath)
            logger.info("Exported animation clip for {} ({})".format(mainNode, fileName))


if __name__ == '__main__':
    exportSkeletalMesh("lich_rig_proxy:main", outputPath="/Users/masonsmigel/Desktop/lich_mesh.fbx")
    exportAnimationClip("lich_rig_proxy:main", outputPath="/Users/masonsmigel/Desktop/lich_anim.fbx")

    # print gatherRigsFromScene()
    # try:
    #     dlg.deleteLater()
    # except:
    #     print "didnt delete"
    #
    # dlg = BatchExportFBX()
    # dlg.show()
