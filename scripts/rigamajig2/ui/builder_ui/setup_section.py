#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: setup_section.py
    author: masonsmigel
    date: 07/2022
    description: 

"""
# PYTHON
import ast
import logging
import os
import re
import sys
import typing
from functools import partial

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om2
# MAYA
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2.shiboken2 import wrapInstance

# RIGAMAJIG2
import rigamajig2.shared.common as common
from rigamajig2.maya import attr as attr
from rigamajig2.maya import container as rig_container
from rigamajig2.maya import meta as meta
from rigamajig2.maya import naming as naming
from rigamajig2.maya.builder import builder
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import core
from rigamajig2.maya.builder import data_manager
from rigamajig2.ui.builder_ui import editComponent_dialog
from rigamajig2.ui.builder_ui import style
from rigamajig2.ui.builder_ui.widgets import builderSection, dataLoader
from rigamajig2.ui.widgets import QPushButton, mayaMessageBox

ICON_PATH = os.path.abspath(os.path.join(__file__, '../../../../../icons'))

COMPONENT_ROW_HEIGHT = 20

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SetupSection(builderSection.BuilderSection):
    """ Initalize layout for the builder UI """

    WIDGET_TITLE = "Setup Rig"

    def createWidgets(self):
        """ Create Widgets """
        self.componentsDataLoader = dataLoader.DataLoader(label="Components:",
                                                          caption="Select a Component File",
                                                          fileFilter=common.JSON_FILTER,
                                                          fileMode=1,
                                                          dataFilteringEnabled=True,
                                                          dataFilter=["AbstractData", "ComponentData"])
        self.loadComponentsButton = QtWidgets.QPushButton("Load Cmpts")
        self.loadComponentsButton.setIcon(QtGui.QIcon(common.getIcon("loadComponents.png")))
        self.appendComponentsButton = QtWidgets.QPushButton("Append Cmpts")
        self.saveComponentsButton = QtWidgets.QPushButton("Save Cmpts")
        self.saveComponentsButton.setIcon(QtGui.QIcon(common.getIcon("saveComponents.png")))
        self.addComponentsButton = QtWidgets.QPushButton("Add Components")
        self.addComponentsButton.setIcon(QtGui.QIcon(":freeformOff.png"))

        self.loadComponentsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveComponentsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.addComponentsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadComponentsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveComponentsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.addComponentsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.componentManager = ComponentManager()

        self.initalizeBuildButton = QtWidgets.QPushButton("Guide Components")
        self.initalizeBuildButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.guideDataLoader = dataLoader.DataLoader(label="Guides:",
                                                     caption="Select a guide file",
                                                     fileFilter=common.JSON_FILTER,
                                                     fileMode=1,
                                                     dataFilteringEnabled=True,
                                                     dataFilter=["JointData", "GuideData"])
        self.loadGuidesButton = QtWidgets.QPushButton("Load Guides")
        self.loadGuidesButton.setIcon(QtGui.QIcon(common.getIcon("loadGuides.png")))
        self.saveGuidesButton = QPushButton.RightClickableButton("Save Guides")
        self.saveGuidesButton.setIcon(QtGui.QIcon(common.getIcon("saveGuides.png")))
        self.saveGuidesButton.setToolTip(
            "Left Click: Save guides into their source file. (new data appended to last item)"
            "\nRight Click: Save all guides to a new file overriding parents")

        self.loadGuidesButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveGuidesButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadGuidesButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveGuidesButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

    def createLayouts(self):
        """ Create Layouts"""
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
        """ Create Connections"""
        self.loadGuidesButton.clicked.connect(self._onLoadGuides)
        self.saveGuidesButton.leftClicked.connect(self._onSaveGuides)
        self.saveGuidesButton.rightClicked.connect(self._onSaveGuidesAsOverride)
        self.loadComponentsButton.clicked.connect(self._onLoadComponents)
        self.saveComponentsButton.clicked.connect(self._onSaveComponents)

        self.addComponentsButton.clicked.connect(self.componentManager.showAddComponentDialog)
        self.initalizeBuildButton.clicked.connect(self._initalizeRig)

    def _setBuilder(self, builder):
        """ Set a builder for intialize widget"""
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
        """ Run this widget from the builder breakpoint runner"""
        self._onLoadComponents()
        self._initalizeRig()

    # CONNECTIONS
    @QtCore.Slot()
    def _onLoadComponents(self):
        """ Load component setup from json using the builder """
        self.builder.setComponents(list())
        # load the components from the file. then initialize them
        componentFiles = self.componentsDataLoader.getFileList()
        self.builder.loadComponents(componentFiles)
        self.builder.initialize()

        self.componentManager.loadListFromBuilder()

    @QtCore.Slot()
    def _onSaveComponents(self):
        """ Save component setup from json using the builder """
        # self.builder.loadMetadataToComponentSettings()
        self.builder.saveComponents(self.componentsDataLoader.getFileList(absolute=True))

    @QtCore.Slot()
    def _onLoadGuides(self):
        """ Load guide setup to json using the builder """

        self.builder.loadGuideData(self.guideDataLoader.getFileList())

    @QtCore.Slot()
    def _onSaveGuides(self):
        """ Save guides setup to json using the builder """
        if not self.__validateGuidesInScene():
            return
        data_manager.saveGuideData(self.guideDataLoader.getFileList(absolute=True), method="merge")

    @QtCore.Slot()
    def _onSaveGuidesAsOverride(self):
        """ Save all guide data as an override"""
        if not self.__validateGuidesInScene():
            return

        fileResults = cmds.fileDialog2(
            ds=2,
            cap="Save Guides to override file",
            ff="Json Files (*.json)",
            okc="Select",
            fileMode=0,
            dir=self.builder.getRigEnvironment()
        )

        fileName = fileResults[0] if fileResults else None

        savedFiles = data_manager.saveGuideData(
            self.guideDataLoader.getFileList(absolute=True),
            method="overwrite",
            fileName=fileName
        )
        currentFiles = self.guideDataLoader.getFileList(absolute=True)

        newFiles = set(savedFiles) - set(currentFiles)
        self.jointPositionDataLoader.selectPaths(newFiles)

    def __validateGuidesInScene(self):
        """Check to make sure the guides exist in the scene and look to see if the the rig is build"""
        if len(meta.getTagged("guide")) < 1:
            confirm = mayaMessageBox.MayaMessageBox(
                title="Save Guides",
                message="There are no guides in the scene. Are you sure you want to continue?"
            )
            confirm.setWarning()
            confirm.setButtonsYesNoCancel()

            return confirm.getResult()
        return True

    @QtCore.Slot()
    def _initalizeRig(self):
        """Run the comppnent intialize on the builder and update the UI """
        self.builder.guide()
        self.componentManager._loadFromScene()

    def closeEvent(self, *args, **kwargs):
        self.componentManager._teardownCallbacks()


def _getComponentIcon(cmpt):
    """ get the component icon from the module.Class of the component"""
    return QtGui.QIcon(os.path.join(ICON_PATH, "{}.png".format(cmpt.split('.')[0])))


def _getComponentColor(cmpt):
    """get the ui color for the component"""
    tmpComponentObj = core.createComponentClassInstance(cmpt)
    uiColor = tmpComponentObj.UI_COLOR
    # after we get the UI color we can delte the tmp component instance
    del tmpComponentObj
    return uiColor


class ComponentTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """Tree Widget Item for components"""

    def __init__(self, name, componentType, buildStep='unbuilt', container=None):
        super().__init__()

        self.setSizeHint(0, QtCore.QSize(0, COMPONENT_ROW_HEIGHT))  # set height

        uiColor = _getComponentColor(componentType)

        # set the nessesary text.
        self.setText(0, name)
        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(0, font)
        self.setTextColor(0, QtGui.QColor(*uiColor))

        self.setText(1, componentType)
        self.setText(2, buildStep)

        if container:
            self.setData(0, QtCore.Qt.UserRole, container)

        # set the desaturated color
        destaturatedColor = [v * 0.78 for v in uiColor]
        self.setTextColor(1, QtGui.QColor(*destaturatedColor))
        self.setTextColor(2, QtGui.QColor(156, 156, 156))

        # set the icon
        icon = _getComponentIcon(componentType)
        self.setIcon(0, icon)

    def getData(self) -> typing.Dict[str, typing.Any]:
        """
        return a dictionary of data for the selected item.
        :return: a dictionary of component data
        """
        itemData = dict()
        itemData['name'] = self.text(0)
        itemData['type'] = self.text(1)
        itemData['step'] = self.text(2)
        itemData['container'] = self.data(QtCore.Qt.UserRole, 0)

        return itemData


# pylint: disable=too-many-public-methods
class ComponentManager(QtWidgets.QWidget):
    """
    Component manager wiget used within the intialize Widget
    """
    component_icons = dict()

    def __init__(self, builder=None, *args, **kwargs):
        super(ComponentManager, self).__init__(*args, **kwargs)

        # keep a reference to the current builder
        self.builder = builder

        # store an open edit component dialog in a varriable
        self.editComponentDialog = None

        self.callbackArray = om2.MCallbackIdArray()

        self.createActions()
        self.createWidget()

        self.setMinimumHeight(320)

    def createActions(self):
        """ Create Actions"""
        self.selectContainerAction = QtWidgets.QAction("Select Container", self)
        self.selectContainerAction.setIcon(QtGui.QIcon(":out_container.png"))
        self.selectContainerAction.triggered.connect(self._selectContainer)

        self.editComponentSettingsAction = QtWidgets.QAction("Edit Component Parameters")
        self.editComponentSettingsAction.setIcon(QtGui.QIcon(":toolSettings.png"))
        self.editComponentSettingsAction.triggered.connect(self._editComponentParameters)

        self.renameComponentAction = QtWidgets.QAction("Rename Component", self)
        self.renameComponentAction.setIcon(QtGui.QIcon(":quickRename.png"))
        self.renameComponentAction.triggered.connect(self._renameComponent)

        self.componentHelpAction = QtWidgets.QAction("Help", self)
        self.componentHelpAction.setIcon(QtGui.QIcon(":help.png"))
        self.componentHelpAction.triggered.connect(self._getComponentHelp)

        self.mirrorComponentAction = QtWidgets.QAction("Mirror Component")
        self.mirrorComponentAction.setIcon(QtGui.QIcon(":QR_mirrorGuidesRightToLeft.png"))
        self.mirrorComponentAction.triggered.connect(self._mirrorComponent)

        self.reloadComponentAction = QtWidgets.QAction("Reload Cmpts from Scene", self)
        self.reloadComponentAction.setIcon(QtGui.QIcon(":refresh.png"))
        self.reloadComponentAction.triggered.connect(self._loadFromScene)

        self.deleteComponentAction = QtWidgets.QAction("Delete Cmpt", self)
        self.deleteComponentAction.setIcon(QtGui.QIcon(":trash.png"))
        self.deleteComponentAction.triggered.connect(self._deleteComponent)

    def _createContextMenu(self, position):
        menu = QtWidgets.QMenu(self.componentTree)
        menu.addAction(self.selectContainerAction)
        menu.addAction(self.editComponentSettingsAction)
        menu.addAction(self.renameComponentAction)
        menu.addAction(self.componentHelpAction)
        menu.addSeparator()
        menu.addAction(self.mirrorComponentAction)
        menu.addSeparator()
        menu.addAction(self.reloadComponentAction)
        menu.addAction(self.deleteComponentAction)
        menu.exec_(self.componentTree.mapToGlobal(position))

    def createWidget(self):
        """ Create the Widget"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.minimumSize()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(4)

        # search icon
        searchIcon = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(":hotkeyFieldSearch.png")
        searchIcon.setScaledContents(True)
        searchIcon.setPixmap(pixmap)
        searchIcon.setMinimumSize(20, 15)

        # setup the search bar and completer
        self.searchBar = QtWidgets.QLineEdit()
        self.searchBar.setPlaceholderText("find a component")
        self.searchBar.returnPressed.connect(self._searchForComponent)

        # add the expand and contract widget buttons!
        self.expandWidgetButton = QtWidgets.QPushButton()
        self.expandWidgetButton.setIcon(QtGui.QIcon(":nodeGrapherArrowDown.png"))
        self.expandWidgetButton.setFlat(True)
        self.expandWidgetButton.setFixedSize(15, 20)
        self.expandWidgetButton.setToolTip("Expand Component Manager")
        self.expandWidgetButton.clicked.connect(partial(self.__changeTreeWidgetSize, 40))

        self.contractWidgetButton = QtWidgets.QPushButton()
        self.contractWidgetButton.setIcon(QtGui.QIcon(":nodeGrapherArrowUp.png"))
        self.contractWidgetButton.setFlat(True)
        self.contractWidgetButton.setFixedSize(15, 20)
        self.expandWidgetButton.setToolTip("Contract Component Manager")
        self.contractWidgetButton.clicked.connect(partial(self.__changeTreeWidgetSize, -40))

        # build the search bar layout
        searchBarLayout = QtWidgets.QHBoxLayout()
        searchBarLayout.addWidget(searchIcon)
        searchBarLayout.addWidget(self.searchBar)
        searchBarLayout.addSpacing(20)
        searchBarLayout.addWidget(self.contractWidgetButton)
        searchBarLayout.addWidget(self.expandWidgetButton)

        self.mainLayout.addLayout(searchBarLayout)

        self.searchCompleter = QtWidgets.QCompleter(self)
        self.searchCompleterModel = QtCore.QStringListModel(list(), self)
        self.searchCompleter.setModel(self.searchCompleterModel)

        self.searchBar.setCompleter(self.searchCompleter)

        self.componentTree = QtWidgets.QTreeWidget()
        self.componentTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.componentTree.setHeaderHidden(True)
        self.componentTree.setAlternatingRowColors(True)

        self.componentTree.setIndentation(5)
        self.componentTree.setColumnCount(3)
        self.componentTree.setUniformRowHeights(True)
        self.componentTree.setColumnWidth(0, 160)
        self.componentTree.setColumnWidth(1, 120)
        self.componentTree.setColumnWidth(2, 60)

        self.componentTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.componentTree.customContextMenuRequested.connect(self._createContextMenu)

        self.mainLayout.addWidget(self.componentTree)

    def getAll(self):
        """ get all components in the component tree"""
        return [self.componentTree.topLevelItem(i) for i in range(self.componentTree.topLevelItemCount())]

    def getSelectedItem(self):
        """ get the selected items in the component tree"""
        return [item for item in self.componentTree.selectedItems()]

    def _setupCallbacks(self):
        """
        Setup callbacks
        """
        # if a new scene is opened refresh the builder ui
        self.callbackArray.append(om2.MSceneMessage.addCallback(om2.MSceneMessage.kAfterNew, self._loadFromScene))

        # we also want to update the callbacks whenever we update a step on the components.
        # since all the componts activate a container update when the container changes
        self.callbackArray.append(om2.MEventMessage.addEventCallback("currentContainerChange", self._loadFromScene))

        logger.debug(f"Setup Callbacks: {self.callbackArray}")

    def _teardownCallbacks(self):
        """ Teardown the callbacks we created"""
        logger.debug(f"Teardown Callbacks: {self.callbackArray}")

        om2.MEventMessage.removeCallbacks(self.callbackArray)
        self.callbackArray.clear()

    def _addItemToAutoComplete(self, name):
        # add the item to the search bar if it isnt there already
        stringList = self.searchCompleterModel.stringList()
        if name not in stringList:
            newStringList = stringList + [name]
            self.searchCompleterModel.setStringList(newStringList)

    def createComponent(self, name, componentType, input, rigParent):
        """
        Create a new component.
        This will both add it to the active builder the the tree widget UI
        :param name: name of the component
        :param componentType: component type
        :param input: component inputs
        :param rigParent: component rigParent
        :return:
        """
        componentObject = core.createComponentClassInstance(componentType)
        cmpt = componentObject(name=name, input=ast.literal_eval(str(input)), rigParent=rigParent)

        item = ComponentTreeWidgetItem(name=name,
                                       componentType=componentType,
                                       container=cmpt.getContainer()
                                       )
        self.componentTree.addTopLevelItem(item)
        self.builder.componentList.append(cmpt)
        self._addItemToAutoComplete(name=name)

        cmpt.initializeComponent()
        return cmpt

    def _loadFromScene(self, *args):
        """ Load exisiting components from the scene"""
        components = meta.getTagged('component')

        # check the list of components and see if the components exist and are
        # the same amount as the builder component list
        realComponents = [x for x in components if cmds.objExists(x)]
        predictedComponents = len(self.builder.getComponentList()) or 0
        if not len(realComponents) == predictedComponents:
            self.loadListFromBuilder()

        # if there are NO real components then clear the whole tree
        if len(realComponents) == 0:
            self.clearTree()

        for component in components:
            name = cmds.getAttr("{}.name".format(component))
            buildStepList = cmds.attributeQuery("build_step", n=component, le=True)[0].split(":")
            buildStep = buildStepList[cmds.getAttr("{}.build_step".format(component))]
            isSubComponent = meta.hasTag(component, "subComponent")
            if not isSubComponent:
                # look through the list of components and update the component build steps.
                # This is in a try except block because it will sometimes give an runtime error about a delete widget.
                componentItem = self.componentTree.findItems(name, QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
                if componentItem:
                    componentItem[0].setText(2, buildStep)
                    componentItem[0].setData(QtCore.Qt.UserRole, 0, component)

    def getComponentObj(self, item=None):
        """ Get the component object instance from the builder based on the item in the tree widget. """
        if not item:
            item = self.getSelectedItem()[0]

        itemDict = item.getData()
        component = self.builder.findComponent(itemDict['name'])
        return component

    def resetComponentDialogInstance(self):
        """ Set the instance of the component dialog back to None. This way we know when it must be re-created"""
        self.editComponentDialog = None

    def setRigBuilder(self, builder):
        """ Set a new Rig Builder"""
        self.builder = builder

    def loadListFromBuilder(self):
        """ Load the component list from the builder"""
        # reset the tree and autocompletes
        self.clearTree()

        if not self.builder:
            raise RuntimeError("No valid rig builder found")
        for component in self.builder.getComponentList():
            name = component.name
            componentType = component.componentType
            buildStepString = ['unbuilt', 'initialize', 'guide', 'build', 'connect', 'finalize', 'optimize']
            buildStep = buildStepString[component.getStep()]

            item = ComponentTreeWidgetItem(name=name, componentType=componentType, buildStep=buildStep)
            self.componentTree.addTopLevelItem(item)

    @QtCore.Slot()
    def _selectContainer(self):
        """ Select the container node of the selected components """
        cmds.select(cl=True)
        for item in self.getSelectedItem():
            itemDict = item.getData()
            cmds.select(itemDict['container'], add=True)

    @QtCore.Slot()
    def _editComponentParameters(self):
        """ Open the Edit component parameters dialog"""

        if not self.editComponentDialog:
            self.editComponentDialog = editComponent_dialog.EditComponentDialog()
            self.editComponentDialog.windowClosedSignal.connect(self.resetComponentDialogInstance)
            self.editComponentDialog.show()
        else:
            self.editComponentDialog.raise_()
            self.editComponentDialog.activateWindow()

        # set dialog to the current item
        self.editComponentDialog.setComponent(self.getComponentObj())

    @QtCore.Slot()
    def _mirrorComponent(self):

        selectedComponent = self.getComponentObj()

        guessMirrorName = common.getMirrorName(selectedComponent.name)
        componentNameList = [comp.name for comp in self.builder.componentList]
        if guessMirrorName in componentNameList:
            self._mirrorComponentParameters(selectedComponent)
            logger.info(f"Mirrored component Parameters: '{selectedComponent.name}' -> '{guessMirrorName}'")
        else:
            self._createMirroredComponent(selectedComponent)
            logger.info(f"Created Mirrored component: '{guessMirrorName}'")

    def _createMirroredComponent(self, component):
        """ Create a mirrored component"""

        guessMirrorName = common.getMirrorName(component.name)
        componentType = component.componentType

        # mirror the input
        mirroredInput = list()
        for x in component.input:
            value = common.getMirrorName(x) if common.getMirrorName(x) else x
            mirroredInput.append(value)

        # get a mirrored rigParent
        sourceRigParent = component.rigParent
        mirroredRigParent = common.getMirrorName(sourceRigParent) or sourceRigParent

        mirroredComponent = self.createComponent(guessMirrorName, componentType, mirroredInput, mirroredRigParent)

        # We need to force the component to intialize so we can mirror stuff
        mirroredComponent.initializeComponent()
        self._mirrorComponentParameters(component)

        # update the ui
        self._loadFromScene()

    @QtCore.Slot()
    def _mirrorComponentParameters(self, sourceComponent=None):
        """
        Mirror the component parameters for the selected parameter

        NOTE: the mirror script does not support nested lists or dictonaries.
        """
        if not sourceComponent:
            sourceComponent = self.getComponentObj()

        # find the mirrored component
        guessMirrorName = common.getMirrorName(sourceComponent.name)
        mirrorComponent = self.builder.findComponent(guessMirrorName)

        if not mirrorComponent:
            logger.warning("No mirror found for: {}".format(sourceComponent.name))
            return

        # get the original data. We will use this to create the mirrored data.
        sourceMetaNode = meta.MetaNode(sourceComponent.getContainer())
        sourceData = sourceMetaNode.getAllData()

        mirrorMetaNode = meta.MetaNode(mirrorComponent.getContainer())
        for parameter in list(sourceData.keys()):
            # there are some keys we dont need to mirror. we can skip them
            if parameter in ['type', 'name', 'build_step', "__component__", "__version__", "component_side"]:
                continue

            sourceValue = sourceData[parameter]
            # check if the source value is a string. if it is try to mirror it.
            if isinstance(sourceValue, (str, common.UNICODE)):
                # use the mirror name if one exists. otherwise revert back to the source value
                mirroredValue = common.getMirrorName(sourceValue) if common.getMirrorName(sourceValue) else sourceValue

            elif isinstance(sourceValue, list):
                # for each item in the list use the mirror name if one exists.
                # otherwise revert back to the source value
                mirroredValue = list()
                for x in sourceValue:
                    value = common.getMirrorName(x) if common.getMirrorName(x) else x
                    mirroredValue.append(value)

            elif isinstance(sourceValue, dict):
                mirroredValue = dict()
                # for each dictionary key try to get a mirror name for the key and each value.
                for key in list(sourceValue.keys()):
                    mirroredKeyName = common.getMirrorName(key) if common.getMirrorName(key) else key

                    # if the value is a list then try to mirror the list.
                    if isinstance(sourceValue[key], list):
                        mirroredKeyValue = list()
                        for x in sourceValue:
                            value = common.getMirrorName(x) if common.getMirrorName(x) else x
                            mirroredKeyValue.append(value)
                    # otherwise we can try a regular mirror
                    else:
                        mirroredKeyValue = common.getMirrorName(sourceValue[key])

                    # finally if no mirror name is generate just use the source value
                    if not mirroredKeyValue:
                        mirroredValue = sourceValue[key]

                    mirroredValue[mirroredKeyName] = mirroredKeyValue

            else:
                mirroredValue = sourceValue

            # apply the mirrored values
            mirrorMetaNode.setData(attr=parameter, value=mirroredValue)

    @QtCore.Slot()
    def _deleteComponent(self):
        """ Delete a component and the item from the tree widget"""
        items = self.getSelectedItem()
        for item in items:
            component = self.getComponentObj(item)
            if component.getContainer():
                component.deleteSetup()
            self.componentTree.takeTopLevelItem(self.componentTree.indexOfTopLevelItem(item))

            self.builder.componentList.remove(component)

    @QtCore.Slot()
    def _renameComponent(self):
        items = self.getSelectedItem()

        if not len(items) > 0:
            return
        else:
            item = items[0]

        # create a window to ask for a name
        component = self.getComponentObj(item)
        container = component.getContainer()

        newName, accept = QtWidgets.QInputDialog.getText(self, "Rename {}".format(component.name), "New Name:")
        if accept:
            oldName = component.getName()

            # unlock the name attribute
            attr.unlock(container, 'name')
            attr.setAttr(container, 'name', newName)
            attr.lock(container, 'name')

            # get all nodes in the container an do a search and replace
            containedNodes = rig_container.getNodesInContainer(container)
            newContainerName = naming.searchAndReplaceName(container, oldName, newName)[0]
            naming.searchAndReplaceName(containedNodes, oldName, newName)

            # we need to manually reset some of the class parameters of the names we changed
            component.setName(newName)
            component.setContainer(newContainerName)

            # reload the component parameters back into the class
            component._updateClassParameters()

            # rename the component in the UI
            item.setText(0, newName)

            # update the auto complete stringModel
            stringList = self.searchCompleterModel.stringList()
            stringList.remove(oldName)
            stringList.append(newName)

            self.searchCompleterModel.setStringList(stringList)

    @QtCore.Slot()
    def _getComponentHelp(self):
        """ Print component help to the script editor"""
        items = self.getSelectedItem()

        for item in items:
            component = self.getComponentObj(item)
            component.help()

    @QtCore.Slot()
    def _searchForComponent(self):
        searchedText = self.searchBar.text()

        for item in self.getAll():
            if item.text(0) == searchedText:
                self.componentTree.setCurrentItem(item)
                self.searchBar.clear()

    def clearTree(self):
        """ clear the component tree"""
        try:
            if self.componentTree.topLevelItemCount() > 0:
                self.componentTree.clear()
                self.searchCompleterModel.setStringList(list())
        except RuntimeError:
            pass

    @QtCore.Slot(int)
    def __changeTreeWidgetSize(self, size):
        """Change the size of the component tree widget to expand or contract and fit more items"""

        widgetSize = self.frameGeometry()
        newSize = widgetSize.height() + size
        self.setFixedHeight(newSize)

    def showEvent(self, e):
        """ override the show event to add the script job. """
        super(ComponentManager, self).showEvent(e)
        self._setupCallbacks()
        self._loadFromScene()

    def hideEvent(self, e):
        """Override the hide event to teardown the callbacks"""
        super(ComponentManager, self).hideEvent(e)
        self._teardownCallbacks()

    def showAddComponentDialog(self):
        """ Show the add Component dialog"""
        dialog = CreateComponentDialog()
        dialog.newComponentCreatedSignal.connect(self.createComponent)
        dialog.show()


class CreateComponentDialog(QtWidgets.QDialog):
    """
    Create new component dialog
    """
    WINDOW_TITLE = "Create New Component"

    newComponentCreatedSignal = QtCore.Signal(str, str, str, str)

    def __init__(self):
        """
        constructor for the create component dialog
        """
        if sys.version_info.major < 3:
            mainMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mainMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(CreateComponentDialog, self).__init__(mainMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(400, 180)
        self.resize(400, 440)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

        self.updateComboBox()

    def createWidgets(self):
        """ Create widgets"""
        self.nameLineEdit = QtWidgets.QLineEdit()

        self.componentTypeComboBox = QtWidgets.QComboBox()
        self.componentTypeComboBox.setMinimumHeight(30)
        self.componentTypeComboBox.setMaxVisibleItems(30)

        self.inputLineEdit = QtWidgets.QLineEdit()
        self.inputLineEdit.setPlaceholderText("[]")
        self.loadSelectedAsInput = QtWidgets.QPushButton("<")
        self.loadSelectedAsInput.setMaximumWidth(30)

        self.rigParentLineEdit = QtWidgets.QLineEdit()
        self.rigParentLineEdit.setPlaceholderText("None")
        self.loadSelectedAsRigParent = QtWidgets.QPushButton("<")
        self.loadSelectedAsRigParent.setMaximumWidth(30)

        self.discriptionTextEdit = QtWidgets.QTextEdit()
        self.discriptionTextEdit.setReadOnly(True)

        self.applyAndCloseButton = QtWidgets.QPushButton("Create and Close")
        self.applyButton = QtWidgets.QPushButton("Create")
        self.closeButton = QtWidgets.QPushButton("Cancel")

    def createLayouts(self):
        """ Create Layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(4)

        nameLayout = QtWidgets.QHBoxLayout()
        nameLayout.addWidget(QtWidgets.QLabel("name:"))
        nameLayout.addWidget(self.nameLineEdit)
        nameLayout.addSpacing(30)
        nameLayout.addWidget(QtWidgets.QLabel("type:"))
        nameLayout.addWidget(self.componentTypeComboBox)

        inputLayout = QtWidgets.QHBoxLayout()
        inputLayout.addWidget(self.inputLineEdit)
        inputLayout.addWidget(self.loadSelectedAsInput)

        rigParentLayout = QtWidgets.QHBoxLayout()
        rigParentLayout.addWidget(self.rigParentLineEdit)
        rigParentLayout.addWidget(self.loadSelectedAsRigParent)

        widgetLayout = QtWidgets.QFormLayout()
        widgetLayout.addRow(QtWidgets.QLabel("input:"), inputLayout)
        widgetLayout.addRow(QtWidgets.QLabel("rigParent:"), rigParentLayout)

        applyButtonLayout = QtWidgets.QHBoxLayout()
        applyButtonLayout.addWidget(self.applyAndCloseButton)
        applyButtonLayout.addWidget(self.applyButton)
        applyButtonLayout.addWidget(self.closeButton)

        mainLayout.addLayout(nameLayout)
        mainLayout.addLayout(widgetLayout)
        mainLayout.addSpacing(5)
        mainLayout.addWidget(self.discriptionTextEdit)
        mainLayout.addLayout(applyButtonLayout)

    def createConnections(self):
        """ Create Connections"""
        self.loadSelectedAsInput.clicked.connect(self.addSelectionAsInput)
        self.loadSelectedAsRigParent.clicked.connect(self.addSelectionAsRigParent)
        self.componentTypeComboBox.currentIndexChanged.connect(self.updateDiscription)
        self.closeButton.clicked.connect(self.close)
        self.applyButton.clicked.connect(self.apply)
        self.applyAndCloseButton.clicked.connect(self.applyAndClose)

    def updateComboBox(self):
        """ Update the combobox with the exisitng component types """
        self.componentTypeComboBox.clear()
        tempBuilder = builder.Builder()
        for i, componentType in enumerate(sorted(tempBuilder.getAvailableComponents())):
            self.componentTypeComboBox.addItem(componentType)
            self.componentTypeComboBox.setItemIcon(i, QtGui.QIcon(_getComponentIcon(componentType)))

            # get the UI Color
            uiColor = _getComponentColor(componentType)
            self.componentTypeComboBox.setItemData(i, QtGui.QColor(*uiColor), QtCore.Qt.TextColorRole)

    def updateDiscription(self):
        """
        Update the UI discription based on the currently selection component type
        """
        self.discriptionTextEdit.clear()

        componentType = self.componentTypeComboBox.currentText()
        componentObject = core.createComponentClassInstance(componentType)

        classDocs = componentObject.__doc__ or ''
        initDocs = componentObject.__init__.__doc__ or ''
        docstring = classDocs + '\n---- parameters ----\n' + initDocs
        if docstring:
            docstring = re.sub(" {4}", "", docstring.strip())

        self.discriptionTextEdit.setText(docstring)

    def addSelectionAsInput(self):
        """Add the selection as the input"""
        self.inputLineEdit.clear()
        sel = cmds.ls(sl=True)
        selList = list()
        for s in sel:
            selList.append(str(s))

        self.inputLineEdit.setText(str(selList))

    def addSelectionAsRigParent(self):
        """Add the selection as the rigParent"""
        self.rigParentLineEdit.clear()
        sel = cmds.ls(sl=True)

        if len(sel) > 0:
            self.rigParentLineEdit.setText(str(sel[0]))

    def apply(self):
        """
        Apply (create the component and widget) but keep the UI open
        :return:
        """
        componentType = self.componentTypeComboBox.currentText()

        name = self.nameLineEdit.text() or None
        input = self.inputLineEdit.text() or []
        rigParent = self.rigParentLineEdit.text() or None

        # emit the data to the createComponent mehtod of the component manager.
        # if the type is main then we can ignore the input.
        if name and componentType == 'main.Main':
            self.newComponentCreatedSignal.emit(name, componentType, "[]", rigParent)
        elif name and input:
            self.newComponentCreatedSignal.emit(name, componentType, input, rigParent)

    def applyAndClose(self):
        """Apply and close the Ui"""
        self.apply()
        self.close()
