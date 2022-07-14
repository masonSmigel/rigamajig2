#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: actions.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
import sys
import os

# MAYA
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from shiboken2 import wrapInstance

# RIGAMJIG
import rigamajig2.maya.qc as qc
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
import rigamajig2.maya.rig_builder.builderUtils


class Actions(object):
    def __init__(self, dialog):
        """
        This class will setup the actions for the the builder Dialog. you must pass in the dialog as the self.dialog parameter
        :param dialog:
        """
        self.dialog = dialog
        self.create_actions()

    def create_actions(self):
        # FILE
        self.new_rig_file_action = QtWidgets.QAction("New Rig File", self.dialog)
        self.new_rig_file_action.setIcon(QtGui.QIcon(":fileNew.png"))
        self.new_rig_file_action.triggered.connect(self.create_rig_env)

        self.load_rig_file_action = QtWidgets.QAction("Load Rig File", self.dialog)
        self.load_rig_file_action.setIcon(QtGui.QIcon(":folder-open.png"))
        self.load_rig_file_action.triggered.connect(self.load_rig_file)

        self.reload_rig_file_action = QtWidgets.QAction("Reload Rig File", self.dialog)
        self.reload_rig_file_action.setIcon(QtGui.QIcon(":refresh.png"))
        self.reload_rig_file_action.triggered.connect(self.reload_rig_file)

        # UTILS
        self.reload_rigamajig_modules_action = QtWidgets.QAction("Reload Rigamajig2 Modules", self.dialog)
        self.reload_rigamajig_modules_action.triggered.connect(self.reload_rigamajig_modules)

        # TOOLS
        self.run_performance_test_action = QtWidgets.QAction("Run Performance Test", self.dialog)
        self.run_performance_test_action.triggered.connect(self.run_performace_test)

        self.generate_random_anim_action = QtWidgets.QAction("Generate Random Animation", self.dialog)
        self.generate_random_anim_action.triggered.connect(self.generate_random_anmation)

        # HELP
        self.show_documentation_action = QtWidgets.QAction("Documentation", self.dialog)
        self.show_documentation_action.triggered.connect(self.show_documentation)

        self.show_about_action = QtWidgets.QAction("About", self.dialog)
        self.show_about_action.triggered.connect(self.show_about)

    def create_rig_env(self):
        create_dialog = CreateRigEnvDialog()
        create_dialog.new_env_created.connect(self.dialog.set_rig_file)
        create_dialog.show_dialog()

    def load_rig_file(self):
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
        file_dialog.setNameFilters(["Rig Files (*.rig)"])

        fname = file_dialog.exec_()
        # new_path = cmds.fileDialog2(ds=2,
        #                             cap="Select a rig file",
        #                             ff="Rig Files (*.rig)",
        #                             fm=1,
        #                             kc='Select'
        #                             )

        print fname
        if file_dialog.selectedFiles():
            self.dialog.set_rig_file(file_dialog.selectedFiles()[0])

    def reload_rig_file(self):
        self.dialog.set_rig_file(self.dialog.rig_file)

    # TOOLS MENU
    def run_performace_test(self):
        qc.runPerformanceTest()

    def generate_random_anmation(self):
        qc.generateRandomAnim()

    def reload_rigamajig_modules(self):
        import rigamajig2
        rigamajig2.reloadModule(log=True)

    # SHOW HELP
    def show_documentation(self):
        pass

    def show_about(self):
        pass


class CreateRigEnvDialog(QtWidgets.QDialog):
    WINDOW_TITLE = "Create Rig Enviornment"

    new_env_created = QtCore.Signal(str)

    rig_file_result = None

    def show_dialog(self):
        self.exec_()

    def __init__(self):
        if sys.version_info.major < 3:
            maya_main_window = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            maya_main_window = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(CreateRigEnvDialog, self).__init__(maya_main_window)
        self.rig_env = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setFixedSize(375, 135)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        self.update_create_method()

    def create_widgets(self):

        self.from_archetype_rb = QtWidgets.QRadioButton("New From Archetype")
        self.from_existing_rb = QtWidgets.QRadioButton("Clone Existing")
        self.from_archetype_rb.setChecked(True)

        self.archetype_cb_widget = QtWidgets.QWidget()
        self.archetype_cb_widget.setFixedHeight(25)
        self.archetype_cb = QtWidgets.QComboBox()
        for archetype in rigamajig2.maya.rig_builder.builderUtils.get_available_archetypes():
            self.archetype_cb.addItem(archetype)

        self.src_path = pathSelector.PathSelector("Source:", fm=2)
        self.dst_path = pathSelector.PathSelector("New Env:", fm=2)
        self.rig_name_le = QtWidgets.QLineEdit()
        self.rig_name_le.setPlaceholderText("rig_name")

        self.create_btn = QtWidgets.QPushButton("Create")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")

    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        radio_button_layout = QtWidgets.QHBoxLayout()
        radio_button_layout.addSpacing(15)
        radio_button_layout.addWidget(self.from_archetype_rb)
        radio_button_layout.addWidget(self.from_existing_rb)

        archetype_cb_layout = QtWidgets.QHBoxLayout(self.archetype_cb_widget)
        archetype_cb_layout.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel("Archetype:")
        label.setFixedWidth(60)
        archetype_cb_layout.addWidget(label)
        archetype_cb_layout.addWidget(self.archetype_cb)

        rig_name_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Rig Name:")
        label.setFixedWidth(60)
        rig_name_layout.addWidget(label)
        rig_name_layout.addWidget(self.rig_name_le)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.create_btn)

        main_layout.addLayout(radio_button_layout)
        main_layout.addWidget(self.archetype_cb_widget)
        main_layout.addWidget(self.src_path)
        main_layout.addWidget(self.dst_path)
        main_layout.addLayout(rig_name_layout)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.from_archetype_rb.toggled.connect(self.update_create_method)
        self.from_existing_rb.toggled.connect(self.update_create_method)

        self.cancel_btn.clicked.connect(self.close)
        self.create_btn.clicked.connect(self.create_new_rig_env)

    def update_create_method(self):
        if self.from_archetype_rb.isChecked():
            self.archetype_cb_widget.setVisible(True)
            self.src_path.setVisible(False)
        else:
            self.archetype_cb_widget.setVisible(False)
            self.src_path.setVisible(True)

    def create_new_rig_env(self):

        dest_rig_env = self.dst_path.get_path()
        rig_name = self.rig_name_le.text()
        if self.from_archetype_rb.isChecked():
            archetype = self.archetype_cb.currentText()
            rig_file = rigamajig2.maya.rig_builder.builderUtils.new_rigenv_from_archetype(
                new_env=dest_rig_env,
                archetype=archetype,
                rig_name=rig_name)
        else:
            src_env = self.src_path.get_path()
            rig_file = rigamajig2.maya.rig_builder.builderUtils.create_rig_env(
                src_env=src_env,
                tgt_env=dest_rig_env,
                rig_name=rig_name)
        self.new_env_created.emit(rig_file)

        self.close()
