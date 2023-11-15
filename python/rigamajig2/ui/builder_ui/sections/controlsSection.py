#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: controls_section.py
    author: masonsmigel
    date: 07/2022
    description: 

"""
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets

import rigamajig2.maya.curve
import rigamajig2.maya.rig.control
from rigamajig2.maya import meta
from rigamajig2.maya.builder import dataIO
from rigamajig2.maya.builder.constants import CONTROL_SHAPES
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui import style
from rigamajig2.ui.builder_ui.widgets import dataLoader, builderSection, overrideColorer
from rigamajig2.ui.resources import Resources
from rigamajig2.ui.widgets import QPushButton, mayaMessageBox


# For this UI its important to have alot of instance attributes
# pylint: disable = too-many-instance-attributes
class ControlsSection(builderSection.BuilderSection):
    """ Controls layout for the builder UI """

    WIDGET_TITLE = "Controls"

    def createWidgets(self):
        """ Create Widgets """
        self.controlDataLoader = dataLoader.DataLoader(
            label="Controls:",
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
        self.loadControlsButton.setIcon(Resources.getIcon(":loadControls.png"))
        self.loadControlsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadControlsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.saveControlsButton = QPushButton.RightClickableButton("Save Controls")
        self.saveControlsButton.setIcon(Resources.getIcon(":saveControls.png"))
        self.saveControlsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveControlsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveControlsButton.setToolTip(
            "Left Click: Save controls into their source file (new data appended to last item)"
            "\nRight Click: Save all controls to a new file overriding parents")

        self.editControlsWidget = rigamajig2.ui.widgets.collapseableWidget.CollapsibleWidget('Edit Controls')
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
        self.mirrorControlButton.setIcon(Resources.getIcon(":mirrorControls.png"))

        self.controlColorOverrideColor = overrideColorer.OverrideColorer()

        self.controlShapeCheckbox = QtWidgets.QComboBox()
        self.controlShapeCheckbox.setFixedHeight(24)
        self.populateAvailableControlShapes()
        self.setControlShapeButton = QtWidgets.QPushButton("Set Shape")

        self.replaceControlButton = QtWidgets.QPushButton("Replace Control Shape ")

    def createLayouts(self):
        """ Create Layouts"""
        self.mainWidget.addWidget(self.controlDataLoader)

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
        self.mainWidget.addLayout(controlButtonLayout)

        # EDIT CONTROL LAYOUT
        self.mainWidget.addWidget(self.editControlsWidget)

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

    def createConnections(self):
        """ Create Connections"""
        self.controlDataLoader.filesUpdated.connect(self._setControlShapeFiles)
        self.loadControlsButton.clicked.connect(self._onLoadControlShapes)
        self.saveControlsButton.leftClicked.connect(self._onSaveControlShapes)
        self.saveControlsButton.rightClicked.connect(self._onSaveControlShapesAsOverwrite)
        self.mirrorControlButton.clicked.connect(self._onMirrorControl)
        self.setControlShapeButton.clicked.connect(self._onSetControlShape)
        self.replaceControlButton.clicked.connect(self._onReplaceControlShape)

    def populateAvailableControlShapes(self) -> None:
        """ Set control shape items"""
        controlShapes = rigamajig2.maya.rig.control.getAvailableControlShapes()
        for controlShape in controlShapes:
            self.controlShapeCheckbox.addItem(controlShape)

    @QtCore.Slot()
    def _setBuilder(self, builder) -> None:
        """ Set a builder for intialize widget"""
        super()._setBuilder(builder)
        self.controlDataLoader.clear()
        self.controlDataLoader.setRelativePath(self.builder.getRigEnvironment())

        # update data within the rig
        controlFiles = self.builder.getRigData(self.builder.getRigFile(), CONTROL_SHAPES)
        self.controlDataLoader.selectPaths(controlFiles)

    @QtCore.Slot()
    def _runWidget(self) -> None:
        """ Run this widget from the builder breakpoint runner"""
        self._onLoadControlShapes()

    # CONNECTIONS
    @QtCore.Slot()
    def _onLoadControlShapes(self) -> None:
        """ Load controlshapes from json using the builder """
        self.builder.loadControlShapes(self.loadColorCheckBox.isChecked())

    def __validateControlsInScene(self) -> bool:
        """
        Validate the scene for proper controls
        """
        if len(meta.getTagged("control")) < 1:
            confirm = mayaMessageBox.MayaMessageBox(title="Save Control Shapes",
                                                    message="There are no controls in the scene. Are you sure you want to continue?")
            confirm.setWarning()
            confirm.setButtonsYesNoCancel()

            return confirm.getResult()
        # if there are controls we can return true
        return True

    @QtCore.Slot()
    def _onSaveControlShapes(self) -> None:
        """ Save controlshapes to json using the builder """
        if not self.__validateControlsInScene():
            return

        dataIO.saveControlShapes(self.controlDataLoader.getFileList(absolute=True), method="merge")

    @QtCore.Slot()
    def _onSaveControlShapesAsOverwrite(self) -> None:
        """
        Save all controls to a new layer, overwriting existing layers
        """

        if not self.__validateControlsInScene():
            return
        fileResults = cmds.fileDialog2(
            ds=2,
            cap="Save Controls to override file",
            ff="Json Files (*.json)",
            okc="Select",
            fileMode=0,
            dir=self.builder.getRigEnvironment()
        )

        fileName = fileResults[0] if fileResults else None

        savedFiles = dataIO.saveControlShapes(
            self.controlDataLoader.getFileList(absolute=True),
            method="overwrite",
            fileName=fileName
        )
        currentFiles = self.controlDataLoader.getFileList(absolute=True)

        newFiles = set(savedFiles) - set(currentFiles)
        self.jointPositionDataLoader.selectPaths(newFiles)

    @QtCore.Slot()
    def _onMirrorControl(self) -> None:
        """ Mirror a control shape """
        axis = 'x'
        if self.controlAxisYRadioButton.isChecked():
            axis = 'y'
        if self.controlAxisZRadioButton.isChecked():
            axis = 'z'
        mirrorMode = self.mirrorControlModeComboBox.currentText()
        rigamajig2.maya.curve.mirror(cmds.ls(sl=True, type='transform'), axis=axis, mode=mirrorMode)

    @QtCore.Slot()
    def _onSetControlShape(self) -> None:
        """Set the control shape of the selected node"""
        shape = self.controlShapeCheckbox.currentText()
        for node in cmds.ls(sl=True, type='transform'):
            rigamajig2.maya.rig.control.setControlShape(node, shape)

    @QtCore.Slot()
    def _onReplaceControlShape(self) -> None:
        """Replace the control shape"""
        selection = cmds.ls(sl=True, type='transform')
        if len(selection) >= 2:
            for dest in selection[1:]:
                if cmds.listRelatives(dest, shapes=True, pa=True):
                    for shape in cmds.listRelatives(dest, shapes=True, pa=True):
                        cmds.delete(shape)
                rigamajig2.maya.curve.copyShape(selection[0], dest)

    @QtCore.Slot()
    def _setControlShapeFiles(self, fileList):
        if self.builder:
            self.builder.controlShapeFiles = fileList
            self.postRigFileModifiedEvent()
