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

from mayafbx import FbxExportOptions, export_fbx

from rigamajig2.maya import meta
from rigamajig2.maya import decorators
from rigamajig2.maya import container
from rigamajig2.maya import namespace
from rigamajig2.shared import common
from rigamajig2.maya.rig import control
from rigamajig2.maya.anim import keyframe

import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

from rigamajig2.ui.widgets import pathSelector

UPAXIS_DICT = {"x": [0, 0, 90],
               "y": [0, 0, 0],
               "z": [90, 0, 0]}

logger = logging.getLogger(__name__)


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
    cmds.select(bind, model, replace=True)

    # before exporting it we need to setup the export options
    # mel.eval("FBXResetExport")

    # using the awesome mayafbx module we can easily setup the proper arguments for the export
    options = FbxExportOptions()
    options.selected = True
    options.selected_input_connections = True

    options.smoothing_groups = True
    options.smooth_mesh = True
    options.animation = False
    options.deformation = True
    options.defomation_shapes = True
    options.deformation_skins = True
    options.constraints = False

    options.cameras = False

    options.show_warning_ui = False
    options.generate_log = False

    # finally we can do the export. Here we also want to pass in kwargs to allow the user to add any additional options
    export_fbx(outputPath, options)


@decorators.preserveSelection
@decorators.suspendViewport
@decorators.oneUndo
def exportAnimationClip(mainNode, outputPath=None, upAxis='y', cleanTrsGlobal=False):
    """
    Export the selected rig as an FBX without animation. This is used to make the Skeletal mesh for unreal
    :param mainNode: main node of the rig. This is the highest node or 'rig_root' of the rig.
    :param outputPath: path to save the output file to.
    :param cleanTrsGlobal: clean all animation on the trs_global controla and move it to the trs_shot
    :param upAxis: set the up axis.

    :return:
    """

    if not cmds.objExists(mainNode):
        raise Exception("The main node {} does not exist in the scene".format(mainNode))

    mainNode = common.getFirstIndex(mainNode)

    bind = meta.getMessageConnection("{}.bind".format(mainNode))
    model = meta.getMessageConnection("{}.model".format(mainNode))

    # TODO: add some stuff to build the file path

    # before exporting it we need to setup the export options
    minFrame = cmds.playbackOptions(q=True, min=True)
    maxFrame = cmds.playbackOptions(q=True, max=True)

    options = FbxExportOptions()
    options.selected = True
    options.smoothing_groups = True
    options.smooth_mesh = True
    options.animation = True
    options.bake_animation = True
    options.bake_resample_all = True
    options.bake_animation_start = int(minFrame)
    options.bake_animation_end = int(maxFrame)
    options.bake_animation_step = int(1)

    options.use_scene_name = True
    options.deformation = True
    options.defomation_shapes = True
    options.deformation_skins = True
    options.constraints = False
    options.cameras = False
    options.selected_input_connections = True

    options.show_warning_ui = False
    options.generate_log = False

    # if the up axis is set we need to make a tempory transform and connect it to the rig
    tempTransform = cmds.createNode("transform", name="tmpTransform")
    componentContainer = container.getContainerFromNode(model)
    nodes = container.getNodesInContainer(componentContainer)
    trsNode = [x for x in nodes if "trs_global" in x and control.isControl(x)]

    # if clean trs is on run the clean step
    if cleanTrsGlobal:
        transferTrsAnimToTrsShot(mainNode)

    # check for keyframes or constraints
    connections = cmds.listConnections(trsNode, s=True, d=False) or list()
    if len(connections) > 0:
        cmds.warning("{} has incoming connections. pre-rotaton may not apply as expected".format(trsNode))

    const = cmds.parentConstraint(tempTransform, trsNode, mo=True)

    # set the rotation of the temp transform
    cmds.setAttr("{}.r".format(tempTransform), *UPAXIS_DICT[upAxis.lower()])

    # in order to export only the right nodes we need to select them.
    # using the preserve selection decorator will help to ensure we keep the selction we started with
    cmds.select(bind, model, replace=True)

    # finally we can do the export. Here we also want to pass in kwargs to allow the user to add any additional options
    export_fbx(outputPath, options)

    # reset the temp transfrom and delte it.
    cmds.setAttr("{}.r".format(tempTransform), *[0, 0, 0])
    cmds.delete(const, tempTransform)


def gatherRigsFromScene():
    """ Gather a list of all rigs in the scene"""

    # list all nodes associated as a rigamajig root
    rootNodes = meta.getTagged("rigamajigVersion", type=None, namespace="*")
    return rootNodes


@decorators.oneUndo
def transferTrsAnimToTrsShot(mainNode):
    """
    Prep the rig to be exported properly. This will run several steps:

    first we will transfer all animation on the trs_global, trs_shot and trs_motion controls to only the trs_shot
    :param mainNode:
    :return:
    """
    mainNode = common.getFirstIndex(mainNode)

    if not cmds.objExists(mainNode):
        raise Exception("The main node {} does not exist in the scene".format(mainNode))

    componentContainer = container.getContainerFromNode(mainNode)
    nodes = container.getNodesInContainer(componentContainer)
    trsShot = [x for x in nodes if "trs_shot" in x and control.isControl(x)]
    trsMotion = [x for x in nodes if "trs_motion" in x and control.isControl(x)]

    # create a locator and connect the motion control to this. we can re-constrain to this control
    # to copy all gross transforms to the trs_shot control
    tempTransform = cmds.createNode("transform", name="tmpTransform")
    cmds.parentConstraint(trsMotion, tempTransform, mo=False)
    keyframe.bake(tempTransform)

    # we also need to get the scale value to use
    bind = meta.getMessageConnection("{}.bind".format(mainNode))
    scaleValue = cmds.getAttr("{}.s".format(bind))[0]

    # get all the trs controls and reset them.
    keyframe.wipeKeys([ctl for ctl in nodes if control.isControl(ctl)], reset=True)
    trsShotConstraint = cmds.parentConstraint(tempTransform, trsShot, mo=False)
    cmds.setAttr("{}.s".format(trsShot[0]), *scaleValue)

    # bake the transformation back to the trsShot
    keyframe.bake(trsShot)

    # delete the nodes we dont need anymore
    cmds.delete(trsShotConstraint, tempTransform)

    logger.info("All gross transformation for {} transfered to '{}'".format(mainNode, trsShot[0]))


def bakeWholeCharacter(mainNode):
    """
    Bake all controls on a character based on the mainNode
    :param mainNode:
    :return:
    """

    mainNode = common.getFirstIndex(mainNode)

    # get a lsit of all controls
    rigNs = namespace.getNamespace(mainNode)
    controlList = control.getControls(rigNs)

    # bake all the controls
    keyframe.bake(controlList)

    logger.info("Baked keys for {} controls for '{}'".format(len(controlList), rigNs[0]))


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

        # setup the rigList widget
        self.rigsList = QtWidgets.QTreeWidget()
        self.rigsList.setIndentation(10)
        self.rigsList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.rigsList.setHeaderLabels(["", "Rig", "FileName"])
        self.rigsList.setColumnWidth(0, 40)
        self.rigsList.setColumnWidth(1, 180)
        self.rigsList.setHeaderHidden(True)
        self.rigsList.setUniformRowHeights(True)
        self.rigsList.setAlternatingRowColors(True)

        # setup the upAxis combo box
        self.upAxisComboBox = QtWidgets.QComboBox()
        self.upAxisComboBox.addItem("Z (Unreal)")
        self.upAxisComboBox.setItemData(0, "z")
        self.upAxisComboBox.addItem("Y (Maya)")
        self.upAxisComboBox.setItemData(1, "y")

        self.rigsList.setStyleSheet("QTreeView::indicator::unchecked {background-color: rgb(70, 70, 70)}}")

        self.cancelButton = QtWidgets.QPushButton("Close")
        self.cleanTrsGlobalButton = QtWidgets.QPushButton("Clean Trs_Global")
        self.bakeAllControlsButton = QtWidgets.QPushButton("Bake All Controls")
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
        topLayout.addWidget(QtWidgets.QLabel("Export Up Axis:"))
        topLayout.addWidget(self.upAxisComboBox)
        topLayout.addSpacing(40)
        topLayout.addWidget(self.outputPath)

        # setup the bottom buttons
        botLayout = QtWidgets.QHBoxLayout()
        botLayout.setAlignment(QtCore.Qt.AlignRight)
        botLayout.addWidget(self.cancelButton)
        botLayout.addWidget(self.cleanTrsGlobalButton)
        botLayout.addWidget(self.bakeAllControlsButton)
        botLayout.addWidget(self.exportButton)

        # add all widgets to the main layout
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.rigsList)
        mainLayout.addLayout(botLayout)

    def createConnections(self):
        """Create Pyside connections"""
        self.refreshButton.clicked.connect(self.refreshList)
        self.cancelButton.clicked.connect(self.close)
        self.cleanTrsGlobalButton.clicked.connect(self.cleanTrsGlobal)
        self.bakeAllControlsButton.clicked.connect(self.bakeAllControls)
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
        # clear the current rig list...
        self.rigsList.clear()

        # ... then add new items based on the info gathered in the scene
        for item in sorted(gatherRigsFromScene()):
            rigName = item.split(":")[0]
            self.addToList(rigName=rigName, mainNode=item)

    def exportSelected(self):
        """Export all the selected items"""

        outputFilePath = self.outputPath.getPath(absoultePath=True)
        if outputFilePath is None:
            cmds.error("Please select an output path before exporting FBXs")
            return

        logger.info("----- Begin Animation Clip Export -----")

        upAxis = self.upAxisComboBox.currentData()

        counter = 0
        # for each item export all the fbx files.
        for i in range(self.rigsList.topLevelItemCount()):
            # get informaiton associated with the mainNode
            item = self.rigsList.topLevelItem(i)

            if item.checkState(0):
                mainNode = item.data(1, QtCore.Qt.UserRole)
                fileName = item.text(2)
                counter += 1

                # export the FBX file
                fullFilePath = os.path.join(outputFilePath, fileName)
                exportAnimationClip(mainNode, outputPath=fullFilePath, upAxis=upAxis)

        logger.info("-----  Animation Clip Export Complete for {} rigs -----".format(counter))

    def cleanTrsGlobal(self):
        """Bake all controls on the selected rigs"""

        result = cmds.confirmDialog(
            t='Clean Gross Transformation',
            message="Cleaning Gross Transformations is a distuctive Process. Are you sure you want to continue?!",
            button=['Cancel', 'Continue'],
            defaultButton='Continue',
            cancelButton='Cancel')

        if result != 'Continue':
            return

        logger.info("----- Begin Clean Gross Transformation -----")
        counter = 0
        # for each item export all the fbx files.
        for i in range(self.rigsList.topLevelItemCount()):
            # get informaiton associated with the mainNode
            item = self.rigsList.topLevelItem(i)

            if item.checkState(0):
                mainNode = item.data(1, QtCore.Qt.UserRole)
                transferTrsAnimToTrsShot(mainNode=mainNode)
                counter += 1
        logger.info("----- Clean Gross Transformation Complete for {} Rigs -----".format(counter))

    def bakeAllControls(self):
        """Bake all controls on the selected rigs"""

        result = cmds.confirmDialog(
            t='Bake All Controls',
            message="Baking all controls is a distuctive Process. Are you sure you want to continue?!",
            button=['Cancel', 'Continue'],
            defaultButton='Continue',
            cancelButton='Cancel')

        if result != 'Continue':
            return

        logger.info("----- Begin Bake All Controls -----")
        counter = 0
        # for each item export all the fbx files.
        for i in range(self.rigsList.topLevelItemCount()):
            # get informaiton associated with the mainNode
            item = self.rigsList.topLevelItem(i)

            if item.checkState(0):
                mainNode = item.data(1, QtCore.Qt.UserRole)
                bakeWholeCharacter(mainNode=mainNode)
                counter += 1

        logger.info("----- Bake All Controls Complete for {} Rigs -----".format(counter))


if __name__ == '__main__':
    try:
        dlg.deleteLater()
    except:
        print "didnt delete"

    dlg = BatchExportFBX()
    dlg.show()
    # prepRigForExport('lich_rig_proxy:main')
