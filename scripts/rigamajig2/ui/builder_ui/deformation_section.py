#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: deformation_section.py
    author: masonsmigel
    date: 07/2022
    description: 

"""
# MAYA
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
import rigamajig2.maya.builder.constants
from rigamajig2.maya import skinCluster
from rigamajig2.maya.builder import data_manager
from rigamajig2.maya.builder.constants import SKINS, SHAPES, DEFORMERS, DEFORM_LAYERS, DEFORMER_DATA_TYPES
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui import deformationLayer_dialog
from rigamajig2.ui.builder_ui import style
from rigamajig2.ui.builder_ui.widgets import builderSection, dataLoader
from rigamajig2.ui.widgets import pathSelector


class DeformationSection(builderSection.BuilderSection):
    """ Deformation layout for the builder UI """

    WIDGET_TITLE = "Deformations"

    def createWidgets(self):
        """ Create Widgets"""
        self.deformLayerPathSelector = pathSelector.PathSelector(
            "layers:",
            caption='Select a deformationLayer file',
            fileFilter=common.JSON_FILTER,
            fileMode=1)

        self.loadDeformLayersButton = QtWidgets.QPushButton("Load Deform Layers")
        self.loadDeformLayersButton.setIcon(QtGui.QIcon(common.getIcon("loadDeformLayers.png")))
        self.saveDeformLayersButton = QtWidgets.QPushButton("Save Deform Layers")
        self.saveDeformLayersButton.setIcon(QtGui.QIcon(common.getIcon("saveDeformLayers.png")))
        self.manageDeformLayersButton = QtWidgets.QPushButton("Manage")
        self.manageDeformLayersButton.setIcon(QtGui.QIcon(common.getIcon("manageDeformLayers.png")))

        self.skinPathSelector = pathSelector.PathSelector(
            "skin:",
            caption="Select the skin weight folder",
            fileFilter=common.JSON_FILTER,
            fileMode=2)
        self.loadAllSkinButton = QtWidgets.QPushButton("Load All Skins")
        self.loadAllSkinButton.setIcon(QtGui.QIcon(common.getIcon("loadSkincluster.png")))
        self.loadSingleSkinButton = QtWidgets.QPushButton("Load Skin")
        self.loadSingleSkinButton.setIcon(QtGui.QIcon(common.getIcon("loadSkincluster.png")))
        self.saveSkinsButton = QtWidgets.QPushButton("Save Skin")
        self.saveSkinsButton.setIcon(QtGui.QIcon(common.getIcon("saveSkincluster.png")))

        self.loadDeformLayersButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveDeformLayersButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.manageDeformLayersButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadAllSkinButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadSingleSkinButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveSkinsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)

        self.loadAllSkinButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.loadSingleSkinButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveSkinsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.loadDeformLayersButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveDeformLayersButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.manageDeformLayersButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.skinEditWidget = rigamajig2.ui.widgets.collapseableWidget.CollapsibleWidget('Edit Skin Cluster')
        self.skinEditWidget.setHeaderBackground(style.EDIT_BG_HEADER_COLOR)
        self.skinEditWidget.setDarkPallete()

        self.copySkinWeightsButton = QtWidgets.QPushButton("Copy Skin Weights and Influences")
        self.copySkinWeightsButton.setIcon(QtGui.QIcon(":copySkinWeight"))
        self.connectBpmsButton = QtWidgets.QPushButton("Connect BPMs on Skins")

        self.deformersDataLoader = dataLoader.DataLoader(
            label="Deformers:",
            caption="Select a Deformer file",
            fileFilter=common.JSON_FILTER,
            fileMode=1,
            dataFilteringEnabled=True,
            dataFilter=DEFORMER_DATA_TYPES)

        # grow the widget a little bit. We will be loading alot of data.
        self.deformersDataLoader.changeTreeWidgetSize(40)

        self.saveDeformersButton = QtWidgets.QPushButton("Save Deformer")
        self.saveDeformersButton.setIcon(QtGui.QIcon(common.getIcon("saveDeformers.png")))
        self.saveDeformersButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveDeformersButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.loadDeformersButton = QtWidgets.QPushButton("Load Deformers")
        self.loadDeformersButton.setIcon(QtGui.QIcon(common.getIcon("loadDeformers.png")))
        self.loadDeformersButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadDeformersButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

    def createLayouts(self):
        """ Create Layouts"""

        deformLayerLayout = QtWidgets.QHBoxLayout()
        deformLayerLayout.setContentsMargins(0, 0, 0, 0)
        deformLayerLayout.setSpacing(4)
        deformLayerLayout.addWidget(self.loadDeformLayersButton)
        deformLayerLayout.addWidget(self.saveDeformLayersButton)
        deformLayerLayout.addWidget(self.manageDeformLayersButton)

        # add the deformation layers back to the collapseable widget
        self.mainWidget.addWidget(self.deformLayerPathSelector)
        self.mainWidget.addLayout(deformLayerLayout)

        self.mainWidget.addSpacing(10)

        skinButtonLayout = QtWidgets.QHBoxLayout()
        skinButtonLayout.setContentsMargins(0, 0, 0, 0)
        skinButtonLayout.setSpacing(4)
        skinButtonLayout.addWidget(self.loadAllSkinButton)
        skinButtonLayout.addWidget(self.loadSingleSkinButton)
        skinButtonLayout.addWidget(self.saveSkinsButton)

        # add the skin layers back to the collapseable widget
        self.mainWidget.addWidget(self.skinPathSelector)
        self.mainWidget.addLayout(skinButtonLayout)

        self.mainWidget.addWidget(self.skinEditWidget)
        self.skinEditWidget.addWidget(self.copySkinWeightsButton)
        self.skinEditWidget.addWidget(self.connectBpmsButton)
        self.skinEditWidget.addSpacing(4)

        self.mainWidget.addSpacing(10)

        deformersButtonLayout = QtWidgets.QHBoxLayout()
        deformersButtonLayout.setContentsMargins(0, 0, 0, 0)
        deformersButtonLayout.setSpacing(4)
        deformersButtonLayout.addWidget(self.loadDeformersButton)
        deformersButtonLayout.addWidget(self.saveDeformersButton)

        self.mainWidget.addWidget(self.deformersDataLoader)
        self.mainWidget.addLayout(deformersButtonLayout)

    def createConnections(self):
        """ Create Connections"""
        self.deformLayerPathSelector.pathUpdated.connect(self._setDeformLayerFile)
        self.skinPathSelector.pathUpdated.connect(self._setSkinFiles)
        self.deformersDataLoader.filesUpdated.connect(self._setDeformerFiles)

        self.loadDeformLayersButton.clicked.connect(self._onLoadDeformationLayers)
        self.saveDeformLayersButton.clicked.connect(self._onSaveDeformationLayers)
        self.manageDeformLayersButton.clicked.connect(self._onOpenDeformLayerManager)

        self.loadAllSkinButton.clicked.connect(self._onLoadAllSkins)
        self.loadSingleSkinButton.clicked.connect(self._onLoadSingleSkin)
        self.saveSkinsButton.clicked.connect(self._onSaveSkin)
        self.copySkinWeightsButton.clicked.connect(self._onCopySkins)
        self.connectBpmsButton.clicked.connect(self._connectBindPreMatrix)
        self.saveDeformersButton.clicked.connect(self._onSaveDeformerData)
        self.loadDeformersButton.clicked.connect(self._onLoadDeformerData)

    @QtCore.Slot()
    def _setBuilder(self, builder):
        """ Set a builder for intialize widget"""
        super()._setBuilder(builder)
        self.deformLayerPathSelector.setRelativePath(self.builder.getRigEnvironment())
        self.skinPathSelector.setRelativePath(self.builder.getRigEnvironment())

        self.deformersDataLoader.clear()
        self.deformersDataLoader.clear()
        self.deformersDataLoader.setRelativePath(self.builder.getRigEnvironment())

        # update data within the rig
        deformLayerFile = self.builder.getRigData(self.builder.getRigFile(), DEFORM_LAYERS)
        self.deformLayerPathSelector.selectPath(deformLayerFile)

        skinFile = self.builder.getRigData(self.builder.getRigFile(), SKINS)
        self.skinPathSelector.selectPath(skinFile)

        # here in older files we sometimes used a different Key for Shapes. So we need to load SHapes keys BEFORE
        # loading the deformers key into the data loader
        SHAPESFile = self.builder.getRigData(self.builder.getRigFile(), SHAPES)
        self.deformersDataLoader.selectPath(SHAPESFile)

        DeformerFiles = self.builder.getRigData(self.builder.getRigFile(), DEFORMERS)
        self.deformersDataLoader.selectPaths(common.toList(DeformerFiles))

    @QtCore.Slot()
    def _runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self._onLoadDeformationLayers()
        self._onLoadAllSkins()
        self._onLoadDeformerData()

    # CONNECTIONS
    @QtCore.Slot()
    def _onLoadDeformationLayers(self):
        """ Save load pose reader setup from json using the builder """
        self.builder.loadDeformationLayers()

    @QtCore.Slot()
    def _onSaveDeformationLayers(self):
        """ Save pose reader setup to json using the builder """
        data_manager.saveDeformationLayers(self.deformLayerPathSelector.getPath())

    @QtCore.Slot()
    def _onOpenDeformLayerManager(self):
        dialogInstance = deformationLayer_dialog.DeformLayerDialog()
        dialogInstance.show()

    @QtCore.Slot()
    def _onLoadAllSkins(self):
        """Load all skin weights in the given folder"""
        self.builder.loadSkinWeights()

    @QtCore.Slot()
    def _onLoadSingleSkin(self):
        """Load a single skin file"""
        filepath = cmds.fileDialog2(
            dialogStyle=2,
            caption="Select a skin file",
            fileFilter=common.JSON_FILTER,
            okc="Select",
            dir=self.skinPathSelector.getPath()
        )
        if filepath:
            data_manager.loadSingleSkin(filepath[0])

    @QtCore.Slot()
    def _onSaveSkin(self):
        """Save the skin weights"""
        data_manager.saveSkinWeights(self.skinPathSelector.getPath())

    @QtCore.Slot()
    def _onCopySkins(self):
        """ Copy Skin weights"""
        src = cmds.ls(sl=True)[0]
        dst = cmds.ls(sl=True)[1:]
        skinCluster.copySkinClusterAndInfluences(src, dst)

    @QtCore.Slot()
    def _connectBindPreMatrix(self):
        """
        Connect influence joints to their respective bindPreMatrix
        """
        for mesh in cmds.ls(sl=True):
            sc = skinCluster.getSkinCluster(mesh)
            skinCluster.connectExistingBPMs(sc)

    @QtCore.Slot()
    def _onLoadDeformerData(self):
        self.builder.loadDeformers()

    @QtCore.Slot()
    def _onSaveDeformerData(self):
        raise NotImplementedError

    @QtCore.Slot()
    def _setSkinFiles(self, filepath):
        if self.builder:
            self.builder.skinsFile = filepath

    @QtCore.Slot()
    def _setDeformLayerFile(self, filepath):
        if self.builder:
            self.builder.deformLayersFile = filepath

    @QtCore.Slot()
    def _setDeformerFiles(self, fileList):
        if self.builder:
            self.builder.deformerFiles = fileList