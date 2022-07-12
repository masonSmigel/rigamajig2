#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: model_widget.py
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
from rigamajig2.maya.rig_builder.builder import MODEL_FILE, PRE_SCRIPT


class ModelWidget(QtWidgets.QWidget):

    def __init__(self, builder=None):
        super(ModelWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.model_wdgt = collapseableWidget.CollapsibleWidget('Model/ Setup Scene', addCheckbox=True)
        self.model_path_selector = pathSelector.PathSelector(
            "model:",
            cap="Select a Model file",
            ff=constants.MAYA_FILTER,
            fm=1
            )
        self.import_model_btn = QtWidgets.QPushButton('Import Model')
        self.open_model_btn = QtWidgets.QPushButton('Open Model')
        self.open_model_btn.setFixedWidth(100)

        # pre script
        self.preScript_scriptRunner = scriptRunner.ScriptRunner(title="Pre-Scripts:")

    def createLayouts(self):
        # setup the main layout.
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.model_wdgt.addWidget(self.preScript_scriptRunner)

        # setup the button layout
        model_btn_layout = QtWidgets.QHBoxLayout()
        model_btn_layout.setContentsMargins(0, 0, 0, 0)
        model_btn_layout.setSpacing(4)
        model_btn_layout.addWidget(self.import_model_btn)
        model_btn_layout.addWidget(self.open_model_btn)

        # add widgets to the collapsable widget.
        self.model_wdgt.addWidget(self.model_path_selector)
        self.model_wdgt.addLayout(model_btn_layout)

        # add the widget to the main layout
        self.main_layout.addWidget(self.model_wdgt)

    def createConnections(self):
        self.import_model_btn.clicked.connect(self.import_model)
        self.open_model_btn.clicked.connect(self.open_model)

    def setBuilder(self, builder):
        rigEnv = builder.get_rig_env()
        rigFile = builder.get_rig_file()
        self.builder = builder
        self.model_path_selector.set_relativeTo(rigEnv)

        # clear the ui
        self.preScript_scriptRunner.clear_scripts()

        # update data within the rig
        modelFile = self.builder.get_rig_data(self.builder.get_rig_file(), MODEL_FILE)
        if modelFile:
            self.model_path_selector.set_path(modelFile)

        # update the script runner
        self.preScript_scriptRunner.set_relative_dir(rigEnv)
        for path in self.builder.get_rig_data(rigFile, PRE_SCRIPT):
            self.preScript_scriptRunner.add_scripts(self.builder._absPath(path))

    def runWidget(self):
        self.preScript_scriptRunner.execute_all_scripts()
        self.import_model()

    @property
    def isChecked(self):
        return self.model_wdgt.isChecked()

    # CONNECTIONS
    def import_model(self):
        self.builder.import_model(self.model_path_selector.get_abs_path())

    def open_model(self):
        cmds.file(self.model_path_selector.get_abs_path(), o=True, f=True)
