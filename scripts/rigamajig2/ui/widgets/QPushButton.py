#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: QPushButton.py
    author: masonsmigel
    date: 08/2023
    discription: 

"""
from PySide2 import QtCore
from PySide2 import QtWidgets


class RightClickableButton(QtWidgets.QPushButton):
    rightClicked = QtCore.Signal()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.rightClicked.emit()
        else:
            super().mousePressEvent(event)
