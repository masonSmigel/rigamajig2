#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: statusLine.py
    author: masonsmigel
    date: 07/2023
    discription: 

"""
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore

import maya.cmds as cmds
import maya.mel as mel


class StatusLine(QtWidgets.QWidget):
    """
    The Status line widget is very similar to a QLabel however it includes an icon that can be set to three states:
    "info", "sucess", "fail" along with a message this can be useful for providing the user with imediate feedback as
    the state of the application overall
    """

    clicked = QtCore.Signal()

    INFO_ICON = QtGui.QPixmap(":info.png")
    SUCCESS_ICON = QtGui.QPixmap(":confirm.png")
    FAILED_ICON = QtGui.QPixmap(":error.png")

    ICONS_DICT = {"info": INFO_ICON,
                  "success": SUCCESS_ICON,
                  "failed": FAILED_ICON}

    def __init__(self):
        """
        Constructor for the status line widget
        """
        super(StatusLine, self).__init__()

        self.messageLabel = QtWidgets.QLabel()
        self.iconLabel = QtWidgets.QLabel()

        mainLayout = QtWidgets.QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setToolTip("Status line. Click to open Script Editor.")

        mainLayout.addWidget(self.iconLabel)
        mainLayout.addWidget(self.messageLabel)

        # connect the main widget to a function to open up the script editor
        self.clicked.connect(self.openScriptEditor)

    def setStatusMessage(self, message, icon):

        if message:
            self.messageLabel.setText(message)
        if icon:
            properPixmap = self.ICONS_DICT.get(icon)
            if properPixmap:
                self.iconLabel.setScaledContents(True)
                self.iconLabel.setPixmap(properPixmap)
                self.iconLabel.setFixedSize(15, 15)
            else:
                raise ValueError("f{icon} is not a valid icon type")

    def openScriptEditor(self):
        """Open the script Editor"""

        if cmds.pluginInfo("CharcoalEditor2", q=True, loaded=True):
            mel.eval("charcoalEditor2;")
        else:
            mel.eval("ScriptEditor;")

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
