#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: dataLoader.py
    author: masonsmigel
    date: 07/2023
    discription: 

"""
import os
import sys
import pathlib
import inspect
from functools import partial

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

from rigamajig2.ui import showInFolder
from rigamajig2.maya.builder.constants import DATA_PATH
from rigamajig2.maya.data import abstract_data
from rigamajig2.shared import path as rig_path
from rigamajig2.shared import common

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

EXCLUDE_FILES = ['__init__.py']
EXCLUDE_FOLDERS = []


def getDataModules(path=None):
    """
    get a dictionary of data type and data module.
    This can be used to create instances of each data module to use in data loading.
    :return:
    """

    if not path: path = DATA_PATH
    path = rig_path.cleanPath(path)

    pathObj = pathlib.Path(path)

    # here we can find a python root to use later when creating python paths to load the modules
    pythonPaths = [p for p in sys.path if p in path]
    rigamajigRootPyPath = max(pythonPaths, key=len)

    # Using path lib we can list all files and directories than filter out only the files
    files = [f for f in pathObj.iterdir() if f.is_file()]

    toReturn = dict()
    for file in files:
        filePath = pathlib.Path(os.path.join(path, file.name))

        # check the extension of the files.
        if filePath.suffix == '.py' and filePath.name not in EXCLUDE_FILES:
            # get the path local to the python path
            relPath = pathlib.Path(filePath.relative_to(rigamajigRootPyPath))

            # convert the path into a python module path (separated by ".")
            # ie: path/to/module --> path.to.module

            # split the file name into parts.
            # then join them back together minus the suffix
            pathSplit = relPath.parts
            pythonModulePath = ".".join([p.removesuffix(".py") for p in pathSplit])

            # next lets import the module to get an instance of it
            moduleObject = __import__(pythonModulePath, globals(), locals(), ["*"], 0)
            classesInModule = inspect.getmembers(moduleObject, inspect.isclass)

            # now we can look through each class and find the subclasses of the abstract Data Class
            for className, classObj in classesInModule:
                if issubclass(classObj, abstract_data.AbstractData):
                    classDict = dict()
                    classDict[className] = [pythonModulePath, className]
                    toReturn.update(classDict)

    return toReturn


def createDataClassInstance(dataType=None):
    """
    Create a new and usable instance of a given data type to be activly used when loading new data
    :param dataType:
    :return:
    """
    dataTypeInfo = getDataModules().get(dataType)
    if not dataTypeInfo:
        return False

    modulePath = dataTypeInfo[0]
    className = dataTypeInfo[1]

    moduleObject = __import__(modulePath, globals(), locals(), ["*"], 0)
    classInstance = getattr(moduleObject, className)

    return classInstance


class DataLoader(QtWidgets.QWidget):
    """ Widget to select valid file or folder paths """

    def __init__(self,
                 label=None,
                 caption='Select a file or Folder',
                 fileFilter="All Files (*.*)",
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

        # TODO: implement theese to filter out the various data types and only allow some types
        self.dataFilteringEnabled = dataFilteringEnabled
        self.dataFilter = dataFilter or list()

        self.setFixedHeight(self.widgetHeight)

        self.createActions()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createActions(self):
        # TODO: create popup menu
        pass

    def createWidgets(self):
        self.pathLabel = QtWidgets.QLabel()

        self.pathTreeWidget = QtWidgets.QTreeWidget()
        self.pathTreeWidget.setAlternatingRowColors(True)
        self.pathTreeWidget.setHeaderHidden(True)

        self.pathTreeWidget.setIndentation(5)
        self.pathTreeWidget.setColumnCount(2)
        self.pathTreeWidget.setUniformRowHeights(True)
        self.pathTreeWidget.setColumnWidth(0, 160)
        self.pathTreeWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # self.pathTreeWidget.setUniformItemSizes(True)
        # self.pathLineEdit.setPlaceholderText("path/to/file/or/folder")

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
        self.expandWidgetButton.setToolTip("Expand Component Manager")
        self.contractWidgetButton = QtWidgets.QPushButton()
        self.contractWidgetButton.setIcon(QtGui.QIcon(":nodeGrapherArrowUp.png"))
        self.contractWidgetButton.setFlat(True)
        self.contractWidgetButton.setFixedSize(15, 10)
        self.contractWidgetButton.setToolTip("Contract Component Manager")
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
        self.addPathButtton.clicked.connect(self.showAddDataContextMenu)
        self.selectPathButton.clicked.connect(self.selectPath)
        self.showInFolderButton.clicked.connect(self.showInFolder)
        self.expandWidgetButton.clicked.connect(partial(self.changeTreeWidgetSize, 20))
        self.contractWidgetButton.clicked.connect(partial(self.changeTreeWidgetSize, -20))

    def showAddDataContextMenu(self):
        dataTypeMenu = QtWidgets.QMenu()
        for dataType in getDataModules():

            # if we want to use filtering check to see if the data is in the filter.
            if self.dataFilteringEnabled and dataType not in self.dataFilter:
                continue
            action = QtWidgets.QAction(dataType, self)
            dataTypeMenu.addAction(action)
            action.triggered.connect(partial(self.addEmptyFile, dataType))

        pos = self.addPathButtton.mapToGlobal(QtCore.QPoint(0, self.addPathButtton.height()))
        dataTypeMenu.exec_(pos)

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

    def getFileList(self, absoulte=False):
        """
        Get a list of all files used in this widget.
        :return:
        """
        fileList = list()
        for item in self.getAllItems():
            path = item.data(0, QtCore.Qt.UserRole)
            path = pathlib.Path(path)

            if self.relativePath and absoulte == False:
                path = path.relative_to(self.relativePath)
            fileList.append(str(path))

        return fileList

    def clear(self):
        self.pathTreeWidget.clear()

    # Widget Specific
    def selectPath(self, path=None):
        # popup browser to select a file type.
        # if filtering is enabled then we can check the selected type to ensure it matches the given type

        # if a path was provided check that it is absoulte. If its not make it absoulte
        if path:
            path = pathlib.Path(path)
            if path.is_absolute():
                newPath = path
            else:
                print("IS NOT ABSOULTE")
                newPath = path.joinpath(self.relativePath, path)
                newPath = str(newPath.resolve())

        # if no path was provided birng up a fileDialog to select the file
        else:
            # try to find a good current path
            lastItem = self.getLastitem()
            currentPath = pathlib.Path.cwd()
            if lastItem:
                currentPath = lastItem.data(0, QtCore.Qt.UserRole)

            fileInfo = QtCore.QFileInfo(currentPath)
            if not fileInfo.exists():
                currentPath = cmds.workspace(q=True, dir=True)

            newPath = cmds.fileDialog2(
                ds=2,
                cap=self.caption,
                ff=self.fileFilter,
                fm=self.fileMode,
                okc='Select',
                dir=currentPath
                )
            if newPath:
                newPath = newPath[0]
            else:
                # if we dont select a new path cancel the action by returning.
                return

        print(newPath)
        # get the data type of the file and try to filter it.
        newPathDataType = abstract_data.AbstractData().getDataType(newPath)
        if self.dataFilteringEnabled and newPathDataType not in self.dataFilter:
            # TODO: should I keep the raise Warnings?
            raise Warning(f"{pathlib.Path(newPath).name}'s data type does not match filter {self.dataFilter}")

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

        # TODO: Implement
        print(datatype)
        # TODO: add a confirm box to show the name of the file,  type and path BEFORE creating it!

        # create a new file relative to the setRelative path. (if a relative path is set. Otherwise select a full path

    def showInFolder(self):
        """Show the selected file(s) in the finder/explorer"""
        item = self.getSelectedItems()[-1]
        if item:
            path = item.data(0, QtCore.Qt.UserRole)
            showInFolder.showInFolder(path)

    def loadDataFromFile(self, path):
        """
        Holder method for inherited classes to determine data use
        :param path: path to the data file to load.
        """
        if pathlib.Path(path).exists() and pathlib.Path(path).is_file():
            dataType = abstract_data.AbstractData().getDataType(path)
            dataClassInstance = createDataClassInstance(dataType=dataType)

            # initialize the data class instance
            dataClass = dataClassInstance()
            # read the data and apply all keys
            dataClass.read(filepath=path)
            dataClass.applyData(dataClass.getKeys())

    def loadAllData(self):

        # for each item in the list of all items
        for item in self.getAllItems():
            itemFilePath = item.data(0, QtCore.Qt.UserRole)
            self.loadDataFromFile(itemFilePath)

            print(f"loading: {itemFilePath}")

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
                # TODO: should I keep the raise Warnings?
                raise Warning(f"Path '{path}' is already added to the dataLoader")

        dataType = abstract_data.AbstractData.getDataType(fileInfo.filePath())

        # if we are using a relaive path display that instead of the file name.
        fileName = fileInfo.fileName()
        if self.relativePath:
            fileName = os.path.relpath(fileInfo.filePath(), self.relativePath)

        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, fileName)
        item.setText(1, dataType)
        item.setToolTip(0, fileInfo.filePath())

        # icon
        item.setIcon(0,  QtGui.QIcon(":fileNew.png"))

        # we can set the data of the item to the relative path.
        item.setData(0, QtCore.Qt.UserRole, fileInfo.filePath())

        item.setTextColor(1, QtGui.QColor(150, 150, 150))
        item.setSizeHint(0, QtCore.QSize(0, ITEM_SIZE_HINT))  # set height

        self.pathTreeWidget.addTopLevelItem(item)

    # UI Visuals
    def changeTreeWidgetSize(self, size):
        """Change the size of the component tree widget to expand or contract and fit more items"""

        widgetSize = self.frameGeometry()
        newSize = widgetSize.height() + size
        if newSize < self.widgetHeight: newSize = self.widgetHeight
        self.setFixedHeight(newSize)


class TestDialog(QtWidgets.QDialog):
    """
    Test dialog for the script executer
    """
    WINDOW_TITLE = "Test Dialog"

    def __init__(self):

        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(TestDialog, self).__init__(mayaMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(QtCore.Qt.Tool)

        self.setMinimumSize(250, 200)

        self.createWidgets()
        self.createLayouts()

    def createWidgets(self):
        """ Create widgets """
        self.dataLoader = DataLoader("Deformers:")
        self.dataLoader.setRelativePath("/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/")
        self.dataLoader.setFilteringEnabled(True)
        self.dataLoader.setDataFilter(["GuideData", "JointData"])
        self.dataLoader.addItem(
            "/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/components.json")
        self.dataLoader.addItem(
            "/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/skeleton_pos.json")
        self.loadButton = QtWidgets.QPushButton("Load All")
        self.saveButton = QtWidgets.QPushButton("Save All")

        self.loadButton.clicked.connect(self.dataLoader.loadAllData)
        self.saveButton.clicked.connect(self.dataLoader.getFileList)

    def createLayouts(self):
        """ Create layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)

        mainLayout.addWidget(self.dataLoader)
        mainLayout.addWidget(self.loadButton)
        mainLayout.addWidget(self.saveButton)
        mainLayout.addStretch()

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)


if __name__ == "__main__":
    try:
        testDialog.close()  # pylint: disable=E0601
        testDialog.deleteLater()
    except:
        pass
    # pylint: disable=invalid-name
    testDialog = TestDialog()
    testDialog.show()

    # print(getDataModules())
