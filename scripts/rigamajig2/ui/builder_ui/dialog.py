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
import rigamajig2.maya.rig_builder.builderUtils
import rigamajig2.shared.common as common
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
from rigamajig2.ui.builder_ui import model_widget, joint_widget, controls_widget, deformation_widget, initalize_widget, build_widget, publish_widget
import rigamajig2.maya.rig_builder.builder as cmptBuilder
import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.rig_builder.deform as deform

logger = logging.getLogger(__name__)
logger.setLevel(5)

MAYA_FILTER = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
JSON_FILTER = "Json Files (*.json)"

LARGE_BTN_HEIGHT = 35
EDIT_BG_WIDGET_COLOR = QtGui.QColor(70, 70, 80)


class BuilderUi(QtWidgets.QDialog):
    WINDOW_TITLE = "Rigamajig2 Builder"

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = BuilderUi()

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

        super(BuilderUi, self).__init__(maya_main_window)
        self.rig_env = None
        self.rig_builder = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(380, 825)

        self.create_actions()
        self.create_menus()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_actions(self):
        # FILE
        self.new_rig_file_action = QtWidgets.QAction("New Rig File", self)
        self.new_rig_file_action.setIcon(QtGui.QIcon(":fileNew.png"))
        self.new_rig_file_action.triggered.connect(self.create_rig_env)

        self.load_rig_file_action = QtWidgets.QAction("Load Rig File", self)
        self.load_rig_file_action.setIcon(QtGui.QIcon(":folder-open.png"))
        self.load_rig_file_action.triggered.connect(self.load_rig_file)

        self.save_rig_file_action = QtWidgets.QAction("Save Rig File", self)
        self.save_rig_file_action.setIcon(QtGui.QIcon(":save.png"))
        self.save_rig_file_action.triggered.connect(self.save_rig_file)

        self.reload_rig_file_action = QtWidgets.QAction("Reload Rig File", self)
        self.reload_rig_file_action.setIcon(QtGui.QIcon(":refresh.png"))
        self.reload_rig_file_action.triggered.connect(self.reload_rig_file)

        # UTILS
        self.reload_rigamajig_modules_action = QtWidgets.QAction("Reload Rigamajig2 Modules", self)
        self.reload_rigamajig_modules_action.triggered.connect(self.reload_rigamajig_modules)

        # TOOLS
        self.run_performance_test_action = QtWidgets.QAction("Run Performance Test", self)
        self.run_performance_test_action.triggered.connect(self.run_performace_test)

        self.generate_random_anim_action = QtWidgets.QAction("Generate Random Animation", self)
        self.generate_random_anim_action.triggered.connect(self.generate_random_anmation)

        # HELP
        self.show_documentation_action = QtWidgets.QAction("Documentation", self)
        self.show_documentation_action.triggered.connect(self.show_documentation)

        self.show_about_action = QtWidgets.QAction("About", self)
        self.show_about_action.triggered.connect(self.show_about)

    def create_menus(self):
        """create menu actions"""
        self.main_menu = QtWidgets.QMenuBar()

        file_menu = self.main_menu.addMenu("File")
        file_menu.addAction(self.new_rig_file_action)
        file_menu.addAction(self.load_rig_file_action)
        file_menu.addAction(self.save_rig_file_action)
        file_menu.addSeparator()
        file_menu.addAction(self.reload_rig_file_action)

        utils_menu = self.main_menu.addMenu("Utils")
        utils_menu.addAction(self.reload_rigamajig_modules_action)

        qc_menu = self.main_menu.addMenu("QC")
        qc_menu.addAction(self.run_performance_test_action)
        qc_menu.addAction(self.generate_random_anim_action)

        help_menu = self.main_menu.addMenu("Help")
        help_menu.addAction(self.show_documentation_action)
        help_menu.addAction(self.show_about_action)

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

        # # Pre- script section
        # self.preScript_wdgt = collapseableWidget.CollapsibleWidget('Setup Scene', addCheckbox=True)
        # self.preScript_scriptRunner = scriptRunner.ScriptRunner()

        # Component Section
        # self.cmpt_path_selector = pathSelector.PathSelector("cmpts:", cap="Select a Component File", ff=JSON_FILTER,
        #                                                     fm=1)
        # self.load_components_btn = QtWidgets.QPushButton("Load Cmpts")
        # self.append_components_btn = QtWidgets.QPushButton("Append Cmpts")
        # self.save_components_btn = QtWidgets.QPushButton("Save Cmpts")
        # self.save_components_btn.setIcon(QtGui.QIcon(":save.png"))
        # self.add_components_btn = QtWidgets.QPushButton("Add Components")
        # self.add_components_btn.setIcon(QtGui.QIcon(":freeformOff.png"))
        # self.cmpt_manager = componentManager.ComponentManager()
        #
        # self.initalize_build_btn = QtWidgets.QPushButton("Initalize Build")
        # self.initalize_build_btn.setFixedHeight(LARGE_BTN_HEIGHT)
        # self.guide_path_selector = pathSelector.PathSelector("guides:", cap="Select a guide file", ff=JSON_FILTER, fm=1)
        # self.load_guides_btn = QtWidgets.QPushButton("Load Guides")
        # self.save_guides_btn = QtWidgets.QPushButton("Save Guides")

        # self.load_ctls_on_build = QtWidgets.QCheckBox("Load Ctls")
        # self.load_ctls_on_build.setChecked(True)
        # self.load_ctls_on_build.setFixedWidth(80)
        #
        # self.complete_build_btn = QtWidgets.QPushButton("Build Rig")
        # self.complete_build_btn.setFixedHeight(45)
        #
        # # Post - script section
        # self.postScript_wdgt = collapseableWidget.CollapsibleWidget('Post-Script', addCheckbox=True)
        # self.postScript_scriptRunner = scriptRunner.ScriptRunner()

        # Publish Section
        # self.publish_wdgt = collapseableWidget.CollapsibleWidget('Publish', addCheckbox=True)
        # self.publishScript_scriptRunner = scriptRunner.ScriptRunner()
        # self.out_path_selector = pathSelector.PathSelector("out file:", cap="Select a location to save", ff=MAYA_FILTER,
        #                                                    fm=2)
        # self.pub_btn = QtWidgets.QPushButton("Publish Rig")
        # self.pub_btn.setFixedHeight(LARGE_BTN_HEIGHT)
        #
        # self.out_file_type_cb = QtWidgets.QComboBox()
        # self.out_file_type_cb.addItem('ma')
        # self.out_file_type_cb.addItem('mb')

        self.run_selected_btn = QtWidgets.QPushButton("Run Selected")
        self.run_btn = QtWidgets.QPushButton("Run")
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

        # prescript
        # self.preScript_wdgt.addWidget(self.preScript_scriptRunner)

        # Components
        # build_layout = QtWidgets.QHBoxLayout()

        # self.cmpt_wdgt.addLayout(build_layout)
        # build_layout.addWidget(self.load_ctls_on_build)
        # build_layout.addWidget(self.complete_build_btn)
        #
        # # Post Script
        # self.postScript_wdgt.addWidget(self.postScript_scriptRunner)

        # Publish
        # self.publish_wdgt.addWidget(self.publishScript_scriptRunner)
        # publish_file_layout = QtWidgets.QHBoxLayout()
        # publish_file_layout.addWidget(self.out_path_selector)
        # publish_file_layout.addWidget(self.out_file_type_cb)
        # self.publish_wdgt.addLayout(publish_file_layout)
        # self.publish_wdgt.addWidget(self.pub_btn)

        # add the collapseable widgets
        build_layout = QtWidgets.QVBoxLayout()
        # build_layout.addWidget(self.preScript_wdgt)
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
        self.rig_path_selector.select_path_btn.clicked.connect(self.path_selector_load_rig_file)
        self.create_new_rigenv.clicked.connect(self.create_rig_env)
        self.run_selected_btn.clicked.connect(self.run_selected)
        self.run_btn.clicked.connect(self.run_all)
        self.close_btn.clicked.connect(self.close)

    # --------------------------------------------------------------------------------
    # Connections
    # --------------------------------------------------------------------------------

    def load_rig_file(self):
        new_path = cmds.fileDialog2(ds=2, cap="Select a rig file", ff="Rig Files (*.rig)", fm=1, okc='Select',
                                    dir=self.rig_env)
        if new_path:
            self.set_rig_file(new_path[0])

    def path_selector_load_rig_file(self):
        new_path = self.rig_path_selector.get_abs_path()
        if new_path:
            self.set_rig_file(new_path)

    def save_rig_file(self):
        """
        Save out a rig file
        :return:
        """
        data = abstract_data.AbstractData()
        data.read(self.rig_file)
        new_data = data.getData()

        # Save the main feilds
        new_data[cmptBuilder.RIG_NAME] = self.asset_name_le.text()
        new_data[cmptBuilder.PRE_SCRIPT] = self.preScript_scriptRunner.get_current_script_list(relative_paths=True)
        new_data[cmptBuilder.POST_SCRIPT] = self.postScript_scriptRunner.get_current_script_list(relative_paths=True)
        new_data[cmptBuilder.PUB_SCRIPT] = self.publishScript_scriptRunner.get_current_script_list(relative_paths=True)
        new_data[cmptBuilder.MODEL_FILE] = self.model_path_selector.get_path()
        new_data[cmptBuilder.SKELETON_FILE] = self.skel_path_selector.get_path()
        new_data[cmptBuilder.SKELETON_POS] = self.joint_pos_path_selector.get_path()
        new_data[cmptBuilder.GUIDES] = self.guide_path_selector.get_path()
        new_data[cmptBuilder.COMPONENTS] = self.cmpt_path_selector.get_path()
        new_data[cmptBuilder.CONTROL_SHAPES] = self.ctl_path_selector.get_path()
        new_data[cmptBuilder.SKINS] = self.skin_path_selector.get_path()
        new_data[cmptBuilder.PSD] = self.psd_path_selector.get_path()
        new_data[cmptBuilder.OUTPUT_RIG] = self.out_path_selector.get_path()
        new_data[cmptBuilder.OUTPUT_RIG_FILE_TYPE] = self.out_file_type_cb.currentText()

        data.setData(new_data)
        data.write(self.rig_file)
        logger.info("data saved to : {}".format(self.rig_file))

    def reload_rig_file(self):
        self.set_rig_file(self.rig_file)

    def show_documentation(self):
        pass

    def show_about(self):
        pass

    def set_rig_file(self, path=None):
        self.rig_path_selector.select_path(path=path)
        file_info = QtCore.QFileInfo(self.rig_path_selector.get_abs_path())
        self.rig_env = file_info.path()
        self.rig_file = file_info.filePath()

        # set all path selectors to be realive to the new rig enviornment

        # self.cmpt_path_selector.set_relativeTo(self.rig_env)
        # self.guide_path_selector.set_relativeTo(self.rig_env)
        # self.ctl_path_selector.set_relativeTo(self.rig_env)
        # self.skin_path_selector.set_relativeTo(self.rig_env)
        # self.psd_path_selector.set_relativeTo(self.rig_env)
        # self.out_path_selector.set_relativeTo(self.rig_env)

        self.rig_builder = cmptBuilder.Builder(self.rig_file)
        # self.cmpt_manager.set_rig_builder(self.rig_builder)
        self.update_ui_with_rig_data()

    def update_ui_with_rig_data(self):
        if not self.rig_file:
            return

        # set the character name
        self.asset_name_le.setText(self.rig_builder.get_rig_data(self.rig_file, cmptBuilder.RIG_NAME))

        # loadSettings prescripts, postscripts and pubscripts from file or rig_env
        # self.reload_prescripts()
        # self.reload_postscripts()
        # self.reload_pubscripts()

        # set rig paths
        for widget in self.main_widgets:
            widget.setBuilder(builder=self.rig_builder)

        # self.model_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.MODEL_FILE))
        # self.skel_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.SKELETON_FILE))
        # self.joint_pos_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.SKELETON_POS))
        # self.cmpt_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.COMPONENTS))
        # self.guide_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.GUIDES))
        # self.ctl_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.CONTROL_SHAPES))
        # self.skin_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.SKINS))
        # self.psd_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.PSD))
        # self.out_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.OUTPUT_RIG))

        # # set the default output file type
        # file_type_text = cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.OUTPUT_RIG_FILE_TYPE)
        # index = self.out_file_type_cb.findText(file_type_text, QtCore.Qt.MatchFixedString)
        # if index >= 0:
        #     self.out_file_type_cb.setCurrentIndex(index)

    # def reload_prescripts(self):
    #     self.preScript_scriptRunner.clear_scripts()
    #     self.preScript_scriptRunner.set_relative_dir(self.rig_builder.get_rig_env())
    #     for path in self.rig_builder.get_rig_data(self.rig_file, cmptBuilder.PRE_SCRIPT):
    #         # for script in self.rig_builder.validate_script_list(self.rig_builder._absPath(path)):
    #         self.preScript_scriptRunner.add_scripts(self.rig_builder._absPath(path))

    # def reload_postscripts(self):
    #     self.postScript_scriptRunner.clear_scripts()
    #     self.postScript_scriptRunner.set_relative_dir(self.rig_builder.get_rig_env())
    #     for path in self.rig_builder.get_rig_data(self.rig_file, cmptBuilder.POST_SCRIPT):
    #         # for script in self.rig_builder.validate_script_list(self.rig_builder._absPath(path)):
    #         self.postScript_scriptRunner.add_scripts(self.rig_builder._absPath(path))

    # def reload_pubscripts(self):
    #     self.publishScript_scriptRunner.clear_scripts()
    #     self.publishScript_scriptRunner.set_relative_dir(self.rig_builder.get_rig_env())
    #     for path in self.rig_builder.get_rig_data(self.rig_file, cmptBuilder.PUB_SCRIPT):
    #         # for script in self.rig_builder.validate_script_list(self.rig_builder._absPath(path)):
    #         self.publishScript_scriptRunner.add_scripts(self.rig_builder._absPath(path))

    # UTILITIY FUNCTIONS
    def create_rig_env(self):
        create_dialog = CreateRigEnvDialog()
        create_dialog.new_env_created.connect(self.set_rig_file)
        create_dialog.show_dialog()

    # BULDER FUNCTIONS
    def run_selected(self):
        """run selected steps"""
        startTime = time.time()

        if self.preScript_wdgt.isChecked():
            self.preScript_scriptRunner.execute_all_scripts()
        if self.model_wdgt.isChecked():
            self.import_model()
        if self.skeleton_wdgt.isChecked():
            self.import_and_load_skeleton()
        if self.cmpt_wdgt.isChecked():
            self.load_components()
            self.complete_build()
        if self.ctlShape_wdgt.isChecked():
            self.load_controlShapes()
        if self.deformations_wdgt.isChecked():
            self.load_all_skins()
            self.load_posereaders()
        if self.postScript_wdgt.isChecked():
            self.postScript_scriptRunner.execute_all_scripts()
        if self.publish_wdgt.isChecked():
            self.publishScript_scriptRunner.execute_all_scripts()

        runTime = time.time() - startTime
        print("Time Elapsed: {}".format(str(runTime)))

    def run_all(self):
        self.rig_builder.run()
        self.cmpt_manager.load_cmpts_from_scene()

    # def publish(self):
    #     confirm_pub_msg = QtWidgets.QMessageBox()
    #     confirm_pub_msg.setText("Publish the rig")
    #     confirm_pub_msg.setInformativeText(
    #         "Proceeding will rebuild a fresh rig from saved data overwriting any existing any published rigs.")
    #     confirm_pub_msg.setStandardButtons(
    #         QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
    #     confirm_pub_msg.setDefaultButton(QtWidgets.QMessageBox.Save)
    #     res = confirm_pub_msg.exec_()
    #
    #     if res == QtWidgets.QMessageBox.Save:
    #         outputfile = self.out_path_selector.get_abs_path()
    #         assetName = self.asset_name_le.text()
    #         fileType = self.out_file_type_cb.currentText()
    #
    #         self.rig_builder.run(publish=True, outputfile=outputfile, assetName=assetName, fileType=fileType)

    def closeEvent(self, e):
        super(BuilderUi, self).closeEvent(e)
        self.initialize_widget.cmpt_manager.set_scriptjob_enabled(False)

    # TOOLS MENU
    def run_performace_test(self):
        import rigamajig2.maya.qc as qc
        qc.runPerformanceTest()

    def generate_random_anmation(self):
        import rigamajig2.maya.qc as qc
        qc.generateRandomAnim()

    def reload_rigamajig_modules(self):
        import rigamajig2
        rigamajig2.reloadModule(log=True)


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
            rig_file = rigamajig2.maya.rig_builder.builderUtils.new_rigenv_from_archetype(new_env=dest_rig_env,
                                                                                          archetype=archetype,
                                                                                          rig_name=rig_name)
        else:
            src_env = self.src_path.get_path()
            rig_file = rigamajig2.maya.rig_builder.builderUtils.create_rig_env(src_env=src_env, tgt_env=dest_rig_env,
                                                                               rig_name=rig_name)
        self.new_env_created.emit(rig_file)

        self.close()


if __name__ == '__main__':

    try:
        rigamajig_builder_dialog.close()
        rigamajig_builder_dialog.deleteLater()
    except:
        pass

    rigamajig_builder_dialog = BuilderUi()
    rigamajig_builder_dialog.show()

    rigamajig_builder_dialog.set_rig_file(
        path='/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/biped.rig')
