#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: deformLayerDialog.py
    author: masonsmigel
    date: 09/2023
    discription: 

"""
import sys
import os
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
import maya.cmds as cmds

from functools import partial

from rigamajig2.ui.widgets import mayaDialog, mayaMessageBox
from rigamajig2.shared import common

from rigamajig2.maya.rig import deformLayer
from rigamajig2.maya import meta
from rigamajig2.maya import deformer

DEFORMTREE_STYLESHEET = (f"""
                    QTreeView {{
                        spacing: 5px;
                    }}
                    
                    QTreeView::indicator {{
                        width: 13px;
                        height: 13px;
                    }}
                    
                    QTreeView::indicator:unchecked {{
                        image: url({common.ICONS_PATH}/eye_hidden.png);
                    }}
                    
                    QTreeView::indicator:unchecked:hover {{
                        image: url({common.ICONS_PATH}/eye_hidden.png);
                    }}
                    
                    QTreeView::indicator:unchecked:pressed {{
                        image: url({common.ICONS_PATH}/eye_hidden.png);
                    }}
                    
                    QTreeView::indicator:checked {{
                        image: url({common.ICONS_PATH}/eye_visable.png);
                    }}
                    
                    QTreeView::indicator:checked:hover {{
                        image: url({common.ICONS_PATH}/eye_visable.png);
                    }}
                    
                    QTreeView::indicator:checked:pressed {{
                        image: url({common.ICONS_PATH}/eye_visable.png);
                    }}
                    QTreeView::indicator:indeterminate {{
                        image: url({common.ICONS_PATH}/eye_partiallyVisable.png);
                    }}
                    
                    """)


class DeformLayersTreeWidget(QtWidgets.QTreeWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.setIndentation(15)
        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.setUniformRowHeights(True)
        self.setAlternatingRowColors(True)


class DeformLayerHeaderTreeItem(QtWidgets.QTreeWidgetItem):
    """Class for layer headers in the treeWidgetItem"""

    def __init__(self, name, parent=None):
        super(DeformLayerHeaderTreeItem, self).__init__(parent)
        self.setFlags(
            QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsTristate)
        self.setCheckState(0, QtCore.Qt.PartiallyChecked)
        self.child_items = []

        # set the name text
        self.setText(0, name)

        # Create a QFont object with bold style
        font = QtGui.QFont()
        font.setBold(True)

        # Set the font for the item
        self.setFont(0, font)
        self.setSizeHint(0, QtCore.QSize(0, 22))

    def addChild(self, child):
        super(DeformLayerHeaderTreeItem, self).addChild(child)
        self.child_items.append(child)


class DeformLayerMeshTreeItem(QtWidgets.QTreeWidgetItem):
    """Class for deformLayerMeshes in the tree Widget"""

    def __init__(self, deformLayerMesh, model, parent=None):
        super(DeformLayerMeshTreeItem, self).__init__(parent)

        self.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)

        self.setText(0, deformLayerMesh)
        self.setIcon(0, QtGui.QIcon(":mesh.svg"))
        itemVisable = cmds.getAttr(f"{deformLayerMesh}.v")

        checkState = QtCore.Qt.Checked if itemVisable else QtCore.Qt.Unchecked
        self.setCheckState(0, checkState)

        # store the mainMesh
        self.setData(0, QtCore.Qt.UserRole, model)


class DeformerTreeItem(QtWidgets.QTreeWidgetItem):
    """ Class for deformers in the treeWidget"""

    def __init__(self, deformerName, parent=None):
        super(DeformerTreeItem, self).__init__(parent)

        self.deformerName = deformerName
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

        self.setText(0, deformerName)

        # get the deformerType and set the icons
        deformerType = cmds.nodeType(deformerName)
        if deformerType == "skinCluster":
            self.setIcon(0, QtGui.QIcon(f":smoothSkin.png"))
        else:
            self.setIcon(0, QtGui.QIcon(f":{deformerType}.png"))

        # set the envelope
        self.setEnvelope(cmds.getAttr(f"{self.deformerName}.envelope"))

    def setEnvelope(self, value):
        """ Set the envelope value"""
        if value:
            cmds.setAttr(f"{self.deformerName}.envelope", True)
            self.setTextColor(0, QtWidgets.QTreeWidget().palette().color(QtGui.QPalette.Text))
        else:
            cmds.setAttr(f"{self.deformerName}.envelope", False)
            self.setTextColor(0, QtGui.QColor(100, 100, 100))


class DeformLayerDialog(mayaDialog.MayaDialog):
    WINDOW_TITLE = "Deform Layer Manager"

    def __init__(self):
        super().__init__()
        self.setMinimumSize(340, 600)
        self.layerGroupLookupDict = {}

        self.updateLayerGroups()

    def createActions(self):
        self.selectNodeAction = QtWidgets.QAction("Select Node")
        self.selectNodeAction.setIcon(QtGui.QIcon(":selectModel.png"))
        self.selectNodeAction.triggered.connect(self.selectNodes)

        self.selectGeometryAction = QtWidgets.QAction("Select Geometry")
        self.selectGeometryAction.setIcon(QtGui.QIcon(":selectModel.png"))
        self.selectGeometryAction.triggered.connect(self.selectGeometryNode)

        self.toggleDeformerAction = QtWidgets.QAction("Toggle Envelope")
        self.toggleDeformerAction.triggered.connect(self.performToggleDeformer)

        self.moveDeformerUp = QtWidgets.QAction("Move Deformer Up")
        self.moveDeformerUp.setIcon(QtGui.QIcon(":moveUVUp.png"))
        self.moveDeformerUp.triggered.connect(partial(self.performReorderDeformer, opperation="up"))

        self.moveDeformerDown = QtWidgets.QAction("Move Deformer Down")
        self.moveDeformerDown.setIcon(QtGui.QIcon(":moveUVDown.png"))
        self.moveDeformerDown.triggered.connect(partial(self.performReorderDeformer, opperation="down"))

        self.moveDeformerToTop = QtWidgets.QAction("Move Deformer to Top")
        self.moveDeformerToTop.setIcon(QtGui.QIcon(":moveLayerUp.png"))
        self.moveDeformerToTop.triggered.connect(partial(self.performReorderDeformer, opperation="top"))

        self.moveDeformerToBottom = QtWidgets.QAction("Move Deformer to Bottom")
        self.moveDeformerToBottom.setIcon(QtGui.QIcon(":moveLayerDown.png"))
        self.moveDeformerToBottom.triggered.connect(partial(self.performReorderDeformer, opperation="bottom"))

    def createWidgets(self):

        self.layerGroupComboBox = QtWidgets.QComboBox()
        self.layerGroupComboBox.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.filterButton = QtWidgets.QPushButton()
        self.filterButton.setIcon(QtGui.QIcon(":filter.png"))
        self.filterButton.setCheckable(True)
        self.filterButton.setChecked(False)
        self.filterButton.setMaximumSize(20, 20)
        self.filterButton.setFlat(True)

        self.refreshButton = QtWidgets.QPushButton()
        self.refreshButton.setIcon(QtGui.QIcon(":refresh"))
        self.refreshButton.setMaximumSize(20, 20)
        self.refreshButton.setFlat(True)

        self.deformLayersTree = DeformLayersTreeWidget()
        self.deformLayersTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.deformLayersTree.customContextMenuRequested.connect(self._deformLayerTreeContextMenu)
        self.deformLayersTree.setStyleSheet(DEFORMTREE_STYLESHEET)

        self.suffixLineEdit = QtWidgets.QLineEdit()
        self.suffixLineEdit.setPlaceholderText("suffix")

        self.combineMthodComboBox = QtWidgets.QComboBox()
        for item in deformLayer.CONNECTION_METHOD_LIST:
            self.combineMthodComboBox.addItem(item)
        self.addDeformLayerButton = QtWidgets.QPushButton("Add Deform Layer")

    def createLayouts(self):
        mainLayout = QtWidgets.QVBoxLayout(self)

        layerGroupLayout = QtWidgets.QHBoxLayout()
        layerGroupLayout.addWidget(QtWidgets.QLabel("Layer Group:"))
        layerGroupLayout.addWidget(self.layerGroupComboBox)
        layerGroupLayout.addWidget(self.filterButton)
        layerGroupLayout.addWidget(self.refreshButton)

        mainLayout.addLayout(layerGroupLayout)

        mainLayout.addWidget(self.deformLayersTree)

        addLayerLayout = QtWidgets.QHBoxLayout()
        addLayerLayout.addWidget(self.suffixLineEdit)
        addLayerLayout.addWidget(self.combineMthodComboBox)
        addLayerLayout.addWidget(self.addDeformLayerButton)

        mainLayout.addLayout(addLayerLayout)

    def createConnections(self):
        self.filterButton.clicked.connect(self.toggleFilteredTreeWidget)
        self.refreshButton.clicked.connect(self.refreshButtonClicked)
        self.layerGroupComboBox.currentTextChanged.connect(self.updateTreeWidgetFromLayerGroup)
        self.deformLayersTree.itemChanged.connect(self.handleDeformLayerTree)
        self.addDeformLayerButton.clicked.connect(self.addDeformLayer)

    def _deformLayerTreeContextMenu(self, position):

        items = self.deformLayersTree.selectedItems()
        if items:
            item = items[-1]

            menu = QtWidgets.QMenu(self.deformLayersTree)
            menu.addAction(self.selectNodeAction)

            # define actions depending on the context of the current selection
            if isinstance(item, DeformLayerHeaderTreeItem):
                pass

            if isinstance(item, DeformLayerMeshTreeItem):
                pass

            if isinstance(item, DeformerTreeItem):
                menu.addAction(self.selectGeometryAction)
                menu.addSeparator()
                menu.addAction(self.toggleDeformerAction)
                menu.addSeparator()
                menu.addAction(self.moveDeformerUp)
                menu.addAction(self.moveDeformerDown)
                menu.addAction(self.moveDeformerToTop)
                menu.addAction(self.moveDeformerToBottom)

                # next we need to build a menu to transfer a deformer to another layer.
                transferMenu = QtWidgets.QMenu(menu)
                transferMenu.setTitle("Transfer to Layer...")
                menu.addSeparator()
                menu.addMenu(transferMenu)

                #
                mainGeo = item.parent().data(0, QtCore.Qt.UserRole)
                deformLayers = deformLayer.DeformLayer(mainGeo).getDeformationLayers()
                deformLayers.pop(deformLayers.index(item.parent().text(0)))  # remove the current item

                for otherDeformLayer in deformLayers:
                    transferAction = QtWidgets.QAction(otherDeformLayer)
                    transferAction.setIcon(QtGui.QIcon(":mesh.svg"))

                    # find the target item by filtering the names
                    deformLayerMeshItems = self.getTreeWidgetItemsByType(DeformLayerMeshTreeItem)
                    targetItem = None
                    for eachTargetItem in deformLayerMeshItems:
                        if eachTargetItem.text(0) == otherDeformLayer:
                            targetItem = eachTargetItem

                    transferAction.triggered.connect(partial(self.performTransferDeformer, item, targetItem))
                    transferMenu.addAction(transferAction)

            menu.exec_(self.deformLayersTree.mapToGlobal(position))

    def addDeformLayer(self):
        """
        add a new deformation layer to the selected object
        :return:
        """
        # Todo: implement
        suffix = self.suffixLineEdit.text()
        connectionMethod = self.combineMthodComboBox.currentText()

        selection = cmds.ls(sl=True)
        if not selection:
            selectedItems = self.selectedItems()
            selection = []
            meshItems = self.getTreeWidgetItemsByType(DeformLayerMeshTreeItem)
            for item in selectedItems:
                if item in meshItems:
                    selection.append(item.text(0))

        confirm = mayaMessageBox.MayaMessageBox(
            title="Add new Deform Layers",
            message=f"Are you sure you want to add new deform layers to {len(selection)} meshes",
            icon="help")
        confirm.setButtonsYesNoCancel()
        result = confirm.exec_()

        if result == confirm.Yes:
            for node in selection:
                renderModel = deformLayer.getRenderModelFromLayer(node)
                layers = deformLayer.DeformLayer(renderModel)
                layers.createDeformLayer(suffix=suffix, connectionMethod=connectionMethod)

        # update the treeWidget with the new stuff
        self.refreshButtonClicked()

    def insertDeformLayer(self, index):
        """
        Insert a deform layer
        :param index:
        :return:
        """
        raise NotImplementedError

    def updateLayerGroups(self):
        meshWithDeformLayers = meta.getTagged("hasDeformLayers")

        self.layerGroupLookupDict.clear()
        self.layerGroupComboBox.clear()
        layerGroupsList = set()
        for mesh in meshWithDeformLayers:
            # get the layer group
            layerGroup = cmds.getAttr(f"{mesh}.{deformLayer.LAYER_GROUP_ATTR}")
            layerGroupsList.add(layerGroup)
            if layerGroup in self.layerGroupLookupDict:
                existingList = self.layerGroupLookupDict[layerGroup]
                existingList.append(mesh)
                self.layerGroupLookupDict[layerGroup] = existingList
            else:
                self.layerGroupLookupDict[layerGroup] = [mesh]

        # add the items to the combo box
        for layerGroup in layerGroupsList:
            self.layerGroupComboBox.addItem(layerGroup)

    def updateTreeWidgetFromLayerGroup(self, layerGroup):

        if not layerGroup:
            return
        # we need to get the max number of layers
        meshesInLayerGroup = self.layerGroupLookupDict[layerGroup]

        self.updateTreeWidget(meshesInLayerGroup)

    def updateTreeWidget(self, meshList):
        """ Update the deformer Tree Widget based on the input list of meshes"""
        self.deformLayersTree.clear()

        # get the number of layers to add
        if len(meshList) == 0:
            return

        numberOfLayers = max(deformLayer.DeformLayer(mesh).getNumberOfDeformationLayers() for mesh in meshList)

        if numberOfLayers == 0:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, "No deform Layers in the scene ... ")
            disabledColor = QtWidgets.QTreeWidget().palette().color(QtGui.QPalette.Foreground)
            item.setTextColor(0, QtGui.QColor(disabledColor))
            item.setDisabled(True)
            self.deformLayersTree.addTopLevelItem(item)
            return

        topLevelItemsList = []
        for i in range(numberOfLayers):
            item = DeformLayerHeaderTreeItem(name=f"deformLayer_{i}")

            topLevelItemsList.append(item)
            self.deformLayersTree.addTopLevelItem(item)

            item.setExpanded(True)

        # now add the meshes
        for mesh in meshList:
            deformLayerObj = deformLayer.DeformLayer(mesh)
            deformLayers = deformLayerObj.getDeformationLayers()

            for i, deformLayerMesh in enumerate(deformLayers):
                deformLayerMeshItem = DeformLayerMeshTreeItem(deformLayerMesh=deformLayerMesh,
                                                              model=deformLayerObj.model)
                topLevelItemsList[i].insertChild(0, deformLayerMeshItem)

                # get deformer stack for each deformLayerMesh
                deformerStack = deformer.getDeformerStack(deformLayerMesh)

                for eachDeformer in deformerStack:

                    # check to see if this is part of the deform layer chain (a blendshape connecting the previous layer)
                    if meta.hasTag(eachDeformer, tag=deformLayer.DEFORM_LAYER_BSHP_TAG):
                        continue
                    deformerItem = DeformerTreeItem(deformerName=eachDeformer)
                    deformLayerMeshItem.addChild(deformerItem)

    def refreshButtonClicked(self):
        self.updateTreeWidgetFromLayerGroup(self.layerGroupComboBox.currentText())
        self.filterButton.setChecked(False)

    def selectedItems(self):
        items = self.deformLayersTree.selectedItems() or list()
        return items

    def lastSelectedItem(self):
        if self.selectedItems():
            return self.selectedItems()[-1]
        return None

    def toggleFilteredTreeWidget(self):

        if self.filterButton.isChecked():
            items = self.deformLayersTree.selectedItems()

            meshList = set()
            for item in items:
                if isinstance(item, DeformLayerMeshTreeItem):
                    mesh = item.data(0, QtCore.Qt.UserRole)
                    meshList.add(mesh)

            if len(list(meshList)) > 0:
                for eachItem in self.getAllDeformLayerTreeItems():
                    itemModel = eachItem.data(0, QtCore.Qt.UserRole)
                    if isinstance(eachItem, DeformLayerMeshTreeItem) and itemModel not in meshList:
                        eachItem.setHidden(True)
                return

        # if there are no selections OR we want to uncheck the filter button:
        for eachItem in self.getAllDeformLayerTreeItems():
            if isinstance(eachItem, DeformLayerMeshTreeItem):
                eachItem.setHidden(False)

        self.filterButton.setChecked(False)

    def handleDeformLayerTree(self, item, column):
        """
        Handle any changes to the tree Widget Item
        :param item: item object passed by the itemChanged() signal
        :param column: column index passed py the itemChanged() signal
        :return:
        """

        # if the change was in the first column and the item is a deformLayerMeshItem
        if isinstance(item, DeformLayerMeshTreeItem) and column == 0:
            self.handleDeformMeshLayerVisability(item)
        # Todo: make the item re-namable in the UI

    def handleDeformMeshLayerVisability(self, item):
        """
        Handle changes to the visablilty of the deform Mesh layers. This code will turn on/off visability for
        deform layer meshes. If a different layer is showing this will ensure it is turned off.

        :param item: item object from the handleItemChanged signal
        """

        value = True if item.checkState(0) == QtCore.Qt.CheckState.Checked else False
        cmds.setAttr(f"{item.text(0)}.v", value)
        renderModel = item.data(0, QtCore.Qt.UserRole)

        # loop through the other items that have the same mesh and turn them off if the value is true
        if not value:
            return

        for otherItem in self.getAllDeformLayerTreeItems():
            if isinstance(otherItem, DeformLayerMeshTreeItem):
                if otherItem == item:
                    continue
                if otherItem.data(0, QtCore.Qt.UserRole) == renderModel:
                    otherItem.setCheckState(0, QtCore.Qt.Unchecked)
                    cmds.setAttr(f"{otherItem.text(0)}.v", False)

    def getAllDeformLayerTreeItems(self):
        """Returns all QTreeWidgetItems in the given QTreeWidget."""
        allItems = []
        topLevelItemCount = self.deformLayersTree.topLevelItemCount()

        for i in range(topLevelItemCount):
            topItem = self.deformLayersTree.topLevelItem(i)
            allItems.extend(self.getSubtreeNodes(topItem))

        return allItems

    def getSubtreeNodes(self, treeWidgetItem):
        """Returns all QTreeWidgetItems in the subtree rooted at the given node."""
        nodes = [treeWidgetItem]

        for i in range(treeWidgetItem.childCount()):
            childItem = treeWidgetItem.child(i)
            nodes.extend(self.getSubtreeNodes(childItem))

        return nodes

    def getTreeWidgetItemsByType(self, type):
        """
        Get a list of all treeWidget items by the type
        :param type: base classes to itterate through
        :return:
        """

        returnList = set()

        for item in self.getAllDeformLayerTreeItems():
            if isinstance(item, type):
                returnList.add(item)
        return list(returnList)

    def selectNodes(self):
        """
        Select a node based on the currently selected Item
        """
        items = self.selectedItems()

        nodes = [item.text(0) for item in items]
        cmds.select(nodes, replace=True)

    def selectGeometryNode(self):
        item = self.lastSelectedItem()
        if not item:
            return

        node = item.parent().text(0)
        if cmds.objExists(node):
            cmds.select(node, replace=True)
        else:
            cmds.warning(f"Cannot find the node: '{node}' in your scene")

    def performReorderDeformer(self, opperation="up"):
        """
        Reorder the given deformer up or down
        :return:
        """
        item = self.lastSelectedItem()
        if not item: return

        parentItem = item.parent()

        deformerName = item.text(0)
        geometryName = item.parent().text(0)

        index = item.parent().indexOfChild(item)

        if opperation == "up":
            deformer.reorderSlide(geometry=geometryName, deformer=deformerName, up=True)
            newIndex = index - 1
            if newIndex != -1:
                parentItem.removeChild(item)
                parentItem.insertChild(newIndex, item)
        if opperation == "down":
            deformer.reorderSlide(geometry=geometryName, deformer=deformerName, up=False)
            newIndex = index + 1
            if index != parentItem.childCount() - 1:
                parentItem.removeChild(item)
                parentItem.insertChild(newIndex, item)
        if opperation == "top":
            deformer.reorderToTop(geometry=geometryName, deformer=deformerName)
            newIndex = 0
            parentItem.removeChild(item)
            parentItem.insertChild(newIndex, item)
        if opperation == "bottom":
            deformer.reorderToBottom(geometry=geometryName, deformer=deformerName)
            if index != parentItem.childCount() - 1:
                parentItem.removeChild(item)
                parentItem.addChild(item)

        self.deformLayersTree.setCurrentItem(item)

    def performTransferDeformer(self, item, targetItem):
        """
        Transfer the given deformer from one layer to another.

        :param item:
        :param targetItem:
        """

        if not isinstance(item, DeformerTreeItem):
            raise ValueError("Source Item must be of type 'DeformerTreeWidgetItem'")

        if not isinstance(targetItem, DeformLayerMeshTreeItem):
            raise ValueError("Source Item must be of type 'DeformLayerMeshTreeItem'")

        # perform the deformer transfer
        deformerName = item.text(0)
        sourceMesh = item.parent().text(0)
        targetMesh = targetItem.text(0)
        newDeformer = deformLayer.transferAllDeformerTypes(deformerName=deformerName,
                                                           sourceGeo=sourceMesh,
                                                           targetGeo=targetMesh)

        newDeformerItem = DeformerTreeItem(newDeformer)
        targetItem.insertChild(0, newDeformerItem)

        # remove the old item
        item.parent().removeChild(item)

    def performToggleDeformer(self):
        """
        Toggle the envelope of a deformer
        :param item: Item to toggle the envelope of
        :return:
        """
        item = self.lastSelectedItem()
        if not item: return

        if not isinstance(item, DeformerTreeItem):
            raise ValueError(f"{item} must be of type 'DeformerTreeWidgetItem'")

        deformer = item.text(0)

        envelope = cmds.getAttr(f"{deformer}.envelope")

        if envelope:
            item.setEnvelope(False)
        else:
            item.setEnvelope(True)
