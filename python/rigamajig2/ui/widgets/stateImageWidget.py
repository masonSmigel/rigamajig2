#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: statusIcon.py.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
from enum import Enum

from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout


class State(Enum):
    GOOD = "good"
    WARNING = "warning"
    ERROR = "error"


class StateImageWidget(QWidget):
    def __init__(self, parent=None, image_size=12):
        super(StateImageWidget, self).__init__(parent)
        self.imageSize = image_size

        self.stateImages = {
            State.GOOD: ":statusGood.png",
            State.WARNING: ":warningModal.png",
            State.ERROR: ":errorModal.png",
        }

        self.imageLabel = QLabel(self)
        self.imageLabel.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.imageLabel)
        layout.setAlignment(Qt.AlignCenter)

        self.setDefaultState()

    def setDefaultState(self):
        self.setState(State.GOOD)

    def setState(self, state, message=None):
        if state in self.stateImages:
            try:
                _imagePath = self.stateImages[state]
                _originalPixmap = QPixmap(_imagePath)
            except FileNotFoundError:
                raise FileNotFoundError(" Unable to find the image")
            else:
                _scaledPixmap = _originalPixmap.scaled(
                    self.imageSize, self.imageSize, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.imageLabel.setPixmap(_scaledPixmap)
                self.setToolTip(message)
        else:
            raise ValueError(f"Invalid state: {state}")
