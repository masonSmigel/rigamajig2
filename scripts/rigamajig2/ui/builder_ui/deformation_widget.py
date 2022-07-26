#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: deformation_widget.py
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
from rigamajig2.ui.widgets import pathSelector, collapseableWidget
from rigamajig2.ui.builder_ui import constants
from rigamajig2.maya.rig_builder.builder import PSD, SKINS


class DeformationWidget(QtWidgets.QWidget):

    def __init__(self, builder=None):
        super(DeformationWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.main_collapseable_widget = collapseableWidget.CollapsibleWidget('Deformations', addCheckbox=True)

        self.skin_path_selector = pathSelector.PathSelector(
            "skin:",
            cap="Select the skin weight folder",
            ff=constants.JSON_FILTER,
            fm=2)
        self.load_all_skin_btn = QtWidgets.QPushButton("Load All Skins")
        self.load_single_skin_btn = QtWidgets.QPushButton("Load Skin")
        self.save_skin_btn = QtWidgets.QPushButton("Save Skin")

        self.skinEdit_wgt = collapseableWidget.CollapsibleWidget('Edit Skin Cluster')
        self.skinEdit_wgt.set_header_background_color(constants.EDIT_BG_HEADER_COLOR)
        self.skinEdit_wgt.set_widget_background_color(constants.EDIT_BG_WIDGET_COLOR)

        self.copySkinWeights_btn = QtWidgets.QPushButton("Copy Skin Weights and Influences")
        self.copySkinWeights_btn.setIcon(QtGui.QIcon(":copySkinWeight"))

        self.psd_path_selector = pathSelector.PathSelector(
            "psd:",
            cap="Select a Pose Reader File",
            ff=constants.JSON_FILTER,
            fm=1)
        self.load_psd_btn = QtWidgets.QPushButton("Load Pose Readers")
        self.save_psd_btn = QtWidgets.QPushButton("Save Pose Readers")

        self.load_psd_mode_cbox = QtWidgets.QComboBox()
        self.load_psd_mode_cbox.setFixedHeight(24)
        self.load_psd_mode_cbox.addItem("append")
        self.load_psd_mode_cbox.addItem("replace")

    def createLayouts(self):
        # setup the main layout.
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        skin_btn_layout = QtWidgets.QHBoxLayout()
        skin_btn_layout.setContentsMargins(0, 0, 0, 0)
        skin_btn_layout.setSpacing(4)
        skin_btn_layout.addWidget(self.load_all_skin_btn)
        skin_btn_layout.addWidget(self.load_single_skin_btn)
        skin_btn_layout.addWidget(self.save_skin_btn)

        self.main_collapseable_widget.addWidget(self.skin_path_selector)
        self.main_collapseable_widget.addLayout(skin_btn_layout)

        self.main_collapseable_widget.addWidget(self.skinEdit_wgt)
        self.skinEdit_wgt.addWidget(self.copySkinWeights_btn)
        self.skinEdit_wgt.addSpacing(4)

        psd_btn_layout = QtWidgets.QHBoxLayout()
        psd_btn_layout.setContentsMargins(0, 0, 0, 0)
        psd_btn_layout.setSpacing(4)
        psd_btn_layout.addWidget(self.load_psd_btn)
        psd_btn_layout.addWidget(self.save_psd_btn)
        psd_btn_layout.addWidget(self.load_psd_mode_cbox)

        # add widgets to the collapsable widget.
        self.main_collapseable_widget.addWidget(self.psd_path_selector)
        self.main_collapseable_widget.addLayout(psd_btn_layout)

        # add the widget to the main layout
        self.main_layout.addWidget(self.main_collapseable_widget)

    def createConnections(self):
        self.load_all_skin_btn.clicked.connect(self.load_all_skins)
        self.load_single_skin_btn.clicked.connect(self.load_single_skin)
        self.save_skin_btn.clicked.connect(self.save_skin)
        self.copySkinWeights_btn.clicked.connect(self.copySkinWeights)
        self.load_psd_btn.clicked.connect(self.load_posereaders)
        self.save_psd_btn.clicked.connect(self.save_posereaders)

    def setBuilder(self, builder):
        rigEnv = builder.get_rig_env()
        self.builder = builder
        self.skin_path_selector.set_relativeTo(rigEnv)
        self.psd_path_selector.set_relativeTo(rigEnv)

        # update data within the rig
        skinFile = self.builder.getRigData(self.builder.get_rig_file(), SKINS)
        if skinFile:
            self.skin_path_selector.set_path(skinFile)

        psdFile = self.builder.getRigData(self.builder.get_rig_file(), PSD)
        if psdFile:
            self.psd_path_selector.set_path(psdFile)

    def runWidget(self):
        self.load_posereaders()
        self.load_all_skins()

    @property
    def isChecked(self):
        return self.main_collapseable_widget.isChecked()

    # CONNECTIONS
    def load_all_skins(self):
        self.builder.load_skin_weights(self.skin_path_selector.get_abs_path())

    def load_single_skin(self):
        path = cmds.fileDialog2(ds=2, cap="Select a skin file", ff=JSON_FILTER, okc="Select",
                                dir=self.skin_path_selector.get_abs_path())
        if path:
            deform.load_single_skin(path[0])

    def save_skin(self):
        self.builder.save_skin_weights(path=self.skin_path_selector.get_abs_path())

    def load_posereaders(self):
        self.builder.load_poseReaders(self.psd_path_selector.get_abs_path(),
                                      replace=self.load_psd_mode_cbox.currentIndex())

    def save_posereaders(self):
        self.builder.save_poseReaders(self.psd_path_selector.get_abs_path())

    def copySkinWeights(self):
        import rigamajig2.maya.skinCluster as rig_skinCluster
        src = cmds.ls(sl=True)[0]
        dst = cmds.ls(sl=True)[1:]
        rig_skinCluster.copySkinClusterAndInfluences(src, dst)
