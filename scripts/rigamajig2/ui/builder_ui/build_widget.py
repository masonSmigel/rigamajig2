#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: builder_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
from rigamajig2.ui.builder_ui import constants
from rigamajig2.maya.rig_builder.builder import POST_SCRIPT
from rigamajig2.ui.builder_ui import controls_widget


class BuildWidget(QtWidgets.QWidget):

    def __init__(self, builder=None):
        super(BuildWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.main_collapseable_widget = collapseableWidget.CollapsibleWidget('Build Rig', addCheckbox=True)
        self.load_ctls_on_build = QtWidgets.QCheckBox("Load Ctls")
        self.load_ctls_on_build.setChecked(True)
        self.load_ctls_on_build.setFixedWidth(80)

        self.complete_build_btn = QtWidgets.QPushButton("Build Rig")
        self.complete_build_btn.setFixedHeight(45)

        self.build_btn = QtWidgets.QPushButton("Build")
        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.finalize_btn = QtWidgets.QPushButton("Finalize")

        # Post - script section
        self.postScript_scriptRunner = scriptRunner.ScriptRunner(title="Post-Scripts:")

    def createLayouts(self):
        # setup the main layout.
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        build_layout = QtWidgets.QHBoxLayout()
        build_layout.addWidget(self.build_btn)
        build_layout.addWidget(self.connect_btn)
        build_layout.addWidget(self.finalize_btn)

        # build_layout.addWidget(self.load_ctls_on_build)
        self.main_collapseable_widget.addWidget(self.complete_build_btn)
        self.main_collapseable_widget.addLayout(build_layout)

        # Post Script
        self.main_collapseable_widget.addSpacing()
        self.main_collapseable_widget.addWidget(self.postScript_scriptRunner)

        # add the widget to the main layout
        self.main_layout.addWidget(self.main_collapseable_widget)

    def createConnections(self):
        self.complete_build_btn.clicked.connect(self.complete_build)
        self.build_btn.clicked.connect(self.build_rig)
        self.connect_btn.clicked.connect(self.connect_rig)
        self.finalize_btn.clicked.connect(self.finalize_rig)

    def setBuilder(self, builder):
        rigEnv = builder.get_rig_env()
        rigFile = builder.get_rig_file()
        self.builder = builder

        # clear the ui
        self.postScript_scriptRunner.clear_scripts()

        self.postScript_scriptRunner.set_relative_dir(rigEnv)
        for path in self.builder.getRigData(rigFile, POST_SCRIPT):
            self.postScript_scriptRunner.add_scripts(self.builder._absPath(path))

    def runWidget(self):
        self.complete_build()
        self.postScript_scriptRunner.execute_all_scripts()

    @property
    def isChecked(self):
        return self.main_collapseable_widget.isChecked()

    # CONNECTIONS
    def initalize_rig(self):
        self.builder.initalize()

    def clear_components(self):
        self.builder.set_cmpts(list())

    def build_rig(self):
        self.builder.build()

    def connect_rig(self):
        self.builder.connect()

    def finalize_rig(self):
        self.builder.finalize()

    def complete_build(self):
        self.builder.initalize()
        self.builder.load_component_settings()
        self.builder.build()
        self.builder.connect()
        self.builder.finalize()
        # self.cmpt_manager.load_cmpts_from_scene()
