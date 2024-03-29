#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: mayaMessageBox.py.py
    author: masonsmigel
    date: 09/2023
    description: 

"""

from PySide2 import QtWidgets

from rigamajig2.ui.resources import Resources


class MayaMessageBox(QtWidgets.QMessageBox):
    def __init__(self, title=None, message=None, icon=None):
        super().__init__()

        self.confirmResultButton = None

        if title:
            self.setText(title)
        if message:
            self.setInformativeText(message)
        if icon:
            self.setMayaIcon(icon=icon)

    def setMayaIcon(self, icon):
        iconToUse = None

        if icon == "help":
            iconToUse = Resources.getIcon(":helpModal.png")
        if icon == "warning":
            iconToUse = Resources.getIcon(":warningModal.png")
        if icon == "error":
            iconToUse = Resources.getIcon(":errorModal.png")
        if icon == "info":
            iconToUse = Resources.getIcon(":infoModal.png")

        self.setIconPixmap(Resources.iconToPixmap(iconToUse, size=(64, 64)))

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
        self.setStandardButtons(
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
        )
        self.setDefaultButton(QtWidgets.QMessageBox.Save)
        self.confirmResultButton = QtWidgets.QMessageBox.Save

    def setButtonsYesNoCancel(self):
        """
        Set the standard buttons to:
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel

        with the default button to:
            QtWidgets.QMessageBox.Yes
        """
        self.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        self.setDefaultButton(QtWidgets.QMessageBox.Yes)
        self.confirmResultButton = QtWidgets.QMessageBox.Yes

    def getResult(self) -> bool:
        """
        Returns a true or false value based on the result of the message box.
        Must have used setButtonsSaveDiscardCancel or setButtonsYesNoCancel"""

        if not self.confirmResultButton:
            raise ValueError(
                "No default button setup intialized. Please use setButtonsSaveDiscardCancel or setButtonsYesNoCancel"
            )

        result = self.exec_()

        if result == self.confirmResultButton:
            return True
        return False
