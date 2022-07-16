#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: dialog.py
    author: masonsmigel
    date: 07/2022
    discription: This module contains the main dialog for the builder UI

"""
# PYTHON
import sys
import time
import logging
import os
from collections import OrderedDict

# MAYA
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

# RIGAMAJIG
import rigamajig2.maya.rig_builder.builder
import rigamajig2.maya.rig_builder.builderUtils
import rigamajig2.shared.common as common
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
from rigamajig2.ui.builder_ui import model_widget
from rigamajig2.ui.builder_ui import joint_widget
from rigamajig2.ui.builder_ui import controls_widget
from rigamajig2.ui.builder_ui import deformation_widget
from rigamajig2.ui.builder_ui import initalize_widget
from rigamajig2.ui.builder_ui import build_widget
from rigamajig2.ui.builder_ui import publish_widget
from rigamajig2.ui.builder_ui import actions

import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.rig_builder.deform as deform

logger = logging.getLogger(__name__)
logger.setLevel(5)

MAYA_FILTER = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
JSON_FILTER = "Json Files (*.json)"

LARGE_BTN_HEIGHT = 35
EDIT_BG_WIDGET_COLOR = QtGui.QColor(70, 70, 80)


class BuilderDialog(QtWidgets.QDialog):
    WINDOW_TITLE = "Rigamajig2 Builder"

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = BuilderDialog()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self):
        if sys.version_info.major < 3:
            maya_main_window = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            maya_main_window = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(BuilderDialog, self).__init__(maya_main_window)
        self.rig_env = None
        self.rig_builder = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(380, 825)

        self.create_menus()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_menus(self):
        """create menu actions"""
        self.main_menu = QtWidgets.QMenuBar()

        file_menu = self.main_menu.addMenu("File")
        self.actions = actions.Actions(self)
        file_menu.addAction(self.actions.new_rig_file_action)
        file_menu.addAction(self.actions.load_rig_file_action)
        # file_menu.addAction(self.save_rig_file_action)
        file_menu.addSeparator()
        file_menu.addAction(self.actions.reload_rig_file_action)

        utils_menu = self.main_menu.addMenu("Utils")
        utils_menu.addAction(self.actions.reload_rigamajig_modules_action)

        qc_menu = self.main_menu.addMenu("QC")
        qc_menu.addAction(self.actions.run_performance_test_action)
        qc_menu.addAction(self.actions.generate_random_anim_action)

        help_menu = self.main_menu.addMenu("Help")
        help_menu.addAction(self.actions.show_documentation_action)
        help_menu.addAction(self.actions.show_about_action)

    def create_widgets(self):
        self.rig_path_selector = pathSelector.PathSelector(cap='Select a Rig File', ff="Rig Files (*.rig)", fm=1)

        self.create_new_rigenv = QtWidgets.QPushButton("New Rig Env")
        self.create_new_rigenv.setToolTip("Create a new rig enviornment")

        self.asset_name_le = QtWidgets.QLineEdit()
        self.asset_name_le.setPlaceholderText("asset_name")

        self.main_widgets = list()

        self.model_widget = model_widget.ModelWidget(self.rig_builder)
        self.joint_widget = joint_widget.JointWidget(self.rig_builder)
        self.controls_widget = controls_widget.ControlsWidget(self.rig_builder)
        self.initialize_widget = initalize_widget.InitializeWidget(self.rig_builder)
        self.build_widget = build_widget.BuildWidget(self.rig_builder)
        self.deformation_widget = deformation_widget.DeformationWidget(self.rig_builder)
        self.publish_widget = publish_widget.PublishWidget(self.rig_builder)

        self.main_widgets = [self.model_widget,
                             self.joint_widget,
                             self.initialize_widget,
                             self.build_widget,
                             self.controls_widget,
                             self.deformation_widget,
                             self.publish_widget]

        self.run_selected_btn = QtWidgets.QPushButton(QtGui.QIcon(":execute.png"), "Run Selected")
        self.run_btn = QtWidgets.QPushButton(QtGui.QIcon(":executeAll.png"), "Run")
        self.run_btn.setFixedWidth(80)

        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layouts(self):

        rig_char_name_layout = QtWidgets.QHBoxLayout()
        rig_char_name_layout.addWidget(QtWidgets.QLabel("Rig Name:"))
        rig_char_name_layout.addWidget(self.asset_name_le)
        rig_char_name_layout.addWidget(self.create_new_rigenv)

        rig_env_layout = QtWidgets.QVBoxLayout()
        rig_env_layout.addWidget(self.rig_path_selector)
        rig_env_layout.addLayout(rig_char_name_layout)

        # add the collapseable widgets
        build_layout = QtWidgets.QVBoxLayout()
        build_layout.addWidget(self.model_widget)
        build_layout.addWidget(self.joint_widget)
        build_layout.addWidget(self.initialize_widget)
        build_layout.addWidget(self.build_widget)
        build_layout.addWidget(self.controls_widget)
        build_layout.addWidget(self.deformation_widget)
        build_layout.addWidget(self.publish_widget)
        build_layout.addStretch()

        # groups
        rig_env_grp = QtWidgets.QGroupBox('Rig Enviornment')
        rig_env_grp.setLayout(rig_env_layout)

        build_grp = QtWidgets.QGroupBox('Build')
        build_grp.setLayout(build_layout)

        # lower persistant buttons (AKA close)
        low_buttons_layout = QtWidgets.QVBoxLayout()
        run_buttons_layout = QtWidgets.QHBoxLayout()
        run_buttons_layout.addWidget(self.run_selected_btn)
        run_buttons_layout.addWidget(self.run_btn)

        low_buttons_layout.addLayout(run_buttons_layout)
        low_buttons_layout.addWidget(self.close_btn)

        # scrollable area
        body_wdg = QtWidgets.QWidget()
        body_layout = QtWidgets.QVBoxLayout(body_wdg)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(rig_env_grp)
        body_layout.addWidget(build_grp)

        body_scroll_area = QtWidgets.QScrollArea()
        body_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        body_scroll_area.setWidgetResizable(True)
        body_scroll_area.setWidget(body_wdg)

        # main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        main_layout.setMenuBar(self.main_menu)
        main_layout.addWidget(body_scroll_area)
        main_layout.addLayout(low_buttons_layout)

    def create_connections(self):

        # setup each widget with a connection to uncheck all over widgets when one is checked.
        # This ensures all setups until a breakpoint are run
        self.model_widget.main_collapseable_widget.header_wdg.checkbox.clicked.connect(lambda x:self.update_widget_checks(self.model_widget))
        self.joint_widget.main_collapseable_widget.header_wdg.checkbox.clicked.connect(lambda x:self.update_widget_checks(self.joint_widget))
        self.initialize_widget.main_collapseable_widget.header_wdg.checkbox.clicked.connect(lambda x:self.update_widget_checks(self.initialize_widget))
        self.build_widget.main_collapseable_widget.header_wdg.checkbox.clicked.connect(lambda x:self.update_widget_checks(self.build_widget))
        self.controls_widget.main_collapseable_widget.header_wdg.checkbox.clicked.connect(lambda x:self.update_widget_checks(self.controls_widget))
        self.deformation_widget.main_collapseable_widget.header_wdg.checkbox.clicked.connect(lambda x:self.update_widget_checks(self.deformation_widget))
        self.publish_widget.main_collapseable_widget.header_wdg.checkbox.clicked.connect(lambda x:self.update_widget_checks(self.publish_widget))

        self.rig_path_selector.select_path_btn.clicked.connect(self.path_selector_load_rig_file)
        self.create_new_rigenv.clicked.connect(self.actions.create_rig_env)
        self.run_selected_btn.clicked.connect(self.run_selected)
        self.run_btn.clicked.connect(self.run_all)
        self.close_btn.clicked.connect(self.close)

    # --------------------------------------------------------------------------------
    # Connections
    # --------------------------------------------------------------------------------

    def path_selector_load_rig_file(self):
        new_path = self.rig_path_selector.get_abs_path()
        if new_path:
            self.set_rig_file(new_path)

    def set_rig_file(self, path=None):
        self.rig_path_selector.select_path(path=path)
        file_info = QtCore.QFileInfo(self.rig_path_selector.get_abs_path())
        self.rig_env = file_info.path()
        self.rig_file = file_info.filePath()

        self.rig_builder = rigamajig2.maya.rig_builder.builder.Builder(self.rig_file)

        if not self.rig_file:
            return

        # setup ui Data
        rigName = rigamajig2.maya.rig_builder.builder.RIG_NAME
        self.asset_name_le.setText(self.rig_builder.get_rig_data(self.rig_file, rigName))

        # set paths and widgets relative to the rig env
        for widget in self.main_widgets:
            widget.setBuilder(builder=self.rig_builder)

    # BULDER FUNCTIONS
    def update_widget_checks(self, selectedWidget):
        """ This function ensures only one build step is selected at a time. it is run whenever a checkbox is toggled."""
        for widget in self.main_widgets:
            if widget is not selectedWidget:
                widget.main_collapseable_widget.set_checked(False)

    def run_selected(self):
        """run selected steps"""

        # ensure at least one breakpoint is selected
        breakpointSelected = False
        for widget in self.main_widgets:
            if widget.main_collapseable_widget.isChecked():
                breakpointSelected = True

        if not breakpointSelected:
            logger.error("No breakpoint selected no steps to run")
            return

        startTime = time.time()

        # because widgets are added to the ui and the list in oder they can be run sequenctially.
        # when we hit a widget that is checked then the loop stops.
        for widget in self.main_widgets:
            widget.runWidget()

            if widget.isChecked:
                break

        runTime = time.time() - startTime
        print("Time Elapsed: {}".format(str(runTime)))

    def run_all(self):
        self.rig_builder.run()
        self.initialize_widget.cmpt_manager.load_cmpts_from_scene()

    def closeEvent(self, e):
        super(BuilderDialog, self).closeEvent(e)
        self.initialize_widget.cmpt_manager.set_scriptjob_enabled(False)


if __name__ == '__main__':

    try:
        rigamajig_builder_dialog.close()
        rigamajig_builder_dialog.deleteLater()
    except:
        pass

    rigamajig_builder_dialog = BuilderDialog()
    rigamajig_builder_dialog.show()

    rigamajig_builder_dialog.set_rig_file(
        path='/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/biped.rig')
