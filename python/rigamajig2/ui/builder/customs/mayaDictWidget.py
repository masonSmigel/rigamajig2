#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: mayaObjectWidget.py
    author: masonsmigel
    date: 08/2022
    description: 
"""

import sys

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om2
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

from rigamajig2.ui.resources import Resources

SCRIPT_FILE_FILTER = "Python (*.py) ;; Mel (*.mel)"


def mayaMainWindow():
    """ Return the Maya main window widget as a Python object """
    mainWindowPointer = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(mainWindowPointer), QtWidgets.QWidget)
    else:
        return wrapInstance(long(mainWindowPointer), QtWidgets.QWidget)


class InputDialog(QtWidgets.QDialog):
    """ Simple two feild input dialog"""

    def __init__(self, parent=None):
        """ InputDialog constructor """
        super(InputDialog, self).__init__()

        self.setWindowTitle("Add New Item")

        self.first = QtWidgets.QLineEdit(self)
        self.second = QtWidgets.QLineEdit(self)
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self);

        layout = QtWidgets.QFormLayout(self)
        layout.addRow("Label:", self.first)
        layout.addRow("Maya Object:", self.second)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        """ return the user inputs"""
        return self.first.text(), self.second.text()


# ignore too many public methods to UI classes.
# pylint: disable = too-many-public-methods
class MayaDict(QtWidgets.QWidget):
    """
    Ui to set up simple dictionaries of maya objects. Simple dictionaries conist of a key and value.
    Like an enum attribute. They are most commonly used for spaces.
    """
    itemsChanged = QtCore.Signal(str)

    def __init__(self, label=None):
        """

        """
        super(MayaDict, self).__init__()

        self.createActions()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createActions(self):
        """ Create actions"""
        self.addNameAction = QtWidgets.QAction("Add New Item", self)
        self.addNameAction.setIcon(Resources.getIcon(":addCreateGeneric.png"))
        self.addNameAction.triggered.connect(self.addName)

        self.addMayaSelectionAction = QtWidgets.QAction("Add Item from Maya", self)
        self.addMayaSelectionAction.setIcon(Resources.getIcon(":addCreateGeneric.png"))
        self.addMayaSelectionAction.triggered.connect(self.loadMayaSelection)

        self.selectInMayaAction = QtWidgets.QAction("Select in Maya", self)
        self.selectInMayaAction.setIcon(Resources.getIcon(":selectObject.png"))
        self.selectInMayaAction.triggered.connect(self.selectInMaya)

        self.selectAllInMayaAction = QtWidgets.QAction("Select All in Maya", self)
        self.selectAllInMayaAction.setIcon(Resources.getIcon(":selectObject.png"))
        self.selectAllInMayaAction.triggered.connect(self.selectAllInMaya)

        self.clearSelectionAction = QtWidgets.QAction("Clear Selection", self)
        self.clearSelectionAction.setIcon(Resources.getIcon(":trash.png"))
        self.clearSelectionAction.triggered.connect(self.clearSelection)

        self.clearAllAction = QtWidgets.QAction("Clear All", self)
        self.clearAllAction.setIcon(Resources.getIcon(":trash.png"))
        self.clearAllAction.triggered.connect(self.clearAll)

    def createWidgets(self):
        """ Create Widgets """
        self.mayaObjectDict = QtWidgets.QTreeWidget()
        self.mayaObjectDict.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.mayaObjectDict.setHeaderHidden(False)
        self.mayaObjectDict.setHeaderLabels(["Label", "Maya Object"])
        self.mayaObjectDict.setAlternatingRowColors(True)

        self.mayaObjectDict.setIndentation(5)
        self.mayaObjectDict.setColumnCount(2)
        self.mayaObjectDict.setColumnWidth(0, 80)

        self.mayaObjectDict.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.mayaObjectDict.customContextMenuRequested.connect(self._createContextMenu)

    def createLayouts(self):
        """ Create layouts """

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(self.mayaObjectDict)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

    def createConnections(self):
        """ Create connections"""

    def setHeight(self, height):
        """ Set the list widget height"""
        self.mayaObjectDict.setFixedHeight(height)

    def getData(self, fullDagPath=False):
        """ Return a dictionary of all items. ie. {label: maya Object}"""
        returnDict = dict()

        for item in self.getAllItems():
            label = item.text(0)
            obj = item.data(QtCore.Qt.UserRole, 1) if fullDagPath else item.text(1)
            returnDict[label] = obj

        return returnDict

    def _createContextMenu(self, position):
        """Create the right click context menu"""

        menu = QtWidgets.QMenu(self.mayaObjectDict)
        menu.addAction(self.addNameAction)
        menu.addAction(self.addMayaSelectionAction)
        menu.addSeparator()
        menu.addAction(self.selectInMayaAction)
        menu.addAction(self.selectAllInMayaAction)
        menu.addSeparator()
        menu.addAction(self.clearSelectionAction)
        menu.addAction(self.clearAllAction)

        menu.exec_(self.mayaObjectDict.mapToGlobal(position))

    def addMayaObject(self, label, obj):
        """Append a new maya object"""

        # if the object exists in maya store the dag path
        if cmds.objExists(obj):
            selection = om2.MGlobal.getSelectionListByName(obj)
            mob = selection.getDependNode(0)
            dagPath = om2.MFnDagNode(mob)

            obj = dagPath.name()
            fullDagPath = dagPath.fullPathName()

        else:
            obj = obj
            fullDagPath = obj

        rowcount = self.mayaObjectDict.topLevelItemCount()
        item = QtWidgets.QTreeWidgetItem(rowcount)

        item.setText(0, label)
        item.setText(1, obj)
        item.setToolTip(1, fullDagPath)
        item.setData(QtCore.Qt.UserRole, 1, fullDagPath)

        self.mayaObjectDict.addTopLevelItem(item)
        self.itemsChanged.emit(item.text(0))

    def setItems(self, dictonary):
        """ Set the list widget to a list of items"""
        self.clearAll()

        for key in list(dictonary.keys()):
            self.addMayaObject(key, dictonary[key])

    def getAllItems(self):
        """ get all components in the component tree"""
        return [self.mayaObjectDict.topLevelItem(i) for i in range(self.mayaObjectDict.topLevelItemCount())]

    def getSelectedItem(self):
        """ get the selected items in the component tree"""
        return [item for item in self.mayaObjectDict.selectedItems()]

    def addName(self):
        """Add a new specific name"""

        dialog = InputDialog()
        if dialog.exec_():
            label, obj = dialog.getInputs()
            self.addMayaObject(label, obj)

    def loadMayaSelection(self):
        """ Load Maya selection action"""

        selection = om2.MGlobal.getActiveSelectionList()
        if selection.length() > 0:

            text, accept = QtWidgets.QInputDialog.getText(self, "Add Name", "Enter Label Name:")
            if not accept:
                return

            for i in range(selection.length()):
                mob = selection.getDependNode(i)
                dagPath = om2.MFnDagNode(mob)
                self.addMayaObject(text, dagPath.name())
        else:
            om2.MGlobal.displayError("Nothing is selected")

    def selectInMaya(self):
        """ Select Current Object in maya"""
        cmds.select(clear=True)
        for item in self.getSelectedItem():
            dagPath = item.data(QtCore.Qt.UserRole, 1)
            cmds.select(dagPath, add=True)

    def selectAllInMaya(self):
        """ Select all Items in maya"""
        cmds.select(clear=True)
        for item in self.getAllItems():
            dagPath = item.data(QtCore.Qt.UserRole, 1)
            cmds.select(dagPath, add=True)

    def clearSelection(self):
        """ Clear the active selection"""
        selectedItems = self.getSelectedItem()
        for item in selectedItems:
            index = self.mayaObjectDict.indexOfTopLevelItem(item)
            self.mayaObjectDict.takeTopLevelItem(index)
            self.itemsChanged.emit(item.text(0))

    def clearAll(self):
        """ Clear the whole widget"""
        self.mayaObjectDict.clear()
        self.itemsChanged.emit("")


class TestDialog(QtWidgets.QDialog):
    """
    Test dialog for the script executer
    """
    WINDOW_TITLE = "Test Dialog"

    def __init__(self, parent=mayaMainWindow()):
        super(TestDialog, self).__init__(parent)

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
        self.mayaObjectLine = MayaDict("Maya Object:")

    def createLayouts(self):
        """ Create layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)

        mainLayout.addWidget(self.mayaObjectLine)

        self.mayaObjectLine.addMayaObject('label', 'pCube1')

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
