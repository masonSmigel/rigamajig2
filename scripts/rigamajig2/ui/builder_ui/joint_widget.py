#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: joint_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""

# !/usr/bin/env python
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

# MAYA
import maya.cmds as cmds

# RIGAMAJIG2
import rigamajig2.maya.joint
import rigamajig2.maya.rig.live as live
import rigamajig2.maya.meta as meta
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, sliderGrp
from rigamajig2.ui.builder_ui import constants
from rigamajig2.maya.rig_builder.builder import SKELETON_POS


class JointWidget(QtWidgets.QWidget):

    def __init__(self, builder=None):
        super(JointWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.main_collapseable_widget = collapseableWidget.CollapsibleWidget('Skeleton', addCheckbox=True)

        self.joint_pos_path_selector = pathSelector.PathSelector(
            "joint pos: ",
            cap="Select a Skeleton position file",
            ff=constants.JSON_FILTER,
            fm=1
            )
        self.load_jnt_pos_btn = QtWidgets.QPushButton("Load joints")
        self.save_jnt_pos_btn = QtWidgets.QPushButton("Save joints")

        self.skeletonEdit_wdgt = collapseableWidget.CollapsibleWidget('Edit Skeleton')
        self.skeletonEdit_wdgt.set_header_background_color(constants.EDIT_BG_HEADER_COLOR)
        self.skeletonEdit_wdgt.set_widget_background_color(constants.EDIT_BG_WIDGET_COLOR)

        self.jnt_to_rot_btn = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Rotation")
        self.jnt_to_ori_btn = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Orientation")
        self.clean_skeleton_btn = QtWidgets.QPushButton("Clean Skeleton")
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

        self.unpinAll_jnt_btn = QtWidgets.QPushButton("Un-Pin All Joints")
        self.unpinAll_jnt_btn.setIcon(QtGui.QIcon(":unpinned"))

        self.insert_jnts_amt_slider = sliderGrp.SliderGroup()
        self.insert_jnts_amt_slider.setValue(1)
        self.insert_jnts_amt_slider.setRange(1, 10)
        self.insert_jnts_btn = QtWidgets.QPushButton("Insert Joints")

        self.prep_jnts_btn = QtWidgets.QPushButton("Prep Skeleton")

    def createLayouts(self):
        # setup the main layout.
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        save_load_jnt_layout = QtWidgets.QHBoxLayout()
        save_load_jnt_layout.setContentsMargins(0, 0, 0, 0)
        save_load_jnt_layout.setSpacing(4)
        save_load_jnt_layout.addWidget(self.load_jnt_pos_btn)
        save_load_jnt_layout.addWidget(self.save_jnt_pos_btn)

        # setup the joint orientation Layout
        jointOrientation_layout = QtWidgets.QHBoxLayout()
        jointOrientation_layout.addWidget(self.jnt_to_rot_btn)
        jointOrientation_layout.addWidget(self.jnt_to_ori_btn)

        # setup the main mirroe axis joint Layout
        jointMirrorAxis_layout = QtWidgets.QHBoxLayout()
        jointMirrorAxis_layout.addWidget(QtWidgets.QLabel("Axis: "))
        jointMirrorAxis_layout.addWidget(self.jntAxisX_rb)
        jointMirrorAxis_layout.addWidget(self.jntAxisY_rb)
        jointMirrorAxis_layout.addWidget(self.jntAxisZ_rb)

        # setup the main mirrr joint Layout
        mirrorJoint_layout = QtWidgets.QHBoxLayout()
        mirrorJoint_layout.setSpacing(4)
        mirrorJoint_layout.addLayout(jointMirrorAxis_layout)
        mirrorJoint_layout.addWidget(self.mirrorJntMode_cbox)
        mirrorJoint_layout.addWidget(self.mirrorJnt_btn)

        # setup the pin joints layout
        pinJoint_layout = QtWidgets.QHBoxLayout()
        pinJoint_layout.addWidget(self.pin_jnt_btn)
        pinJoint_layout.addWidget(self.unpin_jnt_btn)
        pinJoint_layout.addWidget(self.unpinAll_jnt_btn)

        # setup the insert joints layout
        insertJoint_layout = QtWidgets.QHBoxLayout()
        insertJoint_layout.addWidget(self.insert_jnts_amt_slider)
        insertJoint_layout.addWidget(self.insert_jnts_btn)

        # add widgets to the skeletonEdit widget.
        self.skeletonEdit_wdgt.addWidget(self.clean_skeleton_btn)
        self.skeletonEdit_wdgt.addLayout(jointOrientation_layout)
        self.skeletonEdit_wdgt.addLayout(mirrorJoint_layout)
        self.skeletonEdit_wdgt.addLayout(pinJoint_layout)
        self.skeletonEdit_wdgt.addLayout(insertJoint_layout)
        self.skeletonEdit_wdgt.addWidget(self.prep_jnts_btn)
        self.skeletonEdit_wdgt.addSpacing(3)

        # add widgets to the main skeleton widget.
        self.main_collapseable_widget.addWidget(self.joint_pos_path_selector)
        self.main_collapseable_widget.addLayout(save_load_jnt_layout)
        self.main_collapseable_widget.addWidget(self.skeletonEdit_wdgt)

        # add the widget to the main layout
        self.main_layout.addWidget(self.main_collapseable_widget)

    def createConnections(self):
        self.load_jnt_pos_btn.clicked.connect(self.load_joint_positions)
        self.save_jnt_pos_btn.clicked.connect(self.save_joint_positions)
        self.jnt_to_rot_btn.clicked.connect(self.jnt_to_rotation)
        self.jnt_to_ori_btn.clicked.connect(self.jnt_to_orientation)
        self.mirrorJnt_btn.clicked.connect(self.mirror_joint)
        self.pin_jnt_btn.clicked.connect(self.pin_joints)
        self.unpin_jnt_btn.clicked.connect(self.unpin_joints)
        self.unpinAll_jnt_btn.clicked.connect(self.unpinAll_joints)
        self.insert_jnts_btn.clicked.connect(self.insert_joints)
        self.prep_jnts_btn.clicked.connect(self.prep_skeleton)

    def setBuilder(self, builder):
        rigEnv = builder.get_rig_env()
        self.builder = builder
        self.joint_pos_path_selector.set_relativeTo(rigEnv)

        # update data within the rig
        jointFile = self.builder.getRigData(self.builder.get_rig_file(), SKELETON_POS)
        if jointFile:
            self.joint_pos_path_selector.set_path(jointFile)

    def runWidget(self):
        self.load_joint_positions()

    @property
    def isChecked(self):
        return self.main_collapseable_widget.isChecked()

    # CONNECTIONS
    def load_joint_positions(self):
        self.builder.load_joints(self.joint_pos_path_selector.get_abs_path())

    def save_joint_positions(self):
        # TODO add a check about saving a blank scene.
        self.builder.save_joints(self.joint_pos_path_selector.get_abs_path())

    def pin_joints(self):
        live.pin()

    def unpin_joints(self):
        live.unpin()

    def unpinAll_joints(self):
        pinnedNodes = meta.getTagged("isPinned")
        live.unpin(pinnedNodes)

    def insert_joints(self):
        jnt_amt = self.insert_jnts_amt_slider.getValue()
        selection = cmds.ls(sl=True)
        assert len(selection) == 2, "Must select two joints!"
        rigamajig2.maya.joint.insertJoints(selection[0], selection[-1], amount=jnt_amt)

    def prep_skeleton(self):
        joint.addJointOrientToChannelBox(cmds.ls(sl=True))
        rigamajig2.maya.joint.toOrientation(cmds.ls(sl=True))

    def mirror_joint(self):
        """ mirror joint"""
        axis = 'x'
        if self.jntAxisY_rb.isChecked():
            axis = 'y'
        if self.jntAxisZ_rb.isChecked():
            axis = 'z'

        mirrorMode = self.mirrorJntMode_cbox.currentText()
        for joint in cmds.ls(sl=True):
            joints = cmds.listRelatives(cmds.ls(sl=True, type='joint'), ad=True, type='joint') or []
            rigamajig2.maya.joint.mirror(joints + [joint], axis=axis, mode=mirrorMode)

    def jnt_to_rotation(self):
        rigamajig2.maya.joint.toRotation(cmds.ls(sl=True, type='joint'))

    def jnt_to_orientation(self):
        rigamajig2.maya.joint.toOrientation(cmds.ls(sl=True, type='joint'))