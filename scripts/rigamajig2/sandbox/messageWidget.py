#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: messageWidget.py
    author: masonsmigel
    date: 08/2022
    discription: 

"""
import os

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds


class MessageWidget(QtWidgets.QWidget):
    """
    Slider Widget
    """

    INFO_ICON = ":info.png"
    WARN_ICON = ":caution.png"
    ERROR_ICON = ":error.png"

    def __init__(self, level='info', message='', display=True):
        """
        Constructor for the MessageWidget widget
        :param level: importance of the message. Valid values are: "info", "warn", "error"
        :param message: message to display along with the icon
        """
        super(MessageWidget, self).__init__()

        self.level = level

        if self.level == 'warn':
            icon = self.WARN_ICON
            # stylesheet =
        elif self.level == 'error':
            icon = self.ERROR_ICON
        else:
            icon = self.INFO_ICON

        self.pixmap = QtGui.QPixmap(icon)
        self.pixmap.scaled(10, 10, QtCore.Qt.KeepAspectRatio)
        self.iconLabel = QtWidgets.QLabel()
        self.iconLabel.setScaledContents(False)
        self.iconLabel.setPixmap(self.pixmap)
        self.iconLabel.setFixedSize(32, 32)

        self.messageLabel = QtWidgets.QLabel()
        self.setMessage(message)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.iconLabel)
        self.mainLayout.addWidget(self.messageLabel)

        if not display:
            self.setMessageEnabled(False)

    def setMessage(self, text):
        """Set the message of the text"""

        self.messageLabel.setText(text)

    def setMessageEnabled(self, value):
        """ Set the message enabled"""
        if value:
            self.iconLabel.setHidden(False)
            self.messageLabel.setHidden(False)
        else:
            self.iconLabel.setHidden(True)
            self.messageLabel.setHidden(True)
