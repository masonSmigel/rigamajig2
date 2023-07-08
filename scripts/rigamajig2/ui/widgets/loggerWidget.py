#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: loggerWidget.py.py
    author: masonsmigel
    date: 07/2023
    discription: 

"""
import os

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds


class LoggerWidget(QtWidgets.QWidget):
    """
    Logger Widget
    """

    def __init__(self):
        """
        Constructor for the logger widget
        """
        super(LoggerWidget, self).__init__()
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setFrame(False)

        # create a monospace font to use in the widget
        loggerFont = QtGui.QFont()
        loggerFont.setFamily('Courier New')
        loggerFont.setBold(True)
        loggerFont.setPointSize(10)

        self.lineEdit.setFont(loggerFont)
        # self.lineEdit.setEnabled(False)

        pallete = self.lineEdit.palette()
        pallete.setColor(QtGui.QPalette.Base, QtGui.QColor(56, 56, 56))
        pallete.setColor(QtGui.QPalette.Text, QtGui.QColor(180, 180, 180))
        # pallete.setColor(QtGui.QPalette.Background, QtGui.QColor(56, 56, 56, 0))
        self.lineEdit.setPalette(pallete)

        self.outputWindowButton = QtWidgets.QPushButton()
        self.outputWindowButton.setIcon(QtGui.QIcon(":cmdWndIcon.png"))
        self.outputWindowButton.setFlat(True) # sets the background to be transparent
        self.outputWindowButton.setFixedSize(19, 19)
        # self.outputWindowButton.setAutoFillBackground(Q)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.lineEdit)
        self.mainLayout.addWidget(self.outputWindowButton)

        # set text
        self.lineEdit.setText("# rigamajig2.maya.builder.builder : guide -- complete #")

