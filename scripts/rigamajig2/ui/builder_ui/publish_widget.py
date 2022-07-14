#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: publish_widget.py
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
from rigamajig2.maya.rig_builder.builder import OUTPUT_RIG, OUTPUT_RIG_FILE_TYPE, PUB_SCRIPT


class PublishWidget(QtWidgets.QWidget):

    def __init__(self, builder=None):
        super(PublishWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.main_collapseable_widget = collapseableWidget.CollapsibleWidget('Publish', addCheckbox=True)
        self.publishScript_scriptRunner = scriptRunner.ScriptRunner(title="Publish-Scripts:")
        self.out_path_selector = pathSelector.PathSelector("out file:", cap="Select a location to save", ff=constants.MAYA_FILTER,
                                                           fm=2)
        self.pub_btn = QtWidgets.QPushButton("Publish Rig")
        self.pub_btn.setFixedHeight(constants.LARGE_BTN_HEIGHT)

        self.out_file_type_cb = QtWidgets.QComboBox()
        self.out_file_type_cb.addItem('ma')
        self.out_file_type_cb.addItem('mb')

        self.run_selected_btn = QtWidgets.QPushButton("Run Selected")
        self.run_btn = QtWidgets.QPushButton("Run")
        self.run_btn.setFixedWidth(80)

        self.close_btn = QtWidgets.QPushButton("Close")

    def createLayouts(self):
        # setup the main layout.
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.main_collapseable_widget.addWidget(self.publishScript_scriptRunner)
        publish_file_layout = QtWidgets.QHBoxLayout()
        publish_file_layout.addWidget(self.out_path_selector)
        publish_file_layout.addWidget(self.out_file_type_cb)
        self.main_collapseable_widget.addLayout(publish_file_layout)
        self.main_collapseable_widget.addWidget(self.pub_btn)

        self.main_layout.addWidget(self.main_collapseable_widget)

    def createConnections(self):
        self.pub_btn.clicked.connect(self.publish)

    def setBuilder(self, builder):
        rigEnv = builder.get_rig_env()
        rigFile = builder.get_rig_file()
        self.builder = builder
        self.out_path_selector.set_relativeTo(rigEnv)

        # clear the ui
        self.publishScript_scriptRunner.clear_scripts()

        # update data within the rig
        outFile = self.builder.get_rig_data(self.builder.get_rig_file(), OUTPUT_RIG)
        if outFile:
            self.out_path_selector.set_path(outFile)

        # update the script runner
        self.publishScript_scriptRunner.set_relative_dir(rigEnv)
        for path in self.builder.get_rig_data(rigFile, PUB_SCRIPT):
            self.publishScript_scriptRunner.add_scripts(self.builder._absPath(path))

        # set the default output file type
        file_type_text = self.builder.get_rig_data(rigFile, OUTPUT_RIG_FILE_TYPE)
        index = self.out_file_type_cb.findText(file_type_text, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.out_file_type_cb.setCurrentIndex(index)

    def runWidget(self):
        self.publishScript_scriptRunner.execute_all_scripts()

    @property
    def isChecked(self):
        return self.main_collapseable_widget.isChecked()

    # CONNECTIONS
    def publish(self):
        confirm_pub_msg = QtWidgets.QMessageBox()
        confirm_pub_msg.setText("Publish the rig")
        confirm_pub_msg.setInformativeText(
            "Proceeding will rebuild a fresh rig from saved data overwriting any existing any published rigs.")
        confirm_pub_msg.setStandardButtons(
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
        confirm_pub_msg.setDefaultButton(QtWidgets.QMessageBox.Save)
        res = confirm_pub_msg.exec_()

        if res == QtWidgets.QMessageBox.Save:
            outputfile = self.out_path_selector.get_abs_path()
            fileType = self.out_file_type_cb.currentText()

            self.builder.run(publish=True, outputfile=outputfile, assetName=None, fileType=fileType)
