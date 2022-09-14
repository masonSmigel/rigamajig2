#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: initalize_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
import ast
import os
import re
import sys
from functools import partial

# MAYA
import maya.cmds as cmds
from shiboken2.shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
import rigamajig2.shared.common as common
from rigamajig2.maya import meta as meta
from rigamajig2.maya.builder import builder
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, sliderGrp
from rigamajig2.ui.builder_ui import constants
from rigamajig2.maya.builder.constants import GUIDES, COMPONENTS

ICON_PATH = os.path.abspath(os.path.join(__file__, '../../../../../icons'))


class InitializeWidget(QtWidgets.QWidget):
    """ Initalize layout for the builder UI """

    def __init__(self, builder=None):
        """
        Constructor for the initalize widget
        :param builder: builder to connect to the ui
        """
        super(InitializeWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets """
        self.mainCollapseableWidget = collapseableWidget.CollapsibleWidget('Initialize Rig', addCheckbox=True)
        self.componentsPathSelector = pathSelector.PathSelector("cmpts:",
                                                                caption="Select a Component File",
                                                                fileFilter=constants.JSON_FILTER,
                                                                fileMode=1)
        self.loadComponentsButton = QtWidgets.QPushButton("Load Cmpts")
        self.loadComponentsButton.setIcon(QtGui.QIcon(common.getIcon("loadComponents.png")))
        self.appendComponentsButton = QtWidgets.QPushButton("Append Cmpts")
        self.saveComponentsButton = QtWidgets.QPushButton("Save Cmpts")
        self.saveComponentsButton.setIcon(QtGui.QIcon(common.getIcon("saveComponents.png")))
        self.addComponentsButton = QtWidgets.QPushButton("Add Components")
        self.addComponentsButton.setIcon(QtGui.QIcon(":freeformOff.png"))

        self.loadComponentsButton.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.saveComponentsButton.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.addComponentsButton.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.loadComponentsButton.setIconSize(constants.LARGE_BTN_ICON_SIZE)
        self.saveComponentsButton.setIconSize(constants.LARGE_BTN_ICON_SIZE)
        self.addComponentsButton.setIconSize(constants.LARGE_BTN_ICON_SIZE)

        self.componentManager = ComponentManager()

        self.initalizeBuildButton = QtWidgets.QPushButton("Guide Components")
        self.initalizeBuildButton.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.guidePathSelector = pathSelector.PathSelector("guides:",
                                                           caption="Select a guide file",
                                                           fileFilter=constants.JSON_FILTER,
                                                           fileMode=1)
        self.loadGuidesButton = QtWidgets.QPushButton("Load Guides")
        self.saveGuidesButton = QtWidgets.QPushButton("Save Guides")

        self.loadGuidesButton.setIcon(QtGui.QIcon(common.getIcon("loadGuides.png")))
        self.saveGuidesButton.setIcon(QtGui.QIcon(common.getIcon("saveGuides.png")))

        self.loadGuidesButton.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.saveGuidesButton.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.loadGuidesButton.setIconSize(constants.LARGE_BTN_ICON_SIZE)
        self.saveGuidesButton.setIconSize(constants.LARGE_BTN_ICON_SIZE)

    def createLayouts(self):
        """ Create Layouts"""
        # setup the main layout.
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.mainCollapseableWidget.addWidget(self.componentsPathSelector)

        componentButtonLayout = QtWidgets.QHBoxLayout()
        componentButtonLayout.setSpacing(4)

        guideLoadLayout = QtWidgets.QHBoxLayout()
        guideLoadLayout.addWidget(self.loadGuidesButton)
        guideLoadLayout.addWidget(self.saveGuidesButton)

        loadComponentsLayout = QtWidgets.QHBoxLayout()
        loadComponentsLayout.addWidget(self.loadComponentsButton)
        loadComponentsLayout.addWidget(self.saveComponentsButton)
        loadComponentsLayout.addWidget(self.addComponentsButton)
        self.mainCollapseableWidget.addLayout(loadComponentsLayout)

        self.mainCollapseableWidget.addWidget(self.componentManager)
        self.mainCollapseableWidget.addWidget(self.initalizeBuildButton)
        self.mainCollapseableWidget.addLayout(componentButtonLayout)
        self.mainCollapseableWidget.addWidget(self.guidePathSelector)
        self.mainCollapseableWidget.addLayout(guideLoadLayout)

        # add the widget to the main layout
        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections"""
        self.loadGuidesButton.clicked.connect(self.loadGuides)
        self.saveGuidesButton.clicked.connect(self.saveGuides)
        self.loadComponentsButton.clicked.connect(self.loadComponents)
        self.saveComponentsButton.clicked.connect(self.saveComponents)

        self.addComponentsButton.clicked.connect(self.componentManager.showAddComponentDialog)
        self.initalizeBuildButton.clicked.connect(self.initalizeRig)

    def setBuilder(self, builder):
        """ Set a builder for intialize widget"""
        rigEnv = builder.getRigEnviornment()
        self.builder = builder
        self.componentsPathSelector.setRelativePath(rigEnv)
        self.guidePathSelector.setRelativePath(rigEnv)
        self.componentManager.setRigBuilder(self.builder)

        # reset the UI
        self.componentManager.clearTree()

        # update data within the rig
        cmptsFile = self.builder.getRigData(self.builder.getRigFile(), COMPONENTS)
        self.componentsPathSelector.selectPath(cmptsFile)

        guidesFile = self.builder.getRigData(self.builder.getRigFile(), GUIDES)
        self.guidePathSelector.selectPath(guidesFile)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.loadComponents()
        self.initalizeRig()

    @property
    def isChecked(self):
        """ Check it the widget is checked"""
        return self.mainCollapseableWidget.isChecked()

    # CONNECTIONS
    def loadComponents(self):
        """ Load component setup from json using the builder """
        self.builder.setComponents(list())
        # load the compoonents from the file. then initialize them
        self.builder.loadComponents(self.componentsPathSelector.getPath())
        self.builder.initalize()
        # load the component settings from the file.
        self.builder.loadComponentSettings(self.componentsPathSelector.getPath())
        self.componentManager.loadListFromBuilder()

    def saveComponents(self):
        """ Save component setup from json using the builder """
        self.builder.loadMetadataToComponentSettings()
        self.builder.saveComponents(self.componentsPathSelector.getPath())

    def loadGuides(self):
        """ Load guide setup to json using the builder """

        self.builder.loadGuideData(self.guidePathSelector.getPath())

    def saveGuides(self):
        """ Save guides setup to json using the builder """
        self.builder.saveGuideData(self.guidePathSelector.getPath())

    def initalizeRig(self):
        """Run the comppnent intialize on the builder and update the UI """
        self.builder.guide()
        self.builder.loadComponentSettings()
        self.componentManager.loadFromScene()


def _getComponentIcon(cmpt):
    """ get the component icon from the module.Class of the component"""
    return QtGui.QIcon(os.path.join(ICON_PATH, "{}.png".format(cmpt.split('.')[0])))


def getComponentObject(componentType=None):
    """
    Get an instance of the component object based on the componentType
    :param componentType: type of the component to get the class instance from.
    :return:
    """
    tempBuilder = builder.Builder()
    cmptDict = tempBuilder.getComponentRefDict()

    if componentType not in list(cmptDict.keys()):
        # HACK: this is a work around to account for the fact that some old .rig files use the cammel cased components
        module, cls = componentType.split('.')
        newClass = cls[0].lower() + cls[1:]
        tempModuleName = module + "." + newClass
        if tempModuleName in list(cmptDict.keys()):
            componentType = tempModuleName

    modulePath = cmptDict[componentType][0]
    className = cmptDict[componentType][1]
    moduleObject = __import__(modulePath, globals(), locals(), ["*"], 0)
    classInstance = getattr(moduleObject, className)

    return classInstance


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

        # keep track of the script node ID
        self.scriptJobID = -1

        self.createActions()
        self.createWidgets()
        self.createLayouts()
        self.setFixedHeight(280)

    def createActions(self):
        """ Create Actions"""
        self.selectContainerAction = QtWidgets.QAction("Select Container", self)
        self.selectContainerAction.setIcon(QtGui.QIcon(":out_container.png"))
        self.selectContainerAction.triggered.connect(self.selectContainer)

        self.editComponentSettingsAction = QtWidgets.QAction("Edit Component Parameters")
        self.editComponentSettingsAction.setIcon(QtGui.QIcon(":toolSettings.png"))
        self.editComponentSettingsAction.triggered.connect(self.editComponentParameters)

        self.createSymetricalComponent = QtWidgets.QAction("Create Mirrored Component")
        self.createSymetricalComponent.setIcon(QtGui.QIcon(":kinMirrorJoint_S.png"))
        self.createSymetricalComponent.triggered.connect(self.createMirroredComponent)

        self.mirrorComponentSettingsAction = QtWidgets.QAction("Mirror Component Parameters")
        self.mirrorComponentSettingsAction.setIcon(QtGui.QIcon(":QR_mirrorGuidesRightToLeft.png"))
        self.mirrorComponentSettingsAction.triggered.connect(self.mirrorComponentParameters)

        self.reloadComponentAction = QtWidgets.QAction("Reload Cmpts from Scene", self)
        self.reloadComponentAction.setIcon(QtGui.QIcon(":refresh.png"))
        self.reloadComponentAction.triggered.connect(self.loadFromScene)

        self.deleteComponentAction = QtWidgets.QAction("Delete Cmpt", self)
        self.deleteComponentAction.setIcon(QtGui.QIcon(":trash.png"))
        self.deleteComponentAction.triggered.connect(self.deleteComponent)

    def createWidgets(self):
        """ Create Widgets"""
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

        self.componentTree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.componentTree.addAction(self.selectContainerAction)
        self.componentTree.addAction(self.editComponentSettingsAction)
        self.componentTree.addAction(self.createSymetricalComponent)
        self.componentTree.addAction(self.mirrorComponentSettingsAction)
        self.componentTree.addAction(self.reloadComponentAction)
        self.componentTree.addAction(self.deleteComponentAction)

    def createLayouts(self):
        """ Create Layouts"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.minimumSize()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(4)
        self.mainLayout.addWidget(self.componentTree)

    def setScriptJobEnabled(self, enabled):
        """
        Set the state of the script job.
        The script job ensures the widget displays changes when the scene changes
        """
        if enabled and self.scriptJobID < 0:
            self.scriptJobID = cmds.scriptJob(event=["NewSceneOpened", partial(self.loadFromScene)],
                                              protected=True)
        elif not enabled and self.scriptJobID > 0:
            cmds.scriptJob(kill=self.scriptJobID, f=True)
            self.scriptJobID = -1

    def addComponent(self, name, componentType, buildStep='unbuilt', container=None):
        """ append a new component to the ui """
        rowcount = self.componentTree.topLevelItemCount()
        item = QtWidgets.QTreeWidgetItem(rowcount)
        item.setSizeHint(0, QtCore.QSize(item.sizeHint(0).width(), 24))  # set height

        # set the nessesary text.
        item.setText(0, name)
        item.setFont(0, QtGui.QFont())

        item.setText(1, componentType)
        item.setText(2, buildStep)

        item.setTextColor(1, QtGui.QColor(156, 156, 156))
        item.setTextColor(2, QtGui.QColor(156, 156, 156))

        # set the icon
        icon = _getComponentIcon(componentType)
        item.setIcon(0, icon)

        # set the data
        if container:
            item.setData(QtCore.Qt.UserRole, 0, container)

        self.componentTree.addTopLevelItem(item)
        return item

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
        componentObject = getComponentObject(componentType)
        cmpt = componentObject(name=name, input=ast.literal_eval(str(input)), rigParent=rigParent)

        self.addComponent(name=name, componentType=componentType, buildStep='unbuilt', container=None)
        self.builder.appendComponents([cmpt])
        cmpt._initalizeComponent()
        return cmpt

    def loadFromScene(self):
        """ Load exisiting components from the scene"""
        self.clearTree()
        components = meta.getTagged('component')

        for component in components:
            name = cmds.getAttr("{}.name".format(component))
            componentType = cmds.getAttr("{}.type".format(component))
            buildStepList = cmds.attributeQuery("build_step", n=component, le=True)[0].split(":")
            buildStep = buildStepList[cmds.getAttr("{}.build_step".format(component))]
            isSubComponent = meta.hasTag(component, "subComponent")
            if not isSubComponent:
                self.addComponent(name=name, componentType=componentType, buildStep=buildStep, container=component)

    def parseData(self, item):
        """
        return a dictionary of data for the selected item.
        :return:
        """
        itemData = dict()
        itemData['name'] = item.text(0)
        itemData['type'] = item.text(1)
        itemData['step'] = item.text(2)
        itemData['container'] = item.data(QtCore.Qt.UserRole, 0)

        return itemData

    def getAll(self):
        """ get all components in the component tree"""
        return [self.componentTree.topLevelItem(i) for i in range(self.componentTree.topLevelItemCount())]

    def getSelectedItem(self):
        """ get the selected items in the component tree"""
        return [item for item in self.componentTree.selectedItems()]

    def getComponentObj(self, item=None):
        """ Get the component object instance from the builder based on the item in the tree widget. """
        if not item:
            item = self.getSelectedItem()[0]

        itemDict = self.parseData(item)
        cmpt = self.builder.findComponent(itemDict['name'], itemDict['type'])
        return cmpt

    def selectContainer(self):
        """ Select the container node of the selected components """
        cmds.select(cl=True)
        for item in self.getSelectedItem():
            itemDict = self.parseData(item)
            cmds.select(itemDict['container'], add=True)

    def editComponentParameters(self):
        """ Open the Edit component parameters dialog"""
        from rigamajig2.ui.builder_ui import editComponentDialog

        if not self.editComponentDialog:
            self.editComponentDialog = editComponentDialog.EditComponentDialog()
            self.editComponentDialog.windowClosedSignal.connect(self.resetComponentDialogInstance)
            self.editComponentDialog.show()
        else:
            self.editComponentDialog.raise_()
            self.editComponentDialog.activateWindow()

        # set dialog to the current item
        self.editComponentDialog.setComponent(self.getComponentObj())

    def resetComponentDialogInstance(self):
        """ Set the instance of the component dialog back to None. This way we know when it must be re-created"""
        self.editComponentDialog = None

    def createMirroredComponent(self):
        """ Create a mirrored component"""
        selectedComponent = self.getComponentObj()

        guessMirrorName = common.getMirrorName(selectedComponent.name)
        componentType = selectedComponent.componentType

        # mirror the input
        mirroredInput = list()
        for x in selectedComponent.input:
            value = common.getMirrorName(x) if common.getMirrorName(x) else x
            mirroredInput.append(value)

        # get a mirrored rigParent
        sourceRigParent = selectedComponent.rigParent
        mirroredRigParent = common.getMirrorName(sourceRigParent) if common.getMirrorName(
            sourceRigParent) else sourceRigParent

        mirroredComponent = self.createComponent(guessMirrorName, componentType, mirroredInput, mirroredRigParent)

        # We need to force the component to intialize so we can mirror stuff
        mirroredComponent._initalizeComponent()
        self.mirrorComponentParameters(selectedComponent)

        # update the ui
        self.loadFromScene()

    def mirrorComponentParameters(self, sourceComponent=None):
        """
        Mirror the component parameters for the selected parameter

        NOTE: the mirror script does not support nested lists or dictonaries.
        """
        if not sourceComponent:
            sourceComponent = self.getComponentObj()

        # find the mirrored component
        guessMirrorName = common.getMirrorName(sourceComponent.name)
        componentType = sourceComponent.componentType
        mirrorComponent = self.builder.findComponent(guessMirrorName, componentType)

        if not mirrorComponent:
            cmds.warning("No mirror found for: {}".format(sourceComponent.name))
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
            if isinstance(sourceValue, str):
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

    def buildComponent(self):
        """ Build a single component"""
        items = self.getSelectedItem()
        for item in items:
            itemDict = self.parseData(item)

            self.builder.buildSingleComponent(itemDict['name'], itemDict['type'])
            self.updateComponentFromScene(item)

    def deleteComponent(self):
        """ Delete a component and the item from the tree widget"""
        items = self.getSelectedItem()
        for item in items:
            component = self.getComponentObj(item)
            if component.getContainer():
                component.deleteSetup()
            self.componentTree.takeTopLevelItem(self.componentTree.indexOfTopLevelItem(item))

            self.builder.componentList.remove(component)

    def clearTree(self):
        """ clear the component tree"""
        try:
            if self.componentTree.topLevelItemCount() > 0:
                self.componentTree.clear()
        except RuntimeError:
            pass

    def setRigBuilder(self, builder):
        """ Set a new Rig Builder"""
        self.builder = builder

    def loadListFromBuilder(self):
        """ Load the compoonent list from the builder"""
        self.clearTree()

        if not self.builder:
            raise RuntimeError("No valid rig builder found")
        for cmpt in self.builder.getComponentList():
            name = cmpt.name
            componentType = cmpt.componentType
            buildStepString = ['unbuilt', 'initalize', 'build', 'connect', 'finalize', 'optimize']
            buildStep = buildStepString[cmpt.getStep()]

            self.addComponent(name=name, componentType=componentType, buildStep=buildStep)

    def updateComponentFromScene(self, item):
        """ Update a given list item from its scene data """
        itemDict = self.parseData(item)
        container = itemDict['container']

        name = cmds.getAttr("{}.name".format(container))
        cmpt = cmds.getAttr("{}.type".format(container))
        buildStepList = cmds.attributeQuery("build_step", n=container, le=True)[0].split(":")
        buildStep = buildStepList[cmds.getAttr("{}.build_step".format(container))]

        item.setText(0, name)
        item.setText(1, cmpt)
        item.setText(2, buildStep)

    def showEvent(self, e):
        """ override the show event to add the script job. """
        super(ComponentManager, self).showEvent(e)
        self.setScriptJobEnabled(True)

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

        self.numJointsSlider = sliderGrp.SliderGroup(min=0, max=10, value=4)
        self.createInputJointsButton = QtWidgets.QPushButton("Create Input Joints")
        self.createInputJointsButton.setMinimumWidth(180)

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

        createJointsLayout = QtWidgets.QHBoxLayout()
        createJointsLayout.addWidget(QtWidgets.QLabel("num joints:"))
        createJointsLayout.addWidget(self.numJointsSlider)
        createJointsLayout.addWidget(self.createInputJointsButton)

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
        mainLayout.addLayout(createJointsLayout)
        mainLayout.addLayout(widgetLayout)
        mainLayout.addSpacing(5)
        mainLayout.addWidget(self.discriptionTextEdit)
        mainLayout.addLayout(applyButtonLayout)

    def createConnections(self):
        """ Create Connections"""
        self.createInputJointsButton.clicked.connect(self.createInputJoints)
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
        for i, component in enumerate(sorted(tempBuilder.getAvailableComponents())):
            self.componentTypeComboBox.addItem(component)
            self.componentTypeComboBox.setItemIcon(i, QtGui.QIcon(_getComponentIcon(component)))

    def updateDiscription(self):
        """
        Update the UI discription based on the currently selection component type
        """
        self.discriptionTextEdit.clear()

        componentType = self.componentTypeComboBox.currentText()
        componentObject = getComponentObject(componentType)

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

    def createInputJoints(self):
        """ create an input joint list"""
        componentType = self.componentTypeComboBox.currentText()
        componentName = self.nameLineEdit.text()
        numJoints = self.numJointsSlider.getValue()
        side = common.getSide(componentName)

        componentClassInstance = getComponentObject(componentType)
        joints = componentClassInstance.createInputJoints(name=componentName, side=side, numJoints=numJoints)

        stringList = list()
        for s in joints:
            stringList.append(str(s))

        self.inputLineEdit.setText(str(stringList))

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
