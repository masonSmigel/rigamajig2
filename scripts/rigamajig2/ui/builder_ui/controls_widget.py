#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: controls_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# MAYA
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
from rigamajig2.shared import common
from rigamajig2.maya import meta
import rigamajig2.maya.curve
import rigamajig2.maya.rig.control
from rigamajig2.ui.widgets import dataLoader, collapseableWidget, overrideColorer
from rigamajig2.ui.builder_ui import style
from rigamajig2.maya.builder.constants import CONTROL_SHAPES


# For this UI its important to have alot of instance attributes
# pylint: disable = too-many-instance-attributes
class ControlsWidget(QtWidgets.QWidget):
    """ Controls layout for the builder UI """

    def __init__(self, builder=None):
        super(ControlsWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets """
        self.mainCollapseableWidget = collapseableWidget.CollapsibleWidget('Controls', addCheckbox=True)
        self.controlDataLoader = dataLoader.DataLoader(
            "Controls:",
            caption="Select a Control Shape file",
            fileFilter=common.JSON_FILTER,
            fileMode=1,
            dataFilteringEnabled=True,
            dataFilter=["CurveData"]
            )
        self.loadColorCheckBox = QtWidgets.QCheckBox()
        self.loadColorCheckBox.setChecked(True)
        self.loadColorCheckBox.setFixedWidth(25)
        self.loadControlsButton = QtWidgets.QPushButton("Load Controls")
        self.loadControlsButton.setIcon(QtGui.QIcon(common.getIcon("loadControls.png")))
        self.loadControlsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadControlsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.saveControlsButton = QtWidgets.QPushButton("Save Controls")
        self.saveControlsButton.setIcon(QtGui.QIcon(common.getIcon("saveControls.png")))
        self.saveControlsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveControlsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.editControlsWidget = collapseableWidget.CollapsibleWidget('Edit Controls')
        self.editControlsWidget.setHeaderBackground(style.EDIT_BG_HEADER_COLOR)
        self.editControlsWidget.setDarkPallete()

        self.controlAxisXRadioButton = QtWidgets.QRadioButton('x')
        self.controlAxisXRadioButton.setChecked(True)
        self.controlAxisYRadioButton = QtWidgets.QRadioButton('y')
        self.controlAxisZRadioButton = QtWidgets.QRadioButton('z')
        self.mirrorControlModeComboBox = QtWidgets.QComboBox()
        self.mirrorControlModeComboBox.setFixedHeight(24)
        self.mirrorControlModeComboBox.addItem("replace")
        self.mirrorControlModeComboBox.addItem("match")
        self.mirrorControlButton = QtWidgets.QPushButton("Mirror")
        self.mirrorControlButton.setIcon(QtGui.QIcon(common.getIcon("mirrorControls.png")))

        self.controlColorOverrideColor = overrideColorer.OverrideColorer()

        self.controlShapeCheckbox = QtWidgets.QComboBox()
        self.controlShapeCheckbox.setFixedHeight(24)
        self.setAvailableControlShapes()
        self.setControlShapeButton = QtWidgets.QPushButton("Set Shape")

        self.replaceControlButton = QtWidgets.QPushButton("Replace Control Shape ")

    def createLayouts(self):
        """ Create Layouts"""
        # setup the main layout.
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        # MAIN CONTROL LAYOUT
        self.mainCollapseableWidget.addWidget(self.controlDataLoader)

        # create the load color checkbox
        loadColorLabel = QtWidgets.QLabel("Load Color:")
        loadColorLabel.setFixedWidth(60)

        # setup the load option layout
        controlButtonLayout = QtWidgets.QHBoxLayout()
        controlButtonLayout.setSpacing(4)
        controlButtonLayout.addWidget(loadColorLabel)
        controlButtonLayout.addWidget(self.loadColorCheckBox)
        controlButtonLayout.addWidget(self.loadControlsButton)
        controlButtonLayout.addWidget(self.saveControlsButton)
        self.mainCollapseableWidget.addLayout(controlButtonLayout)

        # EDIT CONTROL LAYOUT
        self.mainCollapseableWidget.addWidget(self.editControlsWidget)

        # setup the mirror axis layout
        controlMirrorAxisLayout = QtWidgets.QHBoxLayout()
        controlMirrorAxisLayout.addWidget(QtWidgets.QLabel("Axis: "))
        controlMirrorAxisLayout.addWidget(self.controlAxisXRadioButton)
        controlMirrorAxisLayout.addWidget(self.controlAxisYRadioButton)
        controlMirrorAxisLayout.addWidget(self.controlAxisZRadioButton)

        # setup the mirror controlLayout
        mirrorControlLayout = QtWidgets.QHBoxLayout()
        mirrorControlLayout.setSpacing(4)
        mirrorControlLayout.addLayout(controlMirrorAxisLayout)
        mirrorControlLayout.addWidget(self.mirrorControlModeComboBox)
        mirrorControlLayout.addWidget(self.mirrorControlButton)
        self.editControlsWidget.addLayout(mirrorControlLayout)

        # add the override color layout
        self.editControlsWidget.addWidget(self.controlColorOverrideColor)

        # setup the control shape layout
        setControlShapeLayout = QtWidgets.QHBoxLayout()
        setControlShapeLayout.addWidget(self.controlShapeCheckbox)
        setControlShapeLayout.addWidget(self.setControlShapeButton)
        self.editControlsWidget.addLayout(setControlShapeLayout)

        # add the replace control button
        self.editControlsWidget.addWidget(self.replaceControlButton)
        self.editControlsWidget.addSpacing(3)

        # add the widget to the main layout
        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections"""
        self.loadControlsButton.clicked.connect(self.loadControlShapes)
        self.saveControlsButton.clicked.connect(self.saveControlShapes)
        self.mirrorControlButton.clicked.connect(self.mirrorControl)
        self.setControlShapeButton.clicked.connect(self.setControlShape)
        self.replaceControlButton.clicked.connect(self.replaceControlShape)

    def setBuilder(self, builder):
        """ Set a builder for intialize widget"""
        rigEnv = builder.getRigEnviornment()
        self.builder = builder
        self.controlDataLoader.clear()
        self.controlDataLoader.setRelativePath(rigEnv)

        # update data within the rig
        controlFiles = self.builder.getRigData(self.builder.getRigFile(), CONTROL_SHAPES)
        self.controlDataLoader.selectPaths(controlFiles)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.loadControlShapes()

    @property
    def isChecked(self):
        """ Check it the widget is checked"""
        return self.mainCollapseableWidget.isChecked()

    def setAvailableControlShapes(self):
        """ Set control shape items"""
        controlShapes = rigamajig2.maya.rig.control.getAvailableControlShapes()
        for controlShape in controlShapes:
            self.controlShapeCheckbox.addItem(controlShape)

    # CONNECTIONS
    def loadControlShapes(self):
        """ Load controlshapes from json using the builder """
        self.builder.loadControlShapes(self.controlDataLoader.getFileList(), self.loadColorCheckBox.isChecked())

    def saveControlShapes(self):
        """ Save controlshapes to json using the builder """

        # check if there are controls in the scene before saving.
        if len(meta.getTagged("control")) < 1:
            result = cmds.confirmDialog(
                t='Save Control Shapes',
                message="There are no controls in the scene. Are you sure you want to continue?",
                button=['Cancel', 'Continue'],
                defaultButton='Continue',
                cancelButton='Cancel')

            if result != 'Continue':
                return

        self.builder.saveControlShapes(self.controlDataLoader.getFileList(absolute=True))

    def mirrorControl(self):
        """ Mirror a control shape """
        axis = 'x'
        if self.controlAxisYRadioButton.isChecked():
            axis = 'y'
        if self.controlAxisZRadioButton.isChecked():
            axis = 'z'
        mirrorMode = self.mirrorControlModeComboBox.currentText()
        rigamajig2.maya.curve.mirror(cmds.ls(sl=True, type='transform'), axis=axis, mode=mirrorMode)

    def setControlShape(self):
        """Set the control shape of the selected node"""
        shape = self.controlShapeCheckbox.currentText()
        for node in cmds.ls(sl=True, type='transform'):
            rigamajig2.maya.rig.control.setControlShape(node, shape)

    def replaceControlShape(self):
        """Replace the control shape"""
        selection = cmds.ls(sl=True, type='transform')
        if len(selection) >= 2:
            for dest in selection[1:]:
                if cmds.listRelatives(dest, shapes=True, pa=True):
                    for shape in cmds.listRelatives(dest, shapes=True, pa=True):
                        cmds.delete(shape)
                rigamajig2.maya.curve.copyShape(selection[0], dest)
