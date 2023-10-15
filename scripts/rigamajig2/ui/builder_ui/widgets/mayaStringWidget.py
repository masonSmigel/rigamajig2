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
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

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
class MayaString(QtWidgets.QWidget):
    """
    Ui to set a maya object as the selection and clear and retreive the object
    """

    def __init__(self):
        """

        """
        super(MayaString, self).__init__()
        self._fullDagPath = None

        self.createActions()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createActions(self):
        """ Create actions"""
        self.addMayaSelectionAction = QtWidgets.QAction("Add Maya Selection", self)
        self.addMayaSelectionAction.setIcon(QtGui.QIcon(":addCreateGeneric.png"))
        self.addMayaSelectionAction.triggered.connect(self.loadMayaSelection)

        self.selectInMayaAction = QtWidgets.QAction("Select in Maya", self)
        self.selectInMayaAction.setIcon(QtGui.QIcon(":selectObject.png"))
        self.selectInMayaAction.triggered.connect(self.selectInMaya)

        self.clearSelectionAction = QtWidgets.QAction("Clear Selection", self)
        self.clearSelectionAction.setIcon(QtGui.QIcon(":trash.png"))
        self.clearSelectionAction.triggered.connect(self.clearSelection)

    def createWidgets(self):
        """ Create Widgets """
        self.mayaObject = QtWidgets.QLineEdit()
        self.mayaObject.setReadOnly(False)

        self.mayaObject.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.mayaObject.customContextMenuRequested.connect(self._createContextMenu)

    def createLayouts(self):
        """ Create layouts """

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0,0,0,0)
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

    def setText(self, text):
        """Set the text of the mayaObject line edit"""
        self.mayaObject.setText(text)


    def setHeight(self, height):
        """Set the height of the widget"""
        self.label.setMinimumHeight(height)
        self.mayaObject.setMinimumHeight(height)

    def getSelection(self):
        """ Get the full dag path of the selected object"""
        return self._fullDagPath

    def getText(self):
        """ Return only the text of the selected object (AKA the dag name)"""
        return self.mayaObject.text()

    def loadMayaSelection(self):
        """ Load Maya selection action"""
        selection = om2.MGlobal.getActiveSelectionList()
        if selection.length():
            mob = selection.getDependNode(0)
            dagPath = om2.MFnDagNode(mob)
            self.mayaObject.setText(dagPath.name())
            self._fullDagPath = dagPath.fullPathName()
            # set the tool tip to the dag path so we can hover over and see the path.
            self.mayaObject.setToolTip(self._fullDagPath)
        else:
            om2.MGlobal.displayError("Nothing is selected")

    def selectInMaya(self):
        """ Select Current Object in maya"""
        if self._fullDagPath:
            cmds.select(self._fullDagPath)

    def clearSelection(self):
        """ Clear the active selection"""
        self._fullDagPath = None
        self.mayaObject.clear()
