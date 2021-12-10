"""
This file contains the UI for the main rig builder
"""
import sys
import logging
import os

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

import rigamajig2.shared.common as common
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner, componentManager
import rigamajig2.maya.rig.builder as builder

logger = logging.getLogger(__name__)
logger.setLevel(5)


class RigamajigBuilderUi(QtWidgets.QDialog):
    WINDOW_TITLE = "Rigamajig2 Builder"

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = RigamajigBuilderUi()

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

        super(RigamajigBuilderUi, self).__init__(maya_main_window)
        self.rig_env = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(375, 825)

        self.create_actions()
        self.create_menus()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_actions(self):
        # FILE
        self.load_rig_file_action = QtWidgets.QAction("Load Rig File", self)
        self.load_rig_file_action.triggered.connect(self.load_rig_file)

        self.save_rig_file_action = QtWidgets.QAction("Save Rig File", self)
        self.save_rig_file_action.triggered.connect(self.save_rig_file)

        # UTILS
        # ...

        # HELP
        self.show_documentation_action = QtWidgets.QAction("Documentation", self)
        self.show_documentation_action.triggered.connect(self.show_documentation)

        self.show_about_action = QtWidgets.QAction("About", self)
        self.show_about_action.triggered.connect(self.show_about)

    def create_menus(self):
        """create menu actions"""
        self.main_menu = QtWidgets.QMenuBar()

        file_menu = self.main_menu.addMenu("File")
        file_menu.addAction(self.load_rig_file_action)
        file_menu.addAction(self.save_rig_file_action)

        utils_menu = self.main_menu.addMenu("Utils")
        tools_menu = self.main_menu.addMenu("Tools")

        help_menu = self.main_menu.addMenu("Help")
        help_menu.addAction(self.show_documentation_action)
        help_menu.addAction(self.show_about_action)

    def create_widgets(self):
        self.rig_path_selector = pathSelector.PathSelector(cap='Select a Rig File', ff="Rig Files (*.rig)", fm=1)

        self.create_rig_env_btn = QtWidgets.QPushButton("Create rig env")
        self.create_rig_env_btn.setToolTip("Create a new rig enviornment from scratch")

        self.clone_rig_env_btn = QtWidgets.QPushButton("Clone rig env")
        self.create_rig_env_btn.setToolTip("Create a new rig enviornment from an existing enviornment")

        # Pre- script section
        self.preScript_wdgt = collapseableWidget.CollapsibleWidget('Pre-Script')
        self.preScript_scriptRunner = scriptRunner.ScriptRunner()

        # Model Section
        self.model_wdgt = collapseableWidget.CollapsibleWidget('Model')
        self.model_path_selector = pathSelector.PathSelector("model:", cap="Select a Model file",
                                                             ff="Maya Files (*.ma;; *.mb)", fm=1)
        self.import_model_btn = QtWidgets.QPushButton('Import Model')
        self.check_model_btn = QtWidgets.QPushButton('Check Model')
        self.check_model_btn.setFixedWidth(100)

        # Skeleton Section
        self.skeleton_wdgt = collapseableWidget.CollapsibleWidget('Skeleton')
        self.skel_path_selector = pathSelector.PathSelector("skeleton:", cap="Select a Skeleton file",
                                                            ff="Maya Files (*.ma;; *.mb)", fm=1)
        self.joint_pos_path_selector = pathSelector.PathSelector("joint pos: ", cap="Select a Skeleton position file",
                                                                 ff="Json Files (*.json)", fm=1)
        self.import_skeleton_btn = QtWidgets.QPushButton("Import skeleton")
        self.save_skeleton_btn = QtWidgets.QPushButton("Save skeleton")
        self.load_jnt_pos_btn = QtWidgets.QPushButton("Load joint pos")
        self.save_jnt_pos_btn = QtWidgets.QPushButton("Save joint pos")

        # Component Section
        self.cmpt_wdgt = collapseableWidget.CollapsibleWidget('Component')
        self.cmpt_manager = componentManager.ComponentManager()
        self.initalize_sel_btn = QtWidgets.QPushButton("Initalize Selected")
        self.initalize_all_btn = QtWidgets.QPushButton("Initalize All")
        self.show_advanced_proxy_cb = QtWidgets.QCheckBox()
        self.show_advanced_proxy_cb.setFixedWidth(25)

        # Build Section
        self.build_wdgt = collapseableWidget.CollapsibleWidget('Build')
        self.build_rig_btn = QtWidgets.QPushButton("Build")

        # Post - script section
        self.postScript_wdgt = collapseableWidget.CollapsibleWidget('Post-Script')
        self.postScript_scriptRunner = scriptRunner.ScriptRunner()

        # Control Shape Section
        self.ctlShape_wdgt = collapseableWidget.CollapsibleWidget('Controls')
        self.ctl_selector = pathSelector.PathSelector("Controls:", cap="Select a Control Shape file",
                                                      ff="Json Files (*.json)", fm=1)
        self.load_color_cb = QtWidgets.QCheckBox()
        self.load_color_cb.setChecked(True)
        self.load_color_cb.setFixedWidth(25)
        self.load_ctl_btn = QtWidgets.QPushButton("Load Controls")
        self.save_ctl_btn = QtWidgets.QPushButton("Save Controls")

        # Deformation Section
        self.deformations_wdgt = collapseableWidget.CollapsibleWidget('Deformations')
        # Publish Section
        self.publish_wdgt = collapseableWidget.CollapsibleWidget('Publish')
        self.publishScript_scriptRunner = scriptRunner.ScriptRunner()

        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layouts(self):
        rig_env_btn_layout = QtWidgets.QHBoxLayout()
        rig_env_btn_layout.addWidget(self.create_rig_env_btn)
        rig_env_btn_layout.addWidget(self.clone_rig_env_btn)

        rig_env_layout = QtWidgets.QVBoxLayout()
        rig_env_layout.addWidget(self.rig_path_selector)
        rig_env_layout.addLayout(rig_env_btn_layout)

        build_layout = QtWidgets.QVBoxLayout()
        build_layout.addWidget(self.preScript_wdgt)

        self.preScript_wdgt.addWidget(self.preScript_scriptRunner)

        # Model
        build_layout.addWidget(self.model_wdgt)
        model_btn_layout = QtWidgets.QHBoxLayout()
        model_btn_layout.setContentsMargins(0, 0, 0, 0)
        model_btn_layout.setSpacing(4)
        model_btn_layout.addWidget(self.import_model_btn)
        model_btn_layout.addWidget(self.check_model_btn)

        self.model_wdgt.addWidget(self.model_path_selector)
        self.model_wdgt.addLayout(model_btn_layout)

        # Skeleton
        build_layout.addWidget(self.skeleton_wdgt)
        save_load_skeleton_layout = QtWidgets.QHBoxLayout()
        save_load_skeleton_layout.addWidget(self.import_skeleton_btn)
        save_load_skeleton_layout.addWidget(self.save_skeleton_btn)

        save_load_jnt_layout = QtWidgets.QHBoxLayout()
        save_load_jnt_layout.addWidget(self.load_jnt_pos_btn)
        save_load_jnt_layout.addWidget(self.save_jnt_pos_btn)

        skeleton_btn_layout = QtWidgets.QVBoxLayout()
        skeleton_btn_layout.setContentsMargins(0, 0, 0, 0)
        skeleton_btn_layout.setSpacing(4)
        skeleton_btn_layout.addLayout(save_load_skeleton_layout)
        skeleton_btn_layout.addLayout(save_load_jnt_layout)

        self.skeleton_wdgt.addWidget(self.skel_path_selector)
        self.skeleton_wdgt.addWidget(self.joint_pos_path_selector)
        self.skeleton_wdgt.addLayout(skeleton_btn_layout)

        # Components
        build_layout.addWidget(self.cmpt_wdgt)

        cmpt_btn_layout = QtWidgets.QHBoxLayout()
        cmpt_btn_layout.setSpacing(4)
        show_proxy_label = QtWidgets.QLabel("show proxy:")
        show_proxy_label.setFixedWidth(70)

        cmpt_btn_layout.addWidget(show_proxy_label)
        cmpt_btn_layout.addWidget(self.show_advanced_proxy_cb)
        cmpt_btn_layout.addWidget(self.initalize_sel_btn)
        cmpt_btn_layout.addWidget(self.initalize_all_btn)
        self.cmpt_wdgt.addWidget(self.cmpt_manager)
        self.cmpt_wdgt.addLayout(cmpt_btn_layout)

        # Build
        build_layout.addWidget(self.build_wdgt)
        self.build_wdgt.addWidget(self.build_rig_btn)

        # Post Script
        build_layout.addWidget(self.postScript_wdgt)
        self.postScript_wdgt.addWidget(self.postScript_scriptRunner)

        # Control shapes
        build_layout.addWidget(self.ctlShape_wdgt)

        control_btn_layout = QtWidgets.QHBoxLayout()
        control_btn_layout.setSpacing(4)
        load_color_label = QtWidgets.QLabel("load color:")
        load_color_label.setFixedWidth(60)

        control_btn_layout.addWidget(load_color_label)
        control_btn_layout.addWidget(self.load_color_cb)
        control_btn_layout.addWidget(self.load_ctl_btn)
        control_btn_layout.addWidget(self.save_ctl_btn)
        self.ctlShape_wdgt.addWidget(self.ctl_selector)
        self.ctlShape_wdgt.addLayout(control_btn_layout)

        # Deformations
        build_layout.addWidget(self.deformations_wdgt)

        # Publish
        build_layout.addWidget(self.publish_wdgt)
        self.publish_wdgt.addWidget(self.publishScript_scriptRunner)

        build_layout.addStretch()

        # lower persistant buttons (AKA close, script editor)
        low_buttons_layout = QtWidgets.QHBoxLayout()
        low_buttons_layout.addWidget(self.close_btn)

        # groups
        rig_env_grp = QtWidgets.QGroupBox('Rig Enviornment')
        rig_env_grp.setLayout(rig_env_layout)

        build_grp = QtWidgets.QGroupBox('Build')
        build_grp.setLayout(build_layout)

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
        self.create_rig_env_btn.clicked.connect(self.create_rig_env)
        self.clone_rig_env_btn.clicked.connect(self.clone_rig_env)

        self.import_model_btn.clicked.connect(self.import_model)

        self.import_skeleton_btn.clicked.connect(self.import_skeleton)
        self.load_jnt_pos_btn.clicked.connect(self.load_joint_positions)
        self.save_jnt_pos_btn.clicked.connect(self.save_joint_positions)

        self.show_advanced_proxy_cb.toggled.connect(self.toggle_advanced_proxy)

        self.load_ctl_btn.clicked.connect(self.load_controlShapes)
        self.save_ctl_btn.clicked.connect(self.save_controlShapes)
        self.close_btn.clicked.connect(self.close)

    # Connections
    def load_rig_file(self):
        pass

    def save_rig_file(self):
        pass

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
        self.model_path_selector.set_relativeTo(self.rig_env)
        self.skel_path_selector.set_relativeTo(self.rig_env)
        self.joint_pos_path_selector.set_relativeTo(self.rig_env)
        self.ctl_selector.set_relativeTo(self.rig_env)

        self.rig_builder = builder.Builder(self.rig_file)
        self.update_ui_with_rig_data()

    def update_ui_with_rig_data(self):
        tmp_builder = builder.Builder()
        if not self.rig_file:
            return

        pre_script_path = os.path.join(self.rig_env, builder.PRE_SCRIPT_PATH)
        if QtCore.QFileInfo(pre_script_path).exists():
            self.preScript_scriptRunner.add_scripts_from_dir(pre_script_path)

        post_script_path = os.path.join(self.rig_env, builder.POST_SCRIPT_PATH)
        if QtCore.QFileInfo(post_script_path).exists():
            self.postScript_scriptRunner.add_scripts_from_dir(post_script_path)

        pub_script_path = os.path.join(self.rig_env, builder.PUB_SCRIPT_PATH)
        if QtCore.QFileInfo(pub_script_path).exists():
            self.publishScript_scriptRunner.add_scripts_from_dir(pub_script_path)

        mod_file = tmp_builder.get_rig_data(self.rig_file, builder.MODEL_FILE)
        if mod_file: self.model_path_selector.set_path(mod_file)

        skel_file = tmp_builder.get_rig_data(self.rig_file, builder.SKELETON_FILE)
        if skel_file: self.skel_path_selector.set_path(skel_file)

        skel_pos_file = tmp_builder.get_rig_data(self.rig_file, builder.SKELETON_POS)
        if skel_pos_file: self.joint_pos_path_selector.set_path(skel_pos_file)

        ctl_file = tmp_builder.get_rig_data(self.rig_file, builder.CONTROL_SHAPES)
        if ctl_file: self.ctl_selector.set_path(ctl_file)

    # UTILITIY FUNCTIONS
    def create_rig_env(self):
        print "TODO : create a rig environment"

    def clone_rig_env(self):
        print "TODO : clone a rig environment"

    # BULDER FUNCTIONS
    def import_model(self):
        self.rig_builder.import_model(self.model_path_selector.get_abs_path())

    def import_skeleton(self):
        self.rig_builder.import_skeleton(self.skel_path_selector.get_abs_path())

    def load_joint_positions(self):
        self.rig_builder.load_joint_positions(self.joint_pos_path_selector.get_abs_path())

    def save_joint_positions(self):
        self.rig_builder.save_joint_positions(self.joint_pos_path_selector.get_abs_path())

    def load_controlShapes(self):
        self.rig_builder.load_controlShapes(self.ctl_selector.get_abs_path(), self.load_color_cb.isChecked())

    def save_controlShapes(self):
        self.rig_builder.save_controlShapes(self.ctl_selector.get_abs_path())

    def toggle_advanced_proxy(self):
        """ Toggle the advanced proxy attributes """
        if self.show_advanced_proxy_cb.isChecked():
            self.rig_builder.show_advanced_proxy()
        else:
            self.rig_builder.delete_advanced_proxy()


if __name__ == '__main__':
    try:
        rigamajig_builder_dialog.close()
        rigamajig_builder_dialog.deleteLater()
    except:
        pass

    rigamajig_builder_dialog = RigamajigBuilderUi()
    rigamajig_builder_dialog.show()

    rigamajig_builder_dialog.set_rig_file(
        path='/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/biped.rig')
