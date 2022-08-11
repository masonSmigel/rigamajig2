#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: mayaObjectWidget.py
    author: masonsmigel
    date: 08/2022
    discription: 

"""

import sys
from os.path import relpath

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

import maya.api.OpenMaya as om2

SCRIPT_FILE_FILTER = "Python (*.py) ;; Mel (*.mel)"


def mayaMainWindow():
    """ Return the Maya main window widget as a Python object """
    mainWindowPointer = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(mainWindowPointer), QtWidgets.QWidget)
    else:
        return wrapInstance(long(mainWindowPointer), QtWidgets.QWidget)


# ignore too many public methods to UI classes.
# pylint: disable = too-many-public-methods
class MayaObjectLine(QtWidgets.QWidget):
    """
    Ui to set a maya object as the selection and clear and retreive the object
    """

    def __init__(self, label=None):
        """

        """
        super(MayaObjectLine, self).__init__()
        self.labelText = label
        self._fullDagPath = None

        self.createActions()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createActions(self):
        """ Create actions"""
        self.addMayaSelectionAction = QtWidgets.QAction("Add Maya Selection", self)
        self.addMayaSelectionAction.setIcon(QtGui.QIcon(":absolute.png"))
        self.addMayaSelectionAction.triggered.connect(self.loadMayaSelection)

        self.selectInMayaAction = QtWidgets.QAction("Select in Maya", self)
        self.selectInMayaAction.setIcon(QtGui.QIcon(":selectObject.png"))
        self.selectInMayaAction.triggered.connect(self.selectInMaya)

        self.clearSelectionAction = QtWidgets.QAction("Clear Selection", self)
        self.clearSelectionAction.setIcon(QtGui.QIcon(":trash.png"))
        self.clearSelectionAction.triggered.connect(self.clearSelection)

    def createWidgets(self):
        """ Create Widgets """
        self.label = QtWidgets.QLabel(self.labelText)
        self.mayaObject = QtWidgets.QLineEdit()
        self.mayaObject.setReadOnly(True)

        self.mayaObject.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.mayaObject.customContextMenuRequested.connect(self._createContextMenu)

    def createLayouts(self):
        """ Create layouts """

        self.mainLayout = QtWidgets.QHBoxLayout(self)

        # If we have a label add the label widget.
        if self.labelText:
            self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.mayaObject)

    def createConnections(self):
        """ Create connections"""
        pass

    def _createContextMenu(self, position):
        """Create the right click context menu"""

        menu = QtWidgets.QMenu(self.mayaObject)
        menu.addAction(self.addMayaSelectionAction)
        menu.addAction(self.selectInMayaAction)
        menu.addSeparator()
        menu.addAction(self.clearSelectionAction)

        menu.exec_(self.mayaObject.mapToGlobal(position))

    def setHeight(self, height):
        self.label.setMinimumHeight(height)
        self.mayaObject.setMinimumHeight(height)

    def getSelection(self):
        """ Get the full dag path of the selected object"""
        return self._fullDagPath

    def loadMayaSelection(self):
        """ Load Maya selection action"""
        selection = om2.MGlobal.getActiveSelectionList()
        if selection.length():
            mob = selection.getDependNode(0)
            dagPath = om2.MFnDagNode(mob)
            self.mayaObject.setText(dagPath.name())
            self._fullDagPath = dagPath.fullPathName()
        else:
            raise Exception("Nothing is selected")

    def selectInMaya(self):
        """ Select Current Object in maya"""
        if self._fullDagPath:
            cmds.select(self._fullDagPath)

    def clearSelection(self):
        """ Clear the active selection"""
        self._fullDagPath = None
        self.mayaObject.clear()


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
        self.mayaObjectLine = MayaObjectLine("Maya Object:")
        self.mayaObjectLine.setHeight(20)

    def createLayouts(self):
        """ Create layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)

        mainLayout.addWidget(self.mayaObjectLine)

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
