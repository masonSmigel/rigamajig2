#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: mayaDialog.py.py
    author: masonsmigel
    date: 09/2023
    discription: 

"""
import sys
from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.cmds as cmds


class MayaDialog(QtWidgets.QDialog):
    """ Dialog for the mocap import """
    WINDOW_TITLE = "Maya Dialog"

    dlg_instance = None

    @classmethod
    def showDialog(cls):
        """Show the dialog"""
        if not cls.dlg_instance:
            cls.dlg_instance = cls()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self):
        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(MayaDialog, self).__init__(mayaMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """Create widgets"""
        pass

    def createLayouts(self):
        """Create layouts"""
        pass

    def createConnections(self):
        """Create Pyside connections"""
        pass
