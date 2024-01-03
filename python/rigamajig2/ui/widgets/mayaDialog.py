#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: mayaDialog.py.py
    author: masonsmigel
    date: 09/2023
    description: 

"""
import sys

import maya.OpenMayaUI as omui
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

from rigamajig2.ui.palettes import RigamajigPalette


class MayaDialog(QtWidgets.QDialog):
    """Dialog for the mocap import"""

    WINDOW_TITLE = "Maya Dialog"
    WINDOW_SIZE = (600, 400)
    PALETTE = RigamajigPalette.palette

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

        self.setMinimumSize(*self.WINDOW_SIZE)

        if self.PALETTE:
            self.setPalette(self.PALETTE)

        self.__actions__()
        self.__menus__()
        self.__create__()
        self.__layout__()
        self.__configure__()
        self.__connect__()

    def __actions__(self):
        """Create Actions"""
        ...

    def __menus__(self):
        """Create Actions"""
        ...

    def __create__(self):
        """Create widgets"""
        ...

    def __layout__(self):
        """Create layouts"""
        ...

    def __configure__(self):
        ...

    def __connect__(self):
        """Create Pyside connections"""
        ...
