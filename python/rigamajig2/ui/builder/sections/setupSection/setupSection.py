#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: setup_section.py
    author: masonsmigel
    date: 07/2022
    description: 
"""
import logging

import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets

from rigamajig2.maya import meta
from rigamajig2.maya.builder import componentManager
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import dataIO
from rigamajig2.shared import common
from rigamajig2.ui.builder import style
from rigamajig2.ui.builder.customs import section, dataLoader
from rigamajig2.ui.builder.sections.setupSection.customs import componentTree
from rigamajig2.ui.resources import Resources
from rigamajig2.ui.widgets import QPushButton, mayaMessageBox

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SetupSection(section.BuilderSection):
    """Initalize layout for the builder UI"""

    WIDGET_TITLE = "Setup Rig"

    def createWidgets(self):
        """Create Widgets"""
        self.componentsDataLoader = dataLoader.DataLoader(
            label="Components:",
            caption="Select a Component File",
            fileFilter=common.JSON_FILTER,
            fileMode=1,
            dataFilteringEnabled=True,
            dataFilter=["AbstractData", "ComponentData"],
        )
        self.loadComponentsButton = QtWidgets.QPushButton("Load Cmpts")
        self.loadComponentsButton.setIcon(Resources.getIcon(":loadComponents.png"))
        self.appendComponentsButton = QtWidgets.QPushButton("Append Cmpts")
        self.saveComponentsButton = QtWidgets.QPushButton("Save Cmpts")
        self.saveComponentsButton.setIcon(Resources.getIcon(":saveComponents.png"))
        self.addComponentsButton = QtWidgets.QPushButton("Add Components")
        self.addComponentsButton.setIcon(Resources.getIcon(":freeformOff.png"))

        self.loadComponentsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveComponentsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.addComponentsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadComponentsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveComponentsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.addComponentsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.componentManager = componentTree.ComponentTree()

        self.initalizeBuildButton = QtWidgets.QPushButton("Guide Components")
        self.initalizeBuildButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.guideDataLoader = dataLoader.DataLoader(
            label="Guides:",
            caption="Select a guide file",
            fileFilter=common.JSON_FILTER,
            fileMode=1,
            dataFilteringEnabled=True,
            dataFilter=["JointData", "GuideData"],
        )
        self.loadGuidesButton = QtWidgets.QPushButton("Load Guides")
        self.loadGuidesButton.setIcon(Resources.getIcon(":loadGuides"))
        self.saveGuidesButton = QPushButton.RightClickableButton("Save Guides")
        self.saveGuidesButton.setIcon(Resources.getIcon(":saveGuides"))
        self.saveGuidesButton.setToolTip(
            "Left Click: Save guides into their source file. (new data appended to last item)"
            "\nRight Click: Save all guides to a new file overriding parents"
        )

        self.loadGuidesButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveGuidesButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadGuidesButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveGuidesButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

    def createLayouts(self):
        """Create Layouts"""
        # setup the main layout.
        self.mainWidget.addWidget(self.componentsDataLoader)

        componentButtonLayout = QtWidgets.QHBoxLayout()
        componentButtonLayout.setSpacing(4)

        guideLoadLayout = QtWidgets.QHBoxLayout()
        guideLoadLayout.addWidget(self.loadGuidesButton)
        guideLoadLayout.addWidget(self.saveGuidesButton)

        loadComponentsLayout = QtWidgets.QHBoxLayout()
        loadComponentsLayout.addWidget(self.loadComponentsButton)
        loadComponentsLayout.addWidget(self.saveComponentsButton)
        loadComponentsLayout.addWidget(self.addComponentsButton)
        self.mainWidget.addLayout(loadComponentsLayout)

        self.mainWidget.addWidget(self.componentManager)
        self.mainWidget.addWidget(self.initalizeBuildButton)
        self.mainWidget.addLayout(componentButtonLayout)
        self.mainWidget.addWidget(self.guideDataLoader)
        self.mainWidget.addLayout(guideLoadLayout)

    def createConnections(self):
        """Create Connections"""
        self.componentsDataLoader.filesUpdated.connect(self._setComponentFiles)
        self.guideDataLoader.filesUpdated.connect(self._setGuideFiles)

        self.loadGuidesButton.clicked.connect(self._onLoadGuides)
        self.saveGuidesButton.leftClicked.connect(self._onSaveGuides)
        self.saveGuidesButton.rightClicked.connect(self._onSaveGuidesAsOverride)
        self.loadComponentsButton.clicked.connect(self._onLoadComponents)
        self.saveComponentsButton.clicked.connect(self._onSaveComponents)

        self.addComponentsButton.clicked.connect(self.componentManager.showAddComponentDialog)
        self.initalizeBuildButton.clicked.connect(self._initalizeRig)

    def _setBuilder(self, builder):
        """Set a builder for intialize widget"""
        super()._setBuilder(builder)

        self.componentsDataLoader.clear()
        self.guideDataLoader.clear()
        self.componentManager.clearTree()

        self.componentsDataLoader.setRelativePath(self.builder.getRigEnvironment())
        self.guideDataLoader.setRelativePath(self.builder.getRigEnvironment())
        self.componentManager.setRigBuilder(self.builder)

        # update data within the rig
        cmptsFiles = self.builder.getRigData(self.builder.getRigFile(), constants.COMPONENTS)
        self.componentsDataLoader.selectPaths(cmptsFiles)

        guidesFiles = self.builder.getRigData(self.builder.getRigFile(), constants.GUIDES)
        self.guideDataLoader.selectPaths(guidesFiles)

    def _runWidget(self):
        """Run this widget from the builder breakpoint runner"""
        self._onLoadComponents()
        self._initalizeRig()
        self._onLoadGuides()

    # CONNECTIONS
    @QtCore.Slot()
    def _onLoadComponents(self):
        """Load component setup from json using the builder"""
        self.builder.setComponents(list())
        # load the components from the file. then initialize them
        self.builder.loadComponents()
        self.builder.initialize()

        self.componentManager.loadListFromBuilder()

    @QtCore.Slot()
    def _onSaveComponents(self):
        """Save component setup from json using the builder"""
        dataIO.saveComponents(self.builder, self.componentsDataLoader.getFileList(absolute=True))

    @QtCore.Slot()
    def _onLoadGuides(self):
        """Load guide setup to json using the builder"""

        self.builder.loadGuides()

    @QtCore.Slot()
    def _onSaveGuides(self):
        """Save guides setup to json using the builder"""
        if not self.__validateGuidesInScene():
            return
        dataIO.saveGuides(self.guideDataLoader.getFileList(absolute=True), method="merge")

    @QtCore.Slot()
    def _onSaveGuidesAsOverride(self):
        """Save all guide data as an override"""
        if not self.__validateGuidesInScene():
            return

        fileResults = cmds.fileDialog2(
            ds=2,
            cap="Save Guides to override file",
            ff="Json Files (*.json)",
            okc="Select",
            fileMode=0,
            dir=self.builder.getRigEnvironment(),
        )

        fileName = fileResults[0] if fileResults else None

        savedFiles = dataIO.saveGuides(
            self.guideDataLoader.getFileList(absolute=True), method="overwrite", fileName=fileName
        )
        currentFiles = self.guideDataLoader.getFileList(absolute=True)

        newFiles = set(savedFiles) - set(currentFiles)
        self.jointPositionDataLoader.selectPaths(newFiles)

    def __validateGuidesInScene(self):
        """Check to make sure the guides exist in the scene and look to see if the the rig is build"""
        if len(meta.getTagged("guide")) < 1:
            confirm = mayaMessageBox.MayaMessageBox(
                title="Save Guides", message="There are no guides in the scene. Are you sure you want to continue?"
            )
            confirm.setWarning()
            confirm.setButtonsYesNoCancel()

            return confirm.getResult()
        return True

    @QtCore.Slot()
    def _initalizeRig(self):
        """Run the comppnent intialize on the builder and update the UI"""
        self.builder.guide()
        self.componentManager._loadFromScene()

    @QtCore.Slot()
    def _setComponentFiles(self, fileList):
        if self.builder:
            self.builder.componentFiles = fileList
            self.postRigFileModifiedEvent()

    @QtCore.Slot()
    def _setGuideFiles(self, fileList):
        if self.builder:
            self.builder.guideFiles = fileList
            self.postRigFileModifiedEvent()

    def closeEvent(self, *args, **kwargs):
        self.componentManager._teardownCallbacks()


def _getComponentIcon(componentType):
    """get the component icon from the module.Class of the component"""
    return Resources.getIcon(":icons/components/{}".format(componentType.split(".")[0]))


def _getComponentColor(cmpt):
    """get the ui color for the component"""
    tmpComponentObj = componentManager.createComponentClassInstance(cmpt)
    uiColor = tmpComponentObj.UI_COLOR
    # after we get the UI color we can delete the tmp component instance
    del tmpComponentObj
    return uiColor
