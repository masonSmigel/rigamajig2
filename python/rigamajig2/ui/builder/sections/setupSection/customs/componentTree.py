#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: componentManager.py.py
    author: masonsmigel
    date: 01/2024
    description: 

"""
import ast
import logging
from functools import partial

import maya.api.OpenMaya as om
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from rigamajig2.maya import attr
from rigamajig2.maya import container
from rigamajig2.maya import meta
from rigamajig2.maya import naming
from rigamajig2.maya.builder import componentManager
from rigamajig2.shared import common
from rigamajig2.ui.resources import Resources
from .componentItem import ComponentTreeWidgetItem
from ..dialogs.createComponentDialog import CreateComponentDialog
from ..dialogs.editComponentDialog import EditComponentDialog

logger = logging.getLogger(__name__)


# pylint: disable=too-many-public-methods
class ComponentTree(QtWidgets.QWidget):
    """
    Component manager wiget used within the intialize Widget
    """

    component_icons = dict()

    def __init__(self, builder=None, *args, **kwargs):
        super(ComponentTree, self).__init__(*args, **kwargs)

        # keep a reference to the current builder
        self.builder = builder

        # store an open edit component dialog in a varriable
        self.editComponentDialog = None

        self.callbackArray = om.MCallbackIdArray()

        self.createActions()
        self.createWidget()

        self.setMinimumHeight(320)

    def createActions(self):
        """Create Actions"""
        self.selectContainerAction = QtWidgets.QAction("Select Container", self)
        self.selectContainerAction.setIcon(Resources.getIcon(":out_container.png"))
        self.selectContainerAction.triggered.connect(self._selectContainer)

        self.editComponentSettingsAction = QtWidgets.QAction("Edit Component Parameters")
        self.editComponentSettingsAction.setIcon(Resources.getIcon(":toolSettings.png"))
        self.editComponentSettingsAction.triggered.connect(self._editComponentParameters)

        self.renameComponentAction = QtWidgets.QAction("Rename Component", self)
        self.renameComponentAction.setIcon(Resources.getIcon(":quickRename.png"))
        self.renameComponentAction.triggered.connect(self._renameComponent)

        self.componentHelpAction = QtWidgets.QAction("Help", self)
        self.componentHelpAction.setIcon(Resources.getIcon(":help.png"))
        self.componentHelpAction.triggered.connect(self._getComponentHelp)

        self.mirrorComponentAction = QtWidgets.QAction("Mirror Component")
        self.mirrorComponentAction.setIcon(Resources.getIcon(":QR_mirrorGuidesRightToLeft.png"))
        self.mirrorComponentAction.triggered.connect(self._mirrorComponent)

        self.reloadComponentAction = QtWidgets.QAction("Reload Cmpts from Scene", self)
        self.reloadComponentAction.setIcon(Resources.getIcon(":refresh.png"))
        self.reloadComponentAction.triggered.connect(self._loadFromScene)

        self.deleteComponentAction = QtWidgets.QAction("Delete Cmpt", self)
        self.deleteComponentAction.setIcon(Resources.getIcon(":trash.png"))
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
        """Create the Widget"""
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
        self.expandWidgetButton.setIcon(Resources.getIcon(":nodeGrapherArrowDown.png"))
        self.expandWidgetButton.setFlat(True)
        self.expandWidgetButton.setFixedSize(15, 20)
        self.expandWidgetButton.setToolTip("Expand Component Manager")
        self.expandWidgetButton.clicked.connect(partial(self.__changeTreeWidgetSize, 40))

        self.contractWidgetButton = QtWidgets.QPushButton()
        self.contractWidgetButton.setIcon(Resources.getIcon(":nodeGrapherArrowUp.png"))
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
        """get all components in the component tree"""
        return [self.componentTree.topLevelItem(i) for i in range(self.componentTree.topLevelItemCount())]

    def getSelectedItem(self):
        """get the selected items in the component tree"""
        return [item for item in self.componentTree.selectedItems()]

    def _setupCallbacks(self):
        """
        Setup callbacks
        """
        # if a new scene is opened refresh the builder ui
        self.callbackArray.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, self._loadFromScene))

        # we also want to update the callbacks whenever we update a step on the components.
        # since all the componts activate a container update when the container changes
        self.callbackArray.append(om.MEventMessage.addEventCallback("currentContainerChange", self._loadFromScene))

        logger.debug(f"Setup Callbacks: {self.callbackArray}")

    def _teardownCallbacks(self):
        """Teardown the callbacks we created"""
        logger.debug(f"Teardown Callbacks: {self.callbackArray}")

        om.MEventMessage.removeCallbacks(self.callbackArray)
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
        componentObject = componentManager.createComponentClassInstance(componentType)
        cmpt = componentObject(name=name, input=ast.literal_eval(str(input)), rigParent=rigParent)

        item = ComponentTreeWidgetItem(name=name, componentType=componentType, container=cmpt.getContainer())
        self.componentTree.addTopLevelItem(item)
        self.builder.componentList.append(cmpt)
        self._addItemToAutoComplete(name=name)

        cmpt.initializeComponent()
        return cmpt

    def _loadFromScene(self, *args):
        """Load exisiting components from the scene"""
        components = meta.getTagged("component")

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
        """Get the component object instance from the builder based on the item in the tree widget."""
        if not item:
            item = self.getSelectedItem()[0]

        itemDict = item.getData()
        component = self.builder.findComponent(itemDict["name"])
        return component

    def resetComponentDialogInstance(self):
        """Set the instance of the component dialog back to None. This way we know when it must be re-created"""
        self.editComponentDialog = None

    def setRigBuilder(self, builder):
        """Set a new Rig Builder"""
        self.builder = builder

    def loadListFromBuilder(self):
        """Load the component list from the builder"""
        # reset the tree and autocompletes
        self.clearTree()

        if not self.builder:
            raise RuntimeError("No valid rig builder found")
        for component in self.builder.getComponentList():
            name = component.name
            componentType = component.componentType
            buildStepString = ["unbuilt", "initialize", "guide", "build", "connect", "finalize", "optimize"]
            buildStep = buildStepString[component.getStep()]

            item = ComponentTreeWidgetItem(name=name, componentType=componentType, buildStep=buildStep)
            self.componentTree.addTopLevelItem(item)

    @QtCore.Slot()
    def _selectContainer(self):
        """Select the container node of the selected components"""
        cmds.select(cl=True)
        for item in self.getSelectedItem():
            itemDict = item.getData()
            cmds.select(itemDict["container"], add=True)

    @QtCore.Slot()
    def _editComponentParameters(self):
        """Open the Edit component parameters dialog"""

        if not self.editComponentDialog:
            self.editComponentDialog = EditComponentDialog()
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
        """Create a mirrored component"""

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
            if parameter in ["type", "name", "build_step", "__component__", "__version__", "component_side"]:
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
        """Delete a component and the item from the tree widget"""
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
        componentContainer = component.getContainer()

        newName, accept = QtWidgets.QInputDialog.getText(self, "Rename {}".format(component.name), "New Name:")
        if accept:
            oldName = component.getName()

            # unlock the name attribute
            attr.unlock(componentContainer, "name")
            attr.setAttr(componentContainer, "name", newName)
            attr.lock(componentContainer, "name")

            # get all nodes in the container an do a search and replace
            containedNodes = container.getNodesInContainer(componentContainer)
            newContainerName = naming.searchAndReplaceName(componentContainer, oldName, newName)[0]
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
        """Print component help to the script editor"""
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
        """clear the component tree"""
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
        """override the show event to add the script job."""
        super(ComponentTree, self).showEvent(e)
        self._setupCallbacks()
        self._loadFromScene()

    def hideEvent(self, e):
        """Override the hide event to teardown the callbacks"""
        super(ComponentTree, self).hideEvent(e)
        self._teardownCallbacks()

    def showAddComponentDialog(self):
        """Show the add Component dialog"""
        dialog = CreateComponentDialog()
        dialog.newComponentCreatedSignal.connect(self.createComponent)
        dialog.show()
