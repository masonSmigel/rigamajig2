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
from rigamajig2.maya.builder.builder import MODEL_FILE, PRE_SCRIPT


class ModelWidget(QtWidgets.QWidget):

    def __init__(self, builder=None):
        super(ModelWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.mainCollapseableWidget  = collapseableWidget.CollapsibleWidget('Model/ Setup Scene', addCheckbox=True)
        self.model_path_selector = pathSelector.PathSelector(
            "model:",
            caption="Select a Model file",
            fileFilter=constants.MAYA_FILTER,
            fileMode=1
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

        self.mainCollapseableWidget .addWidget(self.preScript_scriptRunner)

        # setup the button layout
        model_btn_layout = QtWidgets.QHBoxLayout()
        model_btn_layout.setContentsMargins(0, 0, 0, 0)
        model_btn_layout.setSpacing(4)
        model_btn_layout.addWidget(self.import_model_btn)
        model_btn_layout.addWidget(self.open_model_btn)

        # add widgets to the collapsable widget.
        self.mainCollapseableWidget .addSpacing(10)
        self.mainCollapseableWidget .addWidget(self.model_path_selector)
        self.mainCollapseableWidget .addLayout(model_btn_layout)

        # add the widget to the main layout
        self.main_layout.addWidget(self.mainCollapseableWidget )

    def createConnections(self):
        self.import_model_btn.clicked.connect(self.import_model)
        self.open_model_btn.clicked.connect(self.open_model)

    def setBuilder(self, builder):
        rigEnv = builder.getRigEnviornment()
        rigFile = builder.getRigFile()
        self.builder = builder
        self.model_path_selector.setRelativePath(rigEnv)

        # clear the ui
        self.preScript_scriptRunner.clearScript()

        # update data within the rig
        modelFile = self.builder.getRigData(self.builder.getRigFile(), MODEL_FILE)
        if modelFile:
            self.model_path_selector.setPath(modelFile)

        # update the script runner
        self.preScript_scriptRunner.setRelativeDirectory(rigEnv)
        for path in self.builder.getRigData(rigFile, PRE_SCRIPT):
            self.preScript_scriptRunner.addScripts(self.builder.getAbsoultePath(path))

    def runWidget(self):
        self.preScript_scriptRunner.executeAllScripts()
        self.import_model()

    @property
    def isChecked(self):
        return self.mainCollapseableWidget .isChecked()

    # CONNECTIONS
    def import_model(self):
        self.builder.importModel(self.model_path_selector.getPath())

    def open_model(self):
        cmds.file(self.model_path_selector.getPath(), o=True, f=True)
