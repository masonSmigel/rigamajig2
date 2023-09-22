#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: widget_deformation.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# MAYA
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
import rigamajig2.maya.builder.constants
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui.widgets import pathSelector, builderHeader, dataLoader
from rigamajig2.ui.builder_ui import style
from rigamajig2.maya.builder.constants import SKINS, PSD, SHAPES, DEFORMERS, DEFORM_LAYERS, DEFORMER_DATA_TYPES
from rigamajig2.maya.rig import deformLayer
from rigamajig2.maya import skinCluster


class DeformationWidget(QtWidgets.QWidget):
    """ Deformation layout for the builder UI """

    def __init__(self, builder=None):
        """
       Constructor for the deformation widget
       :param builder: builder to connect to the ui
       """
        super(DeformationWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets"""
        self.mainCollapseableWidget = builderHeader.BuilderHeader('Deformations', addCheckbox=True)

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
        # setup the main layout.
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        deformLayerLayout = QtWidgets.QHBoxLayout()
        deformLayerLayout.setContentsMargins(0, 0, 0, 0)
        deformLayerLayout.setSpacing(4)
        deformLayerLayout.addWidget(self.loadDeformLayersButton)
        deformLayerLayout.addWidget(self.saveDeformLayersButton)
        deformLayerLayout.addWidget(self.manageDeformLayersButton)

        # add the deformation layers back to the collapseable widget
        self.mainCollapseableWidget.addWidget(self.deformLayerPathSelector)
        self.mainCollapseableWidget.addLayout(deformLayerLayout)

        self.mainCollapseableWidget.addSpacing(10)

        skinButtonLayout = QtWidgets.QHBoxLayout()
        skinButtonLayout.setContentsMargins(0, 0, 0, 0)
        skinButtonLayout.setSpacing(4)
        skinButtonLayout.addWidget(self.loadAllSkinButton)
        skinButtonLayout.addWidget(self.loadSingleSkinButton)
        skinButtonLayout.addWidget(self.saveSkinsButton)

        # add the skin layers back to the collapseable widget
        self.mainCollapseableWidget.addWidget(self.skinPathSelector)
        self.mainCollapseableWidget.addLayout(skinButtonLayout)

        self.mainCollapseableWidget.addWidget(self.skinEditWidget)
        self.skinEditWidget.addWidget(self.copySkinWeightsButton)
        self.skinEditWidget.addWidget(self.connectBpmsButton)
        self.skinEditWidget.addSpacing(4)

        self.mainCollapseableWidget.addSpacing(10)
        # self.mainCollapseableWidget.addWidget(self.SHAPESPathSelector)

        # SHAPES layout
        deformersButtonLayout = QtWidgets.QHBoxLayout()
        deformersButtonLayout.setContentsMargins(0, 0, 0, 0)
        deformersButtonLayout.setSpacing(4)
        deformersButtonLayout.addWidget(self.loadDeformersButton)
        deformersButtonLayout.addWidget(self.saveDeformersButton)

        self.mainCollapseableWidget.addWidget(self.deformersDataLoader)
        self.mainCollapseableWidget.addLayout(deformersButtonLayout)

        # add the widget to the main layout
        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections"""
        self.loadDeformLayersButton.clicked.connect(self.loadDeformLayers)
        self.saveDeformLayersButton.clicked.connect(self.saveDeformLayers)
        self.manageDeformLayersButton.clicked.connect(self.openDeformLayerDialog)

        self.loadAllSkinButton.clicked.connect(self.loadAllSkins)
        self.loadSingleSkinButton.clicked.connect(self.loadSingleSkin)
        self.saveSkinsButton.clicked.connect(self.saveSkin)
        self.copySkinWeightsButton.clicked.connect(self.copySkinWeights)
        self.connectBpmsButton.clicked.connect(self.connectBindPreMatrix)
        self.saveDeformersButton.clicked.connect(self.saveDeformerData)
        self.loadDeformersButton.clicked.connect(self.loadDeformerData)

    def setBuilder(self, builder):
        """ Set a builder for intialize widget"""
        rigEnv = builder.getRigEnviornment()
        self.builder = builder
        self.deformLayerPathSelector.setRelativePath(rigEnv)
        self.skinPathSelector.setRelativePath(rigEnv)

        self.deformersDataLoader.clear()
        self.deformersDataLoader.setRelativePath(rigEnv)

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

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.builder.loadDeformationLayers(self.deformLayerPathSelector.getPath())
        self.builder.loadSkinWeights(self.skinPathSelector.getPath())
        self.builder.loadDeformers(self.deformersDataLoader.getFileList())

    @property
    def isChecked(self):
        """ Check it the widget is checked"""
        return self.mainCollapseableWidget.isChecked()

    # CONNECTIONS
    @QtCore.Slot()
    def loadDeformLayers(self):
        """ Save load pose reader setup from json using the builder """
        self.builder.loadDeformationLayers(self.deformLayerPathSelector.getPath())

    @QtCore.Slot()
    def saveDeformLayers(self):
        """ Save pose reader setup to json using the builder """
        self.builder.saveDeformationLayers(self.deformLayerPathSelector.getPath())

    @QtCore.Slot()
    def openDeformLayerDialog(self):
        from rigamajig2.ui.builder_ui import deformLayerDialog
        dialogInstance = deformLayerDialog.DeformLayerDialog()
        dialogInstance.show()

    @QtCore.Slot()
    def loadAllSkins(self):
        """Load all skin weights in the given folder"""
        self.builder.loadSkinWeights(self.skinPathSelector.getPath())

    @QtCore.Slot()
    def loadSingleSkin(self):
        """Load a single skin file"""
        import rigamajig2.maya.builder.data
        path = cmds.fileDialog2(dialogStyle=2,
                                caption="Select a skin file",
                                fileFilter=common.JSON_FILTER,
                                okc="Select",
                                dir=self.skinPathSelector.getPath())
        if path:
            rigamajig2.maya.builder.data.loadSingleSkin(path[0])

    @QtCore.Slot()
    def saveSkin(self):
        """Save the skin weights"""
        self.builder.saveSkinWeights(path=self.skinPathSelector.getPath())

    @QtCore.Slot()
    def copySkinWeights(self):
        """ Copy Skin weights"""
        src = cmds.ls(sl=True)[0]
        dst = cmds.ls(sl=True)[1:]
        skinCluster.copySkinClusterAndInfluences(src, dst)

    @QtCore.Slot()
    def connectBindPreMatrix(self):
        """
        Connect influence joints to their respective bindPreMatrix
        """
        for mesh in cmds.ls(sl=True):
            sc = skinCluster.getSkinCluster(mesh)
            skinCluster.connectExistingBPMs(sc)

    @QtCore.Slot()
    def loadDeformerData(self):
        self.builder.loadDeformers(self.deformersDataLoader.getFileList(absolute=False))

    @QtCore.Slot()
    def saveDeformerData(self):
        raise NotImplementedError

