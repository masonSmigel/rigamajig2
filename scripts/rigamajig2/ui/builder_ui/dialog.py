"""
This file contains the UI for the main rig builder
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
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner, overrideColorer, sliderGrp
from rigamajig2.ui.builder_ui import componentManager
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

        # Pre- script section
        self.preScript_wdgt = collapseableWidget.CollapsibleWidget('Pre-Script', addCheckbox=True)
        self.preScript_scriptRunner = scriptRunner.ScriptRunner()

        # Model Section
        self.model_wdgt = collapseableWidget.CollapsibleWidget('Model', addCheckbox=True)
        self.model_path_selector = pathSelector.PathSelector("model:", cap="Select a Model file", ff=MAYA_FILTER, fm=1)
        self.import_model_btn = QtWidgets.QPushButton('Import Model')
        self.open_model_btn = QtWidgets.QPushButton('Open Model')
        self.open_model_btn.setFixedWidth(100)

        # Skeleton Section
        self.skeleton_wdgt = collapseableWidget.CollapsibleWidget('Skeleton', addCheckbox=True)
        self.skel_path_selector = pathSelector.PathSelector("skeleton:", cap="Select a Skeleton file", ff=MAYA_FILTER,
                                                            fm=1)
        self.joint_pos_path_selector = pathSelector.PathSelector("joint pos: ", cap="Select a Skeleton position file",
                                                                 ff=JSON_FILTER, fm=1)
        self.import_skeleton_btn = QtWidgets.QPushButton("Import skeleton")
        self.open_skeleton_btn = QtWidgets.QPushButton("Open skel")
        self.load_jnt_pos_btn = QtWidgets.QPushButton("Load joint pos")
        self.save_jnt_pos_btn = QtWidgets.QPushButton("Save joint pos")
        self.import_load_skeleton_btn = QtWidgets.QPushButton("Import and Load Joint Positions")
        self.import_load_skeleton_btn.setFixedHeight(LARGE_BTN_HEIGHT)

        self.skeletonEdit_wdgt = collapseableWidget.CollapsibleWidget('Edit Skeleton')
        self.clean_skeleton_btn = QtWidgets.QPushButton("Clean Skeleton")
        self.jnt_to_rot_btn = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Rotation")
        self.jnt_to_ori_btn = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Orientation")
        self.jntAxisX_rb = QtWidgets.QRadioButton('x')
        self.jntAxisY_rb = QtWidgets.QRadioButton('y')
        self.jntAxisZ_rb = QtWidgets.QRadioButton('z')
        self.jntAxisX_rb.setChecked(True)

        self.mirrorJntMode_cbox = QtWidgets.QComboBox()
        self.mirrorJntMode_cbox.setFixedHeight(24)
        self.mirrorJntMode_cbox.addItem("rotate")
        self.mirrorJntMode_cbox.addItem("translate")
        self.mirrorJnt_btn = QtWidgets.QPushButton(QtGui.QIcon(":kinMirrorJoint_S"), "Mirror")
        self.mirrorJnt_btn.setFixedHeight(24)

        self.pin_jnt_btn = QtWidgets.QPushButton("Pin Joints")
        self.pin_jnt_btn.setIcon(QtGui.QIcon(":pinned"))
        self.unpin_jnt_btn = QtWidgets.QPushButton("Un-Pin Joints")
        self.unpin_jnt_btn.setIcon(QtGui.QIcon(":unpinned"))

        self.insert_jnts_amt_slider = sliderGrp.SliderGroup()
        self.insert_jnts_amt_slider.setValue(1)
        self.insert_jnts_amt_slider.setRange(1, 10)
        self.insert_jnts_btn = QtWidgets.QPushButton("Insert Joints")

        self.prep_jnts_btn = QtWidgets.QPushButton("Prep Skeleton")

        # Component Section
        self.cmpt_wdgt = collapseableWidget.CollapsibleWidget('Components', addCheckbox=True)
        self.cmpt_path_selector = pathSelector.PathSelector("cmpts:", cap="Select a Component File", ff=JSON_FILTER,
                                                            fm=1)
        self.load_components_btn = QtWidgets.QPushButton("Load Cmpts")
        self.append_components_btn = QtWidgets.QPushButton("Append Cmpts")
        self.save_components_btn = QtWidgets.QPushButton("Save Cmpts")
        self.save_components_btn.setIcon(QtGui.QIcon(":save.png"))
        self.add_components_btn = QtWidgets.QPushButton("Add Components")
        self.add_components_btn.setIcon(QtGui.QIcon(":freeformOff.png"))
        self.cmpt_manager = componentManager.ComponentManager()

        self.initalize_build_btn = QtWidgets.QPushButton("Initalize Build")
        self.initalize_build_btn.setFixedHeight(LARGE_BTN_HEIGHT)
        self.guide_path_selector = pathSelector.PathSelector("guides:", cap="Select a guide file", ff=JSON_FILTER, fm=1)
        self.load_guides_btn = QtWidgets.QPushButton("Load Guides")
        self.save_guides_btn = QtWidgets.QPushButton("Save Guides")

        self.load_ctls_on_build = QtWidgets.QCheckBox("Load Ctls")
        self.load_ctls_on_build.setChecked(True)
        self.load_ctls_on_build.setFixedWidth(80)

        self.complete_build_btn = QtWidgets.QPushButton("Build Rig")
        self.complete_build_btn.setFixedHeight(45)

        # Post - script section
        self.postScript_wdgt = collapseableWidget.CollapsibleWidget('Post-Script', addCheckbox=True)
        self.postScript_scriptRunner = scriptRunner.ScriptRunner()

        # Control Shape Section
        self.ctlShape_wdgt = collapseableWidget.CollapsibleWidget('Controls', addCheckbox=True)
        self.ctl_path_selector = pathSelector.PathSelector("Controls:", cap="Select a Control Shape file",
                                                           ff=JSON_FILTER, fm=1)
        self.load_color_cb = QtWidgets.QCheckBox()
        self.load_color_cb.setChecked(True)
        self.load_color_cb.setFixedWidth(25)
        self.load_ctl_btn = QtWidgets.QPushButton("Load Controls")
        self.save_ctl_btn = QtWidgets.QPushButton("Save Controls")

        self.controlEdit_wgt = collapseableWidget.CollapsibleWidget('Edit Controls')

        self.ctlAxisX_rb = QtWidgets.QRadioButton('x')
        self.ctlAxisX_rb.setChecked(True)
        self.ctlAxisY_rb = QtWidgets.QRadioButton('y')
        self.ctlAxisZ_rb = QtWidgets.QRadioButton('z')
        self.mirrorCtlMode_cbox = QtWidgets.QComboBox()
        self.mirrorCtlMode_cbox.setFixedHeight(24)
        self.mirrorCtlMode_cbox.addItem("replace")
        self.mirrorCtlMode_cbox.addItem("match")
        self.mirror_control_btn = QtWidgets.QPushButton("Mirror")

        self.ctlColor_ovrcol = overrideColorer.OverrideColorer()

        self.ctlShape_cbox = QtWidgets.QComboBox()
        self.ctlShape_cbox.setFixedHeight(24)
        self.set_ctlShape_items()
        self.setCtlShape_btn = QtWidgets.QPushButton("Set Shape")

        self.replace_ctl_btn = QtWidgets.QPushButton("Replace Control Shape ")

        # Deformation Section
        self.deformations_wdgt = collapseableWidget.CollapsibleWidget('Deformations', addCheckbox=True)

        self.skin_path_selector = pathSelector.PathSelector("skin:", cap="Select the skin weight folder", ff=JSON_FILTER,
                                                           fm=2)
        self.load_all_skin_btn = QtWidgets.QPushButton("Load All Skins")
        self.load_single_skin_btn = QtWidgets.QPushButton("Load Skin")
        self.save_skin_btn = QtWidgets.QPushButton("Save Skin")

        self.psd_path_selector = pathSelector.PathSelector("psd:", cap="Select a Pose Reader File", ff=JSON_FILTER,
                                                           fm=1)

        self.load_psd_btn = QtWidgets.QPushButton("Load Pose Readers")
        self.save_psd_btn = QtWidgets.QPushButton("Save Pose Readers")

        self.load_psd_mode_cbox = QtWidgets.QComboBox()
        self.load_psd_mode_cbox.setFixedHeight(24)
        self.load_psd_mode_cbox.addItem("append")
        self.load_psd_mode_cbox.addItem("replace")

        # Publish Section
        self.publish_wdgt = collapseableWidget.CollapsibleWidget('Publish', addCheckbox=True)
        self.publishScript_scriptRunner = scriptRunner.ScriptRunner()
        self.out_path_selector = pathSelector.PathSelector("out file:", cap="Select a location to save", ff=MAYA_FILTER,
                                                           fm=2)
        self.pub_btn = QtWidgets.QPushButton("Publish Rig")
        self.pub_btn.setFixedHeight(LARGE_BTN_HEIGHT)

        self.out_file_type_cb = QtWidgets.QComboBox()
        self.out_file_type_cb.addItem('ma')
        self.out_file_type_cb.addItem('mb')

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
        self.preScript_wdgt.addWidget(self.preScript_scriptRunner)

        # Model
        model_btn_layout = QtWidgets.QHBoxLayout()
        model_btn_layout.setContentsMargins(0, 0, 0, 0)
        model_btn_layout.setSpacing(4)
        model_btn_layout.addWidget(self.import_model_btn)
        model_btn_layout.addWidget(self.open_model_btn)

        self.model_wdgt.addWidget(self.model_path_selector)
        self.model_wdgt.addLayout(model_btn_layout)

        # Skeleton
        save_load_skeleton_layout = QtWidgets.QHBoxLayout()
        save_load_skeleton_layout.addWidget(self.import_skeleton_btn)
        save_load_skeleton_layout.addWidget(self.open_skeleton_btn)

        save_load_jnt_layout = QtWidgets.QHBoxLayout()
        save_load_jnt_layout.addWidget(self.load_jnt_pos_btn)
        save_load_jnt_layout.addWidget(self.save_jnt_pos_btn)

        skeleton_btn_layout = QtWidgets.QVBoxLayout()
        skeleton_btn_layout.setContentsMargins(0, 0, 0, 0)
        skeleton_btn_layout.setSpacing(4)
        skeleton_btn_layout.addLayout(save_load_skeleton_layout)
        skeleton_btn_layout.addLayout(save_load_jnt_layout)

        jointOrientation_layout = QtWidgets.QHBoxLayout()
        jointOrientation_layout.addWidget(self.jnt_to_rot_btn)
        jointOrientation_layout.addWidget(self.jnt_to_ori_btn)

        mirrorJoint_layout = QtWidgets.QHBoxLayout()
        mirrorJoint_layout.setSpacing(4)
        jointMirrorAxis_layout = QtWidgets.QHBoxLayout()
        jointMirrorAxis_layout.addWidget(QtWidgets.QLabel("Axis: "))
        jointMirrorAxis_layout.addWidget(self.jntAxisX_rb)
        jointMirrorAxis_layout.addWidget(self.jntAxisY_rb)
        jointMirrorAxis_layout.addWidget(self.jntAxisZ_rb)

        mirrorJoint_layout.addLayout(jointMirrorAxis_layout)
        mirrorJoint_layout.addWidget(self.mirrorJntMode_cbox)
        mirrorJoint_layout.addWidget(self.mirrorJnt_btn)

        pinJoint_layout = QtWidgets.QHBoxLayout()
        pinJoint_layout.addWidget(self.pin_jnt_btn)
        pinJoint_layout.addWidget(self.unpin_jnt_btn)

        insertJoint_layout = QtWidgets.QHBoxLayout()
        insertJoint_layout.addWidget(self.insert_jnts_amt_slider)
        insertJoint_layout.addWidget(self.insert_jnts_btn)

        self.skeleton_wdgt.addWidget(self.skel_path_selector)
        self.skeleton_wdgt.addWidget(self.joint_pos_path_selector)
        self.skeleton_wdgt.addLayout(skeleton_btn_layout)
        self.skeleton_wdgt.addWidget(self.import_load_skeleton_btn)
        self.skeleton_wdgt.addWidget(self.skeletonEdit_wdgt)

        self.skeletonEdit_wdgt.addWidget(self.clean_skeleton_btn)
        self.skeletonEdit_wdgt.addLayout(jointOrientation_layout)
        self.skeletonEdit_wdgt.addLayout(mirrorJoint_layout)
        self.skeletonEdit_wdgt.addLayout(pinJoint_layout)
        self.skeletonEdit_wdgt.addLayout(insertJoint_layout)
        self.skeletonEdit_wdgt.addWidget(self.prep_jnts_btn)

        # Components
        cmpt_btn_layout = QtWidgets.QHBoxLayout()
        cmpt_btn_layout.setSpacing(4)

        guide_load_layout = QtWidgets.QHBoxLayout()
        guide_load_layout.addWidget(self.load_guides_btn)
        guide_load_layout.addWidget(self.save_guides_btn)

        cmpt_load_layout = QtWidgets.QHBoxLayout()
        cmpt_load_layout.addWidget(self.load_components_btn)
        cmpt_load_layout.addWidget(self.save_components_btn)
        cmpt_load_layout.addWidget(self.add_components_btn)

        self.cmpt_wdgt.addWidget(self.cmpt_path_selector)
        self.cmpt_wdgt.addLayout(cmpt_load_layout)
        self.cmpt_wdgt.addWidget(self.cmpt_manager)
        self.cmpt_wdgt.addWidget(self.initalize_build_btn)
        self.cmpt_wdgt.addLayout(cmpt_btn_layout)
        self.cmpt_wdgt.addWidget(self.guide_path_selector)
        self.cmpt_wdgt.addLayout(guide_load_layout)
        build_layout = QtWidgets.QHBoxLayout()

        self.cmpt_wdgt.addLayout(build_layout)
        build_layout.addWidget(self.load_ctls_on_build)
        build_layout.addWidget(self.complete_build_btn)

        # Post Script
        self.postScript_wdgt.addWidget(self.postScript_scriptRunner)

        # Control shapes
        control_btn_layout = QtWidgets.QHBoxLayout()
        control_btn_layout.setSpacing(4)
        load_color_label = QtWidgets.QLabel("Load Color:")
        load_color_label.setFixedWidth(60)

        control_btn_layout.addWidget(load_color_label)
        control_btn_layout.addWidget(self.load_color_cb)
        control_btn_layout.addWidget(self.load_ctl_btn)
        control_btn_layout.addWidget(self.save_ctl_btn)

        mirrorControl_layout = QtWidgets.QHBoxLayout()
        mirrorControl_layout.setSpacing(4)
        controlMirrorAxis_layout = QtWidgets.QHBoxLayout()
        controlMirrorAxis_layout.addWidget(QtWidgets.QLabel("Axis: "))
        controlMirrorAxis_layout.addWidget(self.ctlAxisX_rb)
        controlMirrorAxis_layout.addWidget(self.ctlAxisY_rb)
        controlMirrorAxis_layout.addWidget(self.ctlAxisZ_rb)

        mirrorControl_layout.addLayout(controlMirrorAxis_layout)
        mirrorControl_layout.addWidget(self.mirrorCtlMode_cbox)
        mirrorControl_layout.addWidget(self.mirror_control_btn)

        setControlShape_layout = QtWidgets.QHBoxLayout()
        setControlShape_layout.addWidget(self.ctlShape_cbox)
        setControlShape_layout.addWidget(self.setCtlShape_btn)

        self.ctlShape_wdgt.addWidget(self.ctl_path_selector)
        self.ctlShape_wdgt.addLayout(control_btn_layout)
        self.ctlShape_wdgt.addWidget(self.controlEdit_wgt)
        self.controlEdit_wgt.addLayout(mirrorControl_layout)
        self.controlEdit_wgt.addWidget(self.ctlColor_ovrcol)
        self.controlEdit_wgt.addLayout(setControlShape_layout)
        self.controlEdit_wgt.addWidget(self.replace_ctl_btn)

        # Deformations
        skin_btn_layout = QtWidgets.QHBoxLayout()
        skin_btn_layout.setContentsMargins(0, 0, 0, 0)
        skin_btn_layout.setSpacing(4)
        skin_btn_layout.addWidget(self.load_all_skin_btn)
        skin_btn_layout.addWidget(self.load_single_skin_btn)
        skin_btn_layout.addWidget(self.save_skin_btn)

        self.deformations_wdgt.addWidget(self.skin_path_selector)
        self.deformations_wdgt.addLayout(skin_btn_layout)

        psd_btn_layout = QtWidgets.QHBoxLayout()
        psd_btn_layout.setContentsMargins(0, 0, 0, 0)
        psd_btn_layout.setSpacing(4)
        psd_btn_layout.addWidget(self.load_psd_btn)
        psd_btn_layout.addWidget(self.save_psd_btn)
        psd_btn_layout.addWidget(self.load_psd_mode_cbox)

        self.deformations_wdgt.addWidget(self.psd_path_selector)
        self.deformations_wdgt.addLayout(psd_btn_layout)


        # Publish
        self.publish_wdgt.addWidget(self.publishScript_scriptRunner)
        publish_file_layout = QtWidgets.QHBoxLayout()
        publish_file_layout.addWidget(self.out_path_selector)
        publish_file_layout.addWidget(self.out_file_type_cb)
        self.publish_wdgt.addLayout(publish_file_layout)
        self.publish_wdgt.addWidget(self.pub_btn)

        # add the collapseable widgets
        build_layout = QtWidgets.QVBoxLayout()
        build_layout.addWidget(self.preScript_wdgt)
        build_layout.addWidget(self.model_wdgt)
        build_layout.addWidget(self.skeleton_wdgt)
        build_layout.addWidget(self.cmpt_wdgt)
        build_layout.addWidget(self.ctlShape_wdgt)
        build_layout.addWidget(self.postScript_wdgt)
        build_layout.addWidget(self.deformations_wdgt)
        build_layout.addWidget(self.publish_wdgt)
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

        self.preScript_scriptRunner.reload_scripts_btn.clicked.connect(self.reload_prescripts)

        self.import_model_btn.clicked.connect(self.import_model)
        self.open_model_btn.clicked.connect(self.open_model)

        self.import_load_skeleton_btn.clicked.connect(self.import_and_load_skeleton)
        self.import_skeleton_btn.clicked.connect(self.import_skeleton)
        self.load_jnt_pos_btn.clicked.connect(self.load_joint_positions)
        self.save_jnt_pos_btn.clicked.connect(self.save_joint_positions)
        self.open_skeleton_btn.clicked.connect(self.open_skeleton)
        self.jnt_to_rot_btn.clicked.connect(self.jnt_to_rotation)
        self.jnt_to_ori_btn.clicked.connect(self.jnt_to_orientation)
        self.mirrorJnt_btn.clicked.connect(self.mirror_joint)
        self.pin_jnt_btn.clicked.connect(self.pin_joints)
        self.unpin_jnt_btn.clicked.connect(self.unpin_joints)
        self.insert_jnts_btn.clicked.connect(self.insert_joints)
        self.prep_jnts_btn.clicked.connect(self.prep_skeleton)

        self.load_guides_btn.clicked.connect(self.load_guides)
        self.save_guides_btn.clicked.connect(self.save_guides)
        self.load_components_btn.clicked.connect(self.load_components)
        self.save_components_btn.clicked.connect(self.save_components)

        self.add_components_btn.clicked.connect(self.cmpt_manager.show_add_component_dialog)
        self.initalize_build_btn.clicked.connect(self.initalize_rig)
        self.complete_build_btn.clicked.connect(self.complete_build)

        self.load_ctl_btn.clicked.connect(self.load_controlShapes)
        self.save_ctl_btn.clicked.connect(self.save_controlShapes)
        self.mirror_control_btn.clicked.connect(self.mirror_control)
        self.setCtlShape_btn.clicked.connect(self.set_controlShape)
        self.replace_ctl_btn.clicked.connect(self.replace_controlShape)

        self.load_all_skin_btn.clicked.connect(self.load_all_skins)
        self.load_single_skin_btn.clicked.connect(self.load_single_skin)
        self.save_skin_btn.clicked.connect(self.save_skin)
        self.load_psd_btn.clicked.connect(self.load_posereaders)
        self.save_psd_btn.clicked.connect(self.save_posereaders)

        self.run_selected_btn.clicked.connect(self.run_selected)
        self.run_btn.clicked.connect(self.run_all)
        self.pub_btn.clicked.connect(self.publish)
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
        self.model_path_selector.set_relativeTo(self.rig_env)
        self.skel_path_selector.set_relativeTo(self.rig_env)
        self.joint_pos_path_selector.set_relativeTo(self.rig_env)
        self.cmpt_path_selector.set_relativeTo(self.rig_env)
        self.guide_path_selector.set_relativeTo(self.rig_env)
        self.ctl_path_selector.set_relativeTo(self.rig_env)
        self.skin_path_selector.set_relativeTo(self.rig_env)
        self.psd_path_selector.set_relativeTo(self.rig_env)
        self.out_path_selector.set_relativeTo(self.rig_env)

        self.rig_builder = cmptBuilder.Builder(self.rig_file)
        self.cmpt_manager.set_rig_builder(self.rig_builder)
        self.update_ui_with_rig_data()

    def update_ui_with_rig_data(self):
        if not self.rig_file:
            return

        # set the character name
        self.asset_name_le.setText(self.rig_builder.get_rig_data(self.rig_file, cmptBuilder.RIG_NAME))

        # loadSettings prescripts, postscripts and pubscripts from file or rig_env
        self.reload_prescripts()
        self.reload_postscripts()
        self.reload_pubscripts()

        # set rig paths
        self.model_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.MODEL_FILE))
        self.skel_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.SKELETON_FILE))
        self.joint_pos_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.SKELETON_POS))
        self.cmpt_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.COMPONENTS))
        self.guide_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.GUIDES))
        self.ctl_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.CONTROL_SHAPES))
        self.skin_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.SKINS))
        self.psd_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.PSD))
        self.out_path_selector.set_path(cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.OUTPUT_RIG))

        # clear the component manager
        self.cmpt_manager.clear_cmpt_tree()

        # set the default output file type
        file_type_text = cmptBuilder.Builder.get_rig_data(self.rig_file, cmptBuilder.OUTPUT_RIG_FILE_TYPE)
        index = self.out_file_type_cb.findText(file_type_text, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.out_file_type_cb.setCurrentIndex(index)

    def reload_prescripts(self):
        self.preScript_scriptRunner.clear_scripts()
        self.preScript_scriptRunner.set_relative_dir(self.rig_builder.get_rig_env())
        for path in self.rig_builder.get_rig_data(self.rig_file, cmptBuilder.PRE_SCRIPT):
            # for script in self.rig_builder.validate_script_list(self.rig_builder._absPath(path)):
            self.preScript_scriptRunner.add_scripts(self.rig_builder._absPath(path))

    def reload_postscripts(self):
        self.postScript_scriptRunner.clear_scripts()
        self.postScript_scriptRunner.set_relative_dir(self.rig_builder.get_rig_env())
        for path in self.rig_builder.get_rig_data(self.rig_file, cmptBuilder.POST_SCRIPT):
            # for script in self.rig_builder.validate_script_list(self.rig_builder._absPath(path)):
            self.postScript_scriptRunner.add_scripts(self.rig_builder._absPath(path))

    def reload_pubscripts(self):
        self.publishScript_scriptRunner.clear_scripts()
        self.publishScript_scriptRunner.set_relative_dir(self.rig_builder.get_rig_env())
        for path in self.rig_builder.get_rig_data(self.rig_file, cmptBuilder.PUB_SCRIPT):
            # for script in self.rig_builder.validate_script_list(self.rig_builder._absPath(path)):
            self.publishScript_scriptRunner.add_scripts(self.rig_builder._absPath(path))

    # UI FUNCTIONS
    def set_ctlShape_items(self):
        import rigamajig2.maya.rig.control
        control_shapes = rigamajig2.maya.rig.control.getAvailableControlShapes()
        for control_shape in control_shapes:
            self.ctlShape_cbox.addItem(control_shape)

    # UTILITIY FUNCTIONS
    def create_rig_env(self):
        create_dialog = CreateRigEnvDialog()
        create_dialog.new_env_created.connect(self.set_rig_file)
        create_dialog.show_dialog()

    # CONNECTIONS
    def mirror_joint(self):
        """ mirror joint"""
        import rigamajig2.maya.joint
        axis = 'x'
        if self.jntAxisY_rb.isChecked(): axis = 'y'
        if self.jntAxisZ_rb.isChecked(): axis = 'z'
        mirrorMode = self.mirrorJntMode_cbox.currentText()
        for joint in cmds.ls(sl=True):
            joints = cmds.listRelatives(cmds.ls(sl=True, type='joint'), ad=True, type='joint') or []
            rigamajig2.maya.joint.mirror(joints + [joint], axis=axis, mode=mirrorMode)

    def jnt_to_rotation(self):
        import rigamajig2.maya.joint
        rigamajig2.maya.joint.toRotation(cmds.ls(sl=True, type='joint'))

    def jnt_to_orientation(self):
        import rigamajig2.maya.joint
        rigamajig2.maya.joint.toOrientation(cmds.ls(sl=True, type='joint'))

    def mirror_control(self):
        import rigamajig2.maya.curve
        axis = 'x'
        if self.ctlAxisY_rb.isChecked(): axis = 'y'
        if self.ctlAxisZ_rb.isChecked(): axis = 'z'
        mirrorMode = self.mirrorCtlMode_cbox.currentText()
        rigamajig2.maya.curve.mirror(cmds.ls(sl=True, type='transform'), axis=axis, mode=mirrorMode)

    # BULDER FUNCTIONS
    def import_model(self):
        self.rig_builder.import_model(self.model_path_selector.get_abs_path())

    def open_model(self):
        cmds.file(self.model_path_selector.get_abs_path(), o=True, f=True)

    def import_and_load_skeleton(self):
        self.load_joint_positions()

    def import_skeleton(self):
        self.rig_builder.import_skeleton(self.skel_path_selector.get_abs_path())

    def open_skeleton(self):
        cmds.file(self.skel_path_selector.get_abs_path(), o=True, f=True)

    def load_joint_positions(self):
        self.rig_builder.load_joints(self.joint_pos_path_selector.get_abs_path())

    def save_joint_positions(self):
        self.rig_builder.save_joints(self.joint_pos_path_selector.get_abs_path())

    def pin_joints(self):
        import rigamajig2.maya.rig.live as live
        live.pin()

    def unpin_joints(self):
        import rigamajig2.maya.rig.live as live
        live.unpin()

    def insert_joints(self):
        import rigamajig2.maya.joint as joint
        jnt_amt = self.insert_jnts_amt_slider.getValue()
        selection = cmds.ls(sl=True)
        assert len(selection) == 2, "Must select two joints!"
        joint.insertJoints(selection[0], selection[-1], amount=jnt_amt)

    def prep_skeleton(self):
        import rigamajig2.maya.joint as joint
        joint.addJointOrientToChannelBox(cmds.ls(sl=True))
        joint.toOrientation(cmds.ls(sl=True))

    def load_components(self):
        self.rig_builder.set_cmpts(list())
        self.rig_builder.load_components(self.cmpt_path_selector.get_abs_path())
        self.rig_builder.load_component_settings(self.cmpt_path_selector.get_abs_path())
        self.cmpt_manager.load_list_from_builder()

    def save_components(self):
        self.rig_builder.load_meta_settings()
        self.rig_builder.save_components(self.cmpt_path_selector.get_abs_path())

    def initalize_rig(self):
        self.rig_builder.initalize()
        self.rig_builder.load_component_settings()
        self.cmpt_manager.load_cmpts_from_scene()

    def clear_components(self):
        self.rig_builder.set_cmpts(list())

    def build_rig(self):
        self.rig_builder.build()
        self.cmpt_manager.load_cmpts_from_scene()

    def connect_rig(self):
        self.rig_builder.connect()
        self.cmpt_manager.load_cmpts_from_scene()

    def finalize_rig(self):
        self.rig_builder.finalize()
        self.cmpt_manager.load_cmpts_from_scene()

    def complete_build(self):
        self.rig_builder.initalize()
        self.rig_builder.load_component_settings()
        self.rig_builder.build()
        self.rig_builder.connect()
        self.rig_builder.finalize()
        if self.load_ctls_on_build.isChecked():
            self.load_controlShapes()
        self.cmpt_manager.load_cmpts_from_scene()

    def load_guides(self):
        self.rig_builder.load_guide_data(self.guide_path_selector.get_abs_path())

    def save_guides(self):
        self.rig_builder.save_guide_data(self.guide_path_selector.get_abs_path())

    def load_controlShapes(self):
        self.rig_builder.load_controlShapes(self.ctl_path_selector.get_abs_path(), self.load_color_cb.isChecked())

    def save_controlShapes(self):
        self.rig_builder.save_controlShapes(self.ctl_path_selector.get_abs_path())

    def set_controlShape(self):
        """Set the control shape of the selected node"""
        import rigamajig2.maya.rig.control
        shape = self.ctlShape_cbox.currentText()
        for node in cmds.ls(sl=True, type='transform'):
            rigamajig2.maya.rig.control.setControlShape(node, shape)

    def replace_controlShape(self):
        """Replace the control shape"""
        import rigamajig2.maya.curve
        selection = cmds.ls(sl=True, type='transform')
        if len(selection) >= 2:
            for dest in selection[1:]:
                if cmds.listRelatives(dest, shapes=True, pa=True):
                    for shape in cmds.listRelatives(dest, shapes=True, pa=True):
                        cmds.delete(shape)
                rigamajig2.maya.curve.copyShape(selection[0], dest)

    def load_all_skins(self):
        self.rig_builder.load_skin_weights(self.skin_path_selector.get_abs_path())

    def load_single_skin(self):
        path = cmds.fileDialog2(ds=2, cap="Select a skin file", ff=JSON_FILTER, okc="Select",
                                dir=self.skin_path_selector.get_abs_path())
        if path:
            deform.load_single_skin(path[0])

    def save_skin(self):
        self.rig_builder.save_skin_weights(path=self.skin_path_selector.get_abs_path())

    def load_posereaders(self):
        self.rig_builder.load_poseReaders(self.psd_path_selector.get_abs_path(),
                                          replace=self.load_psd_mode_cbox.currentIndex())

    def save_posereaders(self):
        self.rig_builder.save_poseReaders(self.psd_path_selector.get_abs_path())

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
            assetName = self.asset_name_le.text()
            fileType = self.out_file_type_cb.currentText()

            self.rig_builder.run(publish=True, outputfile=outputfile, assetName=assetName, fileType=fileType)

    def closeEvent(self, e):
        super(BuilderUi, self).closeEvent(e)
        self.cmpt_manager.set_scriptjob_enabled(False)

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
            rig_file = rigamajig2.maya.rig_builder.builderUtils.new_rigenv_from_archetype(new_env=dest_rig_env, archetype=archetype, rig_name=rig_name)
        else:
            src_env = self.src_path.get_path()
            rig_file = rigamajig2.maya.rig_builder.builderUtils.create_rig_env(src_env=src_env, tgt_env=dest_rig_env, rig_name=rig_name)
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
