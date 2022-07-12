#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: controls_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
import rigamajig2.maya.curve
import rigamajig2.maya.rig.control
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, overrideColorer
from rigamajig2.ui.builder_ui import constants
from rigamajig2.maya.rig_builder.builder import CONTROL_SHAPES


class ControlsWidget(QtWidgets.QWidget):

    def __init__(self, builder=None):
        super(ControlsWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.ctlShape_wdgt = collapseableWidget.CollapsibleWidget('Controls', addCheckbox=True)
        self.ctl_path_selector = pathSelector.PathSelector(
            "Controls:",
            cap="Select a Control Shape file",
            ff=constants.JSON_FILTER,
            fm=1
            )
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

    def createLayouts(self):
        # setup the main layout.
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # MAIN CONTROL LAYOUT
        self.ctlShape_wdgt.addWidget(self.ctl_path_selector)

        # create the load color checkbox
        load_color_label = QtWidgets.QLabel("Load Color:")
        load_color_label.setFixedWidth(60)

        # setup the load option layout
        control_btn_layout = QtWidgets.QHBoxLayout()
        control_btn_layout.setSpacing(4)
        control_btn_layout.addWidget(load_color_label)
        control_btn_layout.addWidget(self.load_color_cb)
        control_btn_layout.addWidget(self.load_ctl_btn)
        control_btn_layout.addWidget(self.save_ctl_btn)
        self.ctlShape_wdgt.addLayout(control_btn_layout)

        # EDIT CONTROL LAYOUT
        self.ctlShape_wdgt.addWidget(self.controlEdit_wgt)

        # setup the mirror axis layout
        controlMirrorAxis_layout = QtWidgets.QHBoxLayout()
        controlMirrorAxis_layout.addWidget(QtWidgets.QLabel("Axis: "))
        controlMirrorAxis_layout.addWidget(self.ctlAxisX_rb)
        controlMirrorAxis_layout.addWidget(self.ctlAxisY_rb)
        controlMirrorAxis_layout.addWidget(self.ctlAxisZ_rb)

        # setup the mirror controlLayout
        mirrorControl_layout = QtWidgets.QHBoxLayout()
        mirrorControl_layout.setSpacing(4)
        mirrorControl_layout.addLayout(controlMirrorAxis_layout)
        mirrorControl_layout.addWidget(self.mirrorCtlMode_cbox)
        mirrorControl_layout.addWidget(self.mirror_control_btn)
        self.controlEdit_wgt.addLayout(mirrorControl_layout)

        # add the override color layout
        self.controlEdit_wgt.addWidget(self.ctlColor_ovrcol)

        # setup the control shape layout
        setControlShape_layout = QtWidgets.QHBoxLayout()
        setControlShape_layout.addWidget(self.ctlShape_cbox)
        setControlShape_layout.addWidget(self.setCtlShape_btn)
        self.controlEdit_wgt.addLayout(setControlShape_layout)

        # add the replace control button
        self.controlEdit_wgt.addWidget(self.replace_ctl_btn)

        # add the widget to the main layout
        self.main_layout.addWidget(self.ctlShape_wdgt)

    def createConnections(self):
        self.load_ctl_btn.clicked.connect(self.load_controlShapes)
        self.save_ctl_btn.clicked.connect(self.save_controlShapes)
        self.mirror_control_btn.clicked.connect(self.mirror_control)
        self.setCtlShape_btn.clicked.connect(self.set_controlShape)
        self.replace_ctl_btn.clicked.connect(self.replace_controlShape)

    def setBuilder(self, builder):
        rigEnv = builder.get_rig_env()
        self.builder = builder
        self.ctl_path_selector.set_relativeTo(rigEnv)

        # update data within the rig
        controlFile = self.builder.get_rig_data(self.builder.get_rig_file(), CONTROL_SHAPES)
        if controlFile:
            self.ctl_path_selector.set_path(controlFile)

    def runWidget(self):
        self.load_controlShapes()

    @property
    def isChecked(self):
        return self.ctlShape_wdgt.isChecked()

    def set_ctlShape_items(self):
        control_shapes = rigamajig2.maya.rig.control.getAvailableControlShapes()
        for control_shape in control_shapes:
            self.ctlShape_cbox.addItem(control_shape)

    # CONNECTIONS
    def load_controlShapes(self):
        self.builder.load_controlShapes(self.ctl_path_selector.get_abs_path(), self.load_color_cb.isChecked())

    def save_controlShapes(self):
        self.builder.save_controlShapes(self.ctl_path_selector.get_abs_path())

    def mirror_control(self):
        axis = 'x'
        if self.ctlAxisY_rb.isChecked():
            axis = 'y'
        if self.ctlAxisZ_rb.isChecked():
            axis = 'z'
        mirrorMode = self.mirrorCtlMode_cbox.currentText()
        rigamajig2.maya.curve.mirror(cmds.ls(sl=True, type='transform'), axis=axis, mode=mirrorMode)

    def set_controlShape(self):
        """Set the control shape of the selected node"""
        shape = self.ctlShape_cbox.currentText()
        for node in cmds.ls(sl=True, type='transform'):
            rigamajig2.maya.rig.control.setControlShape(node, shape)

    def replace_controlShape(self):
        """Replace the control shape"""
        selection = cmds.ls(sl=True, type='transform')
        if len(selection) >= 2:
            for dest in selection[1:]:
                if cmds.listRelatives(dest, shapes=True, pa=True):
                    for shape in cmds.listRelatives(dest, shapes=True, pa=True):
                        cmds.delete(shape)
                rigamajig2.maya.curve.copyShape(selection[0], dest)