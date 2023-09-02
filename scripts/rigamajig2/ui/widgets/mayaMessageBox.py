#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: mayaMessageBox.py.py
    author: masonsmigel
    date: 09/2023
    discription: 

"""

from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore


class MayaMessageBox(QtWidgets.QMessageBox):

    def setMayaIcon(self, icon):
        iconToUse = None

        if icon == "help":
            iconToUse = ":helpModal.png"
        if icon == 'warning':
            iconToUse = ":warningModal.png"
        if icon == "error":
            iconToUse = ":errorModal.png"
        if icon == "info":
            iconToUse = ":infoModal.png"

        pixmap = QtGui.QIcon(iconToUse).pixmap(QtCore.QSize(64, 64))
        self.setIconPixmap(pixmap)

    def setInfo(self):
        self.setMayaIcon("info")

    def setHelp(self):
        self.setMayaIcon("help")

    def setWarning(self):
        self.setMayaIcon("warning")

    def setError(self):
        self.setMayaIcon("error")

