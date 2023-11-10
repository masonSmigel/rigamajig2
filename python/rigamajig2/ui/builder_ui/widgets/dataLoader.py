#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: dataLoader.py
    author: masonsmigel
    date: 07/2023
    description: 

"""
import logging
import os
import pathlib
import platform
import subprocess
from functools import partial
from typing import List

import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from rigamajig2.maya.builder import dataManager
from rigamajig2.maya.data import abstract_data
from rigamajig2.shared import common
from rigamajig2.ui import showInFolder

logger = logging.getLogger(__name__)

ITEM_SIZE_HINT = 18

LOADABLE_TYPES = ['AnimData',
                  'BlendshapeData',
                  'CurveData',
                  'DeformerData',
                  'DeformLayerData',
                  'GuideData',
                  'JointData',
                  'PSDData',
                  'SHAPESData, '
                  'SkinData']

JSON_FILTER = "Json Files (*.json)"


class DataLoader(QtWidgets.QWidget):
    """ Widget to select valid file or folder paths """

    DATA_TYPE_LIST = dataManager.getDataModules()

    # emit a list of files when updated
    filesUpdated = QtCore.Signal(object)

    def __init__(
            self,
            label=None,
            caption='Select a file or Folder',
            fileFilter=JSON_FILTER,
            fileMode=1,
            widgetHeight=102,
            relativePath=None,
            parent=None,
            dataFilteringEnabled=False,
            dataFilter=None):
        """
        :param label: label to give the path selector
        :param caption: hover over caption
        :param fileFilter: List of file type filters to the dialog.
                           Multiple filters should be separated by double semi-colons.
        :param fileMode: Indicate what the dialog is to return.
                         0 Any file, whether it exists or not.
                         1 A single existing file.
                         2 The name of a directory. Both directories and files are displayed in the dialog.
                         3 The name of a directory. Only directories are displayed in the dialog.
                         4 Then names of one or more existing files.

        :param relativePath: if a relative path is set the path is stored relative to this path.
        :param parent: Pyqt parent for the widget
        """
        super(DataLoader, self).__init__(parent)
        self.caption = caption
        self.fileFilter = fileFilter
        self.fileMode = fileMode
        self.widgetHeight = widgetHeight
        self.relativePath = relativePath
        self.label = label

        self.dataFilteringEnabled = dataFilteringEnabled
        self.dataFilter = dataFilter or list()

        self.setFixedHeight(self.widgetHeight)

        # setup parameters for drag and drop.
        self.setAcceptDrops(True)

        self.createActions()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createActions(self):
        self.loadSelectedDataAction = QtWidgets.QAction("Load Selected", self)
        self.loadSelectedDataAction.setIcon(QtGui.QIcon(":newLayerEmpty.png"))
        self.loadSelectedDataAction.triggered.connect(self.loadSelectedData)

        self.saveSelectedAction = QtWidgets.QAction("Save Selected", self)
        self.saveSelectedAction.setIcon(QtGui.QIcon(":save.png"))
        self.saveSelectedAction.triggered.connect(self.saveSelectedData)

        self.showInFolderAction = QtWidgets.QAction("Show in Folder", self)
        self.showInFolderAction.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.showInFolderAction.triggered.connect(self.showInFolder)

        self.openFileAction = QtWidgets.QAction("Open Data", self)
        self.openFileAction.setIcon(QtGui.QIcon(":openScript.png"))
        self.openFileAction.triggered.connect(self.openScript)

        self.addExistingAction = QtWidgets.QAction("Add Existing Data", self)
        self.addExistingAction.setIcon(QtGui.QIcon(":newPreset.png"))
        self.addExistingAction.triggered.connect(self.pickPath)

        self.deleteFileAction = QtWidgets.QAction("Remove Data", self)
        self.deleteFileAction.setIcon(QtGui.QIcon(":trash.png"))
        self.deleteFileAction.triggered.connect(self.deleteSelectedItems)

    def createWidgets(self):
        self.pathLabel = QtWidgets.QLabel()

        self.pathTreeWidget = QtWidgets.QTreeWidget()
        self.pathTreeWidget.setAlternatingRowColors(True)
        self.pathTreeWidget.setHeaderHidden(True)

        self.pathTreeWidget.setIndentation(5)
        self.pathTreeWidget.setColumnCount(2)
        self.pathTreeWidget.setUniformRowHeights(True)
        self.pathTreeWidget.setColumnWidth(1, 120)
        header = self.pathTreeWidget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.pathTreeWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.pathTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.pathTreeWidget.customContextMenuRequested.connect(self._createContextMenu)

        self.selectPathButton = QtWidgets.QPushButton("...")
        self.selectPathButton.setFixedSize(19, 15)
        self.selectPathButton.setToolTip(self.caption)
        self.selectPathButton.setFlat(True)

        self.addPathButtton = QtWidgets.QPushButton("+")
        self.addPathButtton.setFixedSize(19, 15)
        self.addPathButtton.setToolTip(self.caption)
        self.addPathButtton.setFlat(True)

        self.showInFolderButton = QtWidgets.QPushButton(QtGui.QIcon(":fileOpen.png"), "")
        self.showInFolderButton.setFixedSize(19, 19)
        self.showInFolderButton.setToolTip("Show in Folder")
        self.showInFolderButton.setFlat(True)

        # expand and contract buttons
        self.expandWidgetButton = QtWidgets.QPushButton()
        self.expandWidgetButton.setIcon(QtGui.QIcon(":nodeGrapherArrowDown.png"))
        self.expandWidgetButton.setFlat(True)
        self.expandWidgetButton.setFixedSize(15, 10)
        self.expandWidgetButton.setToolTip("Expand Data Loader")
        self.contractWidgetButton = QtWidgets.QPushButton()
        self.contractWidgetButton.setIcon(QtGui.QIcon(":nodeGrapherArrowUp.png"))
        self.contractWidgetButton.setFlat(True)
        self.contractWidgetButton.setFixedSize(15, 10)
        self.contractWidgetButton.setToolTip("Contract Data Loader")
        # self.showInFolderButton.clicked.connect(self.showInFolder)

    def createLayouts(self):
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(4)
        if self.label is not None:
            self.mainLayout.addWidget(self.pathLabel)
            self.setLabelText(self.label)
            # self.pathLabel.setFixedWidth(60)

        lowerLayout = QtWidgets.QHBoxLayout()
        lowerLayout.addWidget(self.pathTreeWidget)

        fileButtonsLayout = QtWidgets.QFormLayout()
        # self.pathsLayout.addSpacing(4)
        fileButtonsLayout.addWidget(self.selectPathButton)
        fileButtonsLayout.addWidget(self.addPathButtton)
        fileButtonsLayout.addWidget(self.showInFolderButton)
        fileButtonsLayout.addWidget(self.contractWidgetButton)
        fileButtonsLayout.addWidget(self.expandWidgetButton)

        lowerLayout.addLayout(fileButtonsLayout)
        self.mainLayout.addLayout(lowerLayout)

    def createConnections(self):
        self.pathTreeWidget.itemChanged.connect(self.emitFilesUpdatedSignal)
        self.addPathButtton.clicked.connect(self.showAddDataContextMenu)
        self.selectPathButton.clicked.connect(self.pickPath)
        self.showInFolderButton.clicked.connect(self.showInFolder)
        self.expandWidgetButton.clicked.connect(partial(self.changeTreeWidgetSize, 20))
        self.contractWidgetButton.clicked.connect(partial(self.changeTreeWidgetSize, -20))

    def _createContextMenu(self, position):
        """Create the right click context menu"""

        menu = QtWidgets.QMenu(self.pathTreeWidget)
        menu.addAction(self.loadSelectedDataAction)
        menu.addSeparator()
        menu.addAction(self.saveSelectedAction)
        menu.addSeparator()
        menu.addAction(self.showInFolderAction)
        menu.addAction(self.openFileAction)
        menu.addAction(self.addExistingAction)

        addNewMenu = QtWidgets.QMenu("Add New Data File")
        addNewMenu.setIcon(QtGui.QIcon(":addCreateGeneric.png"))
        for action in self.__getAddEmptyDatatypeActions():
            addNewMenu.addAction(action)

        menu.addMenu(addNewMenu)
        menu.addSeparator()
        menu.addAction(self.deleteFileAction)
        # menu.addAction(self.deleteScriptAction)

        # menu .addSeparator()
        # menu .addAction(self.deleteScriptAction)

        menu.exec_(self.pathTreeWidget.mapToGlobal(position))

    def showAddDataContextMenu(self):
        dataTypeMenu = QtWidgets.QMenu()
        for action in self.__getAddEmptyDatatypeActions():
            dataTypeMenu.addAction(action)

        pos = QtGui.QCursor.pos()
        dataTypeMenu.exec_(pos)

    def __getAddEmptyDatatypeActions(self):
        """Here we want to create actions for each datatype and return the action so they can be added to a menu.
        This is used in both the add button and add context menu"""
        actions = list()
        for dataType in self.DATA_TYPE_LIST:
            # if we want to use filtering check to see if the data is in the filter.
            if self.dataFilteringEnabled and dataType not in self.dataFilter:
                continue
            action = QtWidgets.QAction(dataType, self)
            action.setIcon(QtGui.QIcon(":fileNew.png"))
            action.triggered.connect(partial(self.addEmptyFile, dataType))
            actions.append(action)
        return actions

    # UI Utilities

    def getSelectedItems(self):
        """ get the selected items in the component tree"""
        return [item for item in self.pathTreeWidget.selectedItems()]

    def getAllItems(self):
        """ get all components in the component tree"""
        if self.pathTreeWidget.topLevelItemCount() > 0:
            return [self.pathTreeWidget.topLevelItem(i) for i in range(self.pathTreeWidget.topLevelItemCount())]

    def getLastitem(self):
        """Get the very last item. Used in some opperations such as saving"""
        if self.pathTreeWidget.topLevelItemCount() > 0:
            return self.getAllItems()[-1]

    def setRelativePath(self, relativeTo):
        """ Set the path display relative to a folder """
        self.relativePath = relativeTo

    def setFilteringEnabled(self, value):
        """Enable or disable data type filtering"""
        self.dataFilteringEnabled = value

    def setDataFilter(self, value):
        """Set the file filtering list. Only types in the list will be allowed"""
        if not isinstance(value, (list, tuple)):
            value = [value]
        self.dataFilter = value

    def setLabelText(self, text):
        """ Set the label text"""
        self.pathLabel.setText(text)

    def getFileList(self, absolute=False) -> List[str]:
        """
        Get a list of all files used in this widget.
        :return:
        """
        # check if there are items to get
        if not self.pathTreeWidget.topLevelItemCount() > 0:
            return []

        fileList = list()
        for item in self.getAllItems():
            path = item.data(0, QtCore.Qt.UserRole)
            path = pathlib.Path(path)

            if self.relativePath and absolute == False:
                path = path.relative_to(self.relativePath)
            fileList.append(str(path))

        return fileList

    def getSelectedFiles(self, absolute=False):
        """ Get a list of the selected files"""

        if not self.pathTreeWidget.topLevelItemCount() > 0:
            return False

        fileList = list()
        for item in self.getSelectedItems():
            path = item.data(0, QtCore.Qt.UserRole)
            path = pathlib.Path(path)

            if self.relativePath and absolute == False:
                path = path.relative_to(self.relativePath)
            fileList.append(str(path))

        return fileList

    def clear(self):
        self.pathTreeWidget.clear()

    # Widget Specific
    def pickPath(self, path=None):
        # popup browser to select a file type.
        # if filtering is enabled then we can check the selected type to ensure it matches the given type

        if path:
            newPath = path
        # if no path was provided birng up a fileDialog to select the file
        else:

            newPath = cmds.fileDialog2(
                ds=2,
                cap=self.caption,
                ff=self.fileFilter,
                fm=self.fileMode,
                okc='Select',
                dir=self.__getCurrentPath()
                )
            if newPath:
                newPath = newPath[0]
            else:
                # if we dont select a new path cancel the action by returning.
                return

        self.selectPath(newPath)

    def selectPath(self, path):
        """
        Select a path
        :param path:
        :return:
        """
        if not path:
            return

        path = pathlib.Path(path)
        if path.is_absolute():
            newPath = str(path)
        else:
            newPath = path.joinpath(self.relativePath, path)
            newPath = str(newPath.resolve())

        # check to make sure the path is a file math
        if os.path.isdir(newPath):
            return

        # get the data type of the file and try to filter it.
        newPathDataType = abstract_data.AbstractData().getDataType(newPath)
        if self.dataFilteringEnabled and newPathDataType not in self.dataFilter:
            logger.warning(f"{pathlib.Path(newPath).name}'s data type does not match filter {self.dataFilter}")

        self.addItem(newPath)

    def selectPaths(self, pathList):
        """ Add several paths at one """
        pathList = common.toList(pathList)
        for path in pathList:
            self.selectPath(path)

    def addEmptyFile(self, datatype):
        # popup window to type in the file name.
        # it would be cool to allow the use of folder creation here: ex "cluster/cluster1.json"
        # select the data type you would like to save. this could be based on the data folder structure.
        # there should also be some filtering of the data types so that some widgets only allow cirtian data types ("only abstract, no deformers etc")

        newPath = cmds.fileDialog2(
            ds=2,
            cap=self.caption,
            ff=self.fileFilter,
            fm=0,  # Any file weither it exists or not
            okc='Select',
            dir=self.__getCurrentPath()
            )

        if newPath:
            newData = rigamajig2.maya.builder.data.createDataClassInstance(dataType=datatype)
            newData.write(filepath=newPath[0])

            self.addItem(newPath[0])

    def __getCurrentPath(self):

        lastItem = self.getLastitem()
        currentPath = cmds.workspace(q=True, dir=True)
        if lastItem:
            lastPath = lastItem.data(0, QtCore.Qt.UserRole)
            currentPath = os.path.dirname(lastPath)
        return currentPath

    def showInFolder(self):
        """Show the selected file(s) in the finder/explorer"""
        items = self.getSelectedItems()
        if items:
            item = items[-1]
            path = item.data(0, QtCore.Qt.UserRole)
            showInFolder.showInFolder(path)

    def openScript(self):
        items = self.getSelectedItems()

        for item in items:
            filePath = item.data(0, QtCore.Qt.UserRole)
            # macOS
            if platform.system() == 'Darwin':
                subprocess.check_call(['open', filePath])
            # Windows
            elif platform.system() == 'Windows':
                os.startfile(filePath)
            # Linux
            else:
                subprocess.check_call(['xdg-open', filePath])

    def loadDataFromFile(self, path):
        """
        Holder method for inherited classes to determine data use
        :param path: path to the data file to load.
        """
        if pathlib.Path(path).exists() and pathlib.Path(path).is_file():
            dataType = abstract_data.AbstractData().getDataType(path)
            dataClass = rigamajig2.maya.builder.data.createDataClassInstance(dataType=dataType)

            # read the data and apply all keys
            dataClass.read(filepath=path)
            dataClass.applyAllData()

    def loadAllData(self):

        # for each item in the list of all items
        for item in self.getAllItems():
            itemFilePath = item.data(0, QtCore.Qt.UserRole)
            self.loadDataFromFile(itemFilePath)

    def loadSelectedData(self):
        """Load only data from the selected object"""
        selectedItems = self.getSelectedItems()
        if not selectedItems:
            return

        for item in selectedItems:
            itemFilePath = item.data(0, QtCore.Qt.UserRole)
            self.loadDataFromFile(itemFilePath)

    def saveSelectedData(self):
        """Load only data from the selected object"""
        items = self.getSelectedItems()
        item = items[-1] if items else None

        if not item:
            return

        sceneSelection = cmds.ls(sl=True)

        dataFile = item.data(0, QtCore.Qt.UserRole)
        dataType = abstract_data.AbstractData.getDataType(dataFile)

        # read the current data into the data object
        dataObj = rigamajig2.maya.builder.data.createDataClassInstance(dataType)
        dataObj.read(dataFile)

        # gather data from the new selection
        dataObj.gatherDataIterate(sceneSelection)

        dataObj.write(dataFile)
        print(f"Saved: {sceneSelection} into {dataFile}")

    def deleteSelectedItems(self):
        """ delete """
        items = self.getSelectedItems()
        for item in items:
            self.pathTreeWidget.takeTopLevelItem(self.pathTreeWidget.indexOfTopLevelItem(item))

        self.emitFilesUpdatedSignal()

    def addItem(self, path=None):
        """
        Add a new path to the data widget. This is mainly two parts, one to validate the path, and a second to create the widget.
        :param path: full absoulte path to the data file.
        :return:
        """
        if not path:
            return

        fileInfo = QtCore.QFileInfo(path)
        if not fileInfo.exists():
            return

        # check if the path is already in the data loader!
        if self.pathTreeWidget.topLevelItemCount() > 0:
            allPaths = [p.data(0, QtCore.Qt.UserRole) for p in self.getAllItems()]
            if path in allPaths:
                logger.warning(f"Path '{path}' is already added to the dataLoader")
                return

        dataType = abstract_data.AbstractData.getDataType(fileInfo.filePath())

        # if we are using a relaive path display that instead of the file name.
        fileName = fileInfo.fileName()
        if self.relativePath:
            fileName = os.path.relpath(fileInfo.filePath(), self.relativePath)

        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, fileName)
        item.setText(1, dataType)

        # get a data object and read the keys so we can add them to the UI
        d = abstract_data.AbstractData()
        d.read(fileInfo.filePath())

        tooltipFormatting = fileInfo.filePath()

        item.setToolTip(0, tooltipFormatting)

        # icon
        item.setIcon(0, QtGui.QIcon(":fileNew.png"))

        # we can set the data of the item to the relative path.
        item.setData(0, QtCore.Qt.UserRole, fileInfo.filePath())

        item.setTextColor(1, QtGui.QColor(150, 150, 150))
        item.setSizeHint(0, QtCore.QSize(0, ITEM_SIZE_HINT))  # set height

        self.pathTreeWidget.addTopLevelItem(item)
        self.emitFilesUpdatedSignal()

    def emitFilesUpdatedSignal(self, *args):
        fileList = list(self.getFileList(absolute=False))
        self.filesUpdated.emit(fileList)

    # UI Visuals
    def changeTreeWidgetSize(self, size):
        """Change the size of the component tree widget to expand or contract and fit more items"""

        widgetSize = self.frameGeometry()
        newSize = widgetSize.height() + size
        if newSize < self.widgetHeight: newSize = self.widgetHeight
        self.setFixedHeight(newSize)

    def dragEnterEvent(self, event):
        """ Reimplementing event to accept plain text, """
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """ Reimplementing event to accept plain text, """
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ """
        if event.mimeData().hasUrls:
            for url in event.mimeData().urls():
                filePath = url.path()
                if filePath:
                    self.selectPath(filePath)


