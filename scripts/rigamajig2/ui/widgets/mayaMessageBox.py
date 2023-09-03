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
    def __init__(self, title=None, message=None, icon=None):
        super().__init__()

        if title:
            self.setText(title)
        if message:
            self.setInformativeText(message)
        if icon:
            self.setMayaIcon(icon=icon)

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

    def setButtonsSaveDiscardCancel(self):
        """
        Set the standard buttons to:
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel

        with the default button to:
            QtWidgets.QMessageBox.Save
        """
        self.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
        self.setDefaultButton(QtWidgets.QMessageBox.Save)

    def setButtonsYesNoCancel(self):
        """
        Set the standard buttons to:
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel

        with the default button to:
            QtWidgets.QMessageBox.Yes
        """
        self.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        self.setDefaultButton(QtWidgets.QMessageBox.Yes)