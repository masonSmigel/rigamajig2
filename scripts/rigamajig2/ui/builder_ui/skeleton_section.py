#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: skeleton_section.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
import logging

import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import rigamajig2.maya.joint
import rigamajig2.maya.meta as meta
import rigamajig2.maya.rig.live as live
from rigamajig2.maya import decorators
from rigamajig2.maya import naming
from rigamajig2.maya.builder.constants import SKELETON_POS
from rigamajig2.maya.cmpts.base import GUIDE_STEP
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui import style
from rigamajig2.ui.builder_ui.widgets import dataLoader, builderSection
from rigamajig2.ui.widgets import QPushButton, Qslider, mayaMessageBox

logger = logging.getLogger(__name__)


# pylint: disable= too-many-instance-attributes
class SkeletonSection(builderSection.BuilderSection):
    """ Joint layout for the builder UI """

    WIDGET_TITLE = "Skeleton"

    def createWidgets(self):
        """ Create Widgets"""
        self.jointPositionDataLoader = dataLoader.DataLoader(
            "Joint Positions: ",
            caption="Select a Skeleton position file",
            fileFilter=common.JSON_FILTER,
            fileMode=1,
            dataFilteringEnabled=True,
            dataFilter=["JointData"]
            )
        self.loadJointPositionButton = QtWidgets.QPushButton("Load joints")
        self.loadJointPositionButton.setIcon(QtGui.QIcon(common.getIcon("loadJoints.png")))
        self.saveJointPositionButton = QPushButton.RightClickableButton("Save joints")
        self.saveJointPositionButton.setIcon(QtGui.QIcon(common.getIcon("saveJoints.png")))
        self.saveJointPositionButton.setToolTip(
            "Left Click: Save joints into their source file. (new data appended to last item)"
            "\nRight Click: Save all joints to a new file overriding parents")

        self.loadJointPositionButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveJointPositionButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadJointPositionButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveJointPositionButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.skeletonEditWidget = rigamajig2.ui.widgets.collapseableWidget.CollapsibleWidget('Edit Skeleton')
        self.skeletonEditWidget.setHeaderBackground(style.EDIT_BG_HEADER_COLOR)
        self.skeletonEditWidget.setDarkPallete()

        self.jointToRotationButton = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Rotation")
        self.jointToOrientationButton = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Orientation")
        self.cleanSkeletonButton = QtWidgets.QPushButton("Clean Skeleton")
        self.jointAxisXRadioButton = QtWidgets.QRadioButton('x')
        self.jointAxisYRadioButton = QtWidgets.QRadioButton('y')
        self.jointAxisZRadioButton = QtWidgets.QRadioButton('z')
        self.jointAxisXRadioButton.setChecked(True)

        self.mirrorJointModeCheckbox = QtWidgets.QComboBox()
        self.mirrorJointModeCheckbox.setFixedHeight(24)
        self.mirrorJointModeCheckbox.addItem("rotate")
        self.mirrorJointModeCheckbox.addItem("translate")
        self.mirrorJointsButton = QtWidgets.QPushButton(QtGui.QIcon(":kinMirrorJoint_S"), "Mirror")
        self.mirrorJointsButton.setFixedHeight(24)

        self.pinJointsButton = QtWidgets.QPushButton("Pin Joints")
        self.pinJointsButton.setIcon(QtGui.QIcon(":pinned"))
        self.unpinJointsButton = QtWidgets.QPushButton("Un-Pin Joints")
        self.unpinJointsButton.setIcon(QtGui.QIcon(":unpinned"))

        self.unpinAllJointsButton = QtWidgets.QPushButton("Un-Pin All Joints")
        self.unpinAllJointsButton.setIcon(QtGui.QIcon(":unpinned"))

        self.insertJointsAmountSlider = Qslider.QSlider()
        self.insertJointsAmountSlider.setValue(1)
        self.insertJointsAmountSlider.setRange(1, 10)
        self.insertJointsButton = QtWidgets.QPushButton("Insert Joints")

    def createLayouts(self):
        """ Create Layouts"""

        saveLoadJointLayout = QtWidgets.QHBoxLayout()
        saveLoadJointLayout.setContentsMargins(0, 0, 0, 0)
        saveLoadJointLayout.setSpacing(4)
        saveLoadJointLayout.addWidget(self.loadJointPositionButton)
        saveLoadJointLayout.addWidget(self.saveJointPositionButton)

        # setup the joint orientation Layout
        jointOrientationLayout = QtWidgets.QHBoxLayout()
        jointOrientationLayout.addWidget(self.jointToRotationButton)
        jointOrientationLayout.addWidget(self.jointToOrientationButton)

        # setup the main mirror axis joint Layout
        jointMirrorAxisLayout = QtWidgets.QHBoxLayout()
        jointMirrorAxisLayout.addWidget(QtWidgets.QLabel("Axis: "))
        jointMirrorAxisLayout.addWidget(self.jointAxisXRadioButton)
        jointMirrorAxisLayout.addWidget(self.jointAxisYRadioButton)
        jointMirrorAxisLayout.addWidget(self.jointAxisZRadioButton)

        # setup the main mirrr joint Layout
        mirrorJointLayout = QtWidgets.QHBoxLayout()
        mirrorJointLayout.setSpacing(4)
        mirrorJointLayout.addLayout(jointMirrorAxisLayout)
        mirrorJointLayout.addWidget(self.mirrorJointModeCheckbox)
        mirrorJointLayout.addWidget(self.mirrorJointsButton)

        # setup the pin joints layout
        pinJointsLayout = QtWidgets.QHBoxLayout()
        pinJointsLayout.addWidget(self.pinJointsButton)
        pinJointsLayout.addWidget(self.unpinJointsButton)
        pinJointsLayout.addWidget(self.unpinAllJointsButton)

        # setup the insert joints layout
        insertJointLayout = QtWidgets.QHBoxLayout()
        insertJointLayout.addWidget(self.insertJointsAmountSlider)
        insertJointLayout.addWidget(self.insertJointsButton)

        # add widgets to the skeletonEdit widget.
        self.skeletonEditWidget.addWidget(self.cleanSkeletonButton)
        self.skeletonEditWidget.addLayout(jointOrientationLayout)
        self.skeletonEditWidget.addLayout(mirrorJointLayout)
        self.skeletonEditWidget.addLayout(pinJointsLayout)
        self.skeletonEditWidget.addLayout(insertJointLayout)
        self.skeletonEditWidget.addSpacing(3)

        # add widgets to the main skeleton widget.
        self.mainWidget.addWidget(self.jointPositionDataLoader)
        self.mainWidget.addLayout(saveLoadJointLayout)
        self.mainWidget.addWidget(self.skeletonEditWidget)

    def createConnections(self):
        """ Create Connections"""
        self.cleanSkeletonButton.clicked.connect(self._cleanSkeleton)
        self.loadJointPositionButton.clicked.connect(self._loadJointsPositions)
        self.saveJointPositionButton.leftClicked.connect(self._saveJointPositions)
        self.saveJointPositionButton.rightClicked.connect(self._saveJointPositionAsOverride)
        self.jointToRotationButton.clicked.connect(self._jointToRotation)
        self.jointToOrientationButton.clicked.connect(self._jointToOrientation)
        self.mirrorJointsButton.clicked.connect(self._mirrorJoint)
        self.pinJointsButton.clicked.connect(self._pinJoints)
        self.unpinJointsButton.clicked.connect(self._unpinJoints)
        self.unpinAllJointsButton.clicked.connect(self._unpinAllJoints)
        self.insertJointsButton.clicked.connect(self._insertJoints)

    @QtCore.Slot()
    def _setBuilder(self, builder):
        """ Set a builder for widget"""
        super()._setBuilder(builder)

        self.jointPositionDataLoader.clear()
        self.jointPositionDataLoader.setRelativePath(self.builder.getRigEnviornment())

        # update data within the rig
        jointFiles = self.builder.getRigData(self.builder.getRigFile(), SKELETON_POS)
        self.jointPositionDataLoader.selectPaths(jointFiles)

    @QtCore.Slot()
    def _runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self._loadJointsPositions()

    @QtCore.Slot()
    def _loadJointsPositions(self):
        """ load joints and positions"""
        self.builder.loadJoints(self.jointPositionDataLoader.getFileList())

    @QtCore.Slot()
    def _saveJointPositions(self):
        """ save the joint positions"""
        if not self.__validateJointsInScene():
            return

        self.builder.saveJoints(self.jointPositionDataLoader.getFileList(absolute=True), method="merge")

    @QtCore.Slot()
    def _saveJointPositionAsOverride(self):
        """Save all joints into a new layer. Overriding any joints from lower files."""
        if not self.__validateJointsInScene():
            return

        savedFiles = self.builder.saveJoints(self.jointPositionDataLoader.getFileList(absolute=True),
                                             method="overwrite")
        currentFiles = self.jointPositionDataLoader.getFileList(absolute=True)
        if savedFiles:
            for savedFile in savedFiles:
                if savedFile not in currentFiles:
                    self.jointPositionDataLoader.selectPath(savedFile)

    def __validateJointsInScene(self) -> bool:
        """Check to make sure the joints exist in the scene and look to see if the the rig is build"""
        isBuilt = False
        # find the main_container and check if its past the guide step
        for container in cmds.ls(type="container"):
            if cmds.getAttr("{}.type".format(container)) == "main.main":
                if cmds.getAttr("{}.build_step".format(container)) > GUIDE_STEP:
                    isBuilt = True

        if isBuilt:
            confirm = mayaMessageBox.MayaMessageBox(
                title="Save Joints",
                message="It looks like the rig is already built. Are you sure you want to continue?"
                )
            confirm.setWarning()
            confirm.setButtonsYesNoCancel()

            return confirm.getResult()
        return True

    @QtCore.Slot()
    def _pinJoints(self):
        """ Pin selected joints"""
        live.pin()

    @QtCore.Slot()
    def _unpinJoints(self):
        """ Unpin selected joints"""
        live.unpin()

    @QtCore.Slot()
    def _unpinAllJoints(self):
        """ Unpin all joints"""
        pinnedNodes = meta.getTagged("isPinned")
        live.unpin(pinnedNodes)

    @QtCore.Slot()
    def _insertJoints(self):
        """ insert joints between two selected joints"""
        jointAmount = self.insertJointsAmountSlider.getValue()
        selection = cmds.ls(sl=True)
        assert len(selection) == 2, "Must select two joints!"
        rigamajig2.maya.joint.insertJoints(selection[0], selection[-1], amount=jointAmount)

    @QtCore.Slot()
    @decorators.oneUndo
    def _cleanSkeleton(self):
        """
        clean the skeleton
        """
        skeletonRoots = common.toList(meta.getTagged('skeleton_root'))

        if not skeletonRoots:
            skeletonRoots = cmds.ls(sl=True)

        fullJointList = list()
        for root in skeletonRoots:
            # we need to keep track of the full joint paths and their indivual names to check the naming later
            validJoints = cmds.listRelatives(root, allDescendents=True, type='joint', pa=True) or list()
            # make the list unique
            fullJointList += [x for x in validJoints + [root] if x not in fullJointList]

        for jnt in fullJointList:
            if cmds.listRelatives(jnt, parent=True):
                if meta.hasTag(jnt, tag="skeleton_root"):
                    meta.untag(jnt, tag="skeleton_root")
            else:
                meta.tag(cmds.ls(sl=True), tag="skeleton_root")

            # check if the joint ends with "_bind"
            if jnt.endswith(f"_{common.BINDTAG}"):
                meta.tag(jnt, tag="bind")

            # freeze the joint scales
            cmds.makeIdentity(jnt, s=True, r=True, apply=True)

            # add the joint orient to the channel box
            rigamajig2.maya.joint.addJointOrientToChannelBox(jnt)

            # give a warning if the names arent unique
            if not naming.isUniqueName(jnt.split("|")[-1]):
                logger.warning(f"Joint name is not unique for '{jnt}'")

    @QtCore.Slot()
    def _mirrorJoint(self):
        """ mirror joint"""
        axis = 'x'
        if self.jointAxisYRadioButton.isChecked():
            axis = 'y'
        if self.jointAxisZRadioButton.isChecked():
            axis = 'z'

        mirrorMode = self.mirrorJointModeCheckbox.currentText()
        for joint in cmds.ls(sl=True):
            joints = cmds.listRelatives(cmds.ls(sl=True, type='joint'), allDescendents=True, type='joint') or []
            rigamajig2.maya.joint.mirror(joints + [joint], axis=axis, mode=mirrorMode)

    @QtCore.Slot()
    def _jointToRotation(self):
        """ Convert joint transformation to rotation"""
        rigamajig2.maya.joint.toRotation(cmds.ls(sl=True, type='joint'))

    @QtCore.Slot()
    def _jointToOrientation(self):
        """ Convert joint transformation to orientation"""
        rigamajig2.maya.joint.toOrientation(cmds.ls(sl=True, type='joint'))