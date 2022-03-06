"""
This module contains the file selector widget
"""
import os

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds


class SliderGroup(QtWidgets.QWidget):

    def __init__(self, min=0, max=10, value=0, sliderIncriment=1 ,*args, **kwargs):
        super(SliderGroup, self).__init__(*args, **kwargs)
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setFixedWidth(50)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.setMinimun(min)
        self.setMaximum(max)
        self.setIncriment(sliderIncriment)
        self.setValue(value)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.addWidget(self.lineEdit)
        self.main_layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self.updateLineEdit)
        self.lineEdit.textChanged.connect(self.updateSlider)

    def setMinimun(self, val):
        self.slider.setMinimum(val)

    def setMaximum(self, val):
        self.slider.setMaximum(val)

    def setIncriment(self, val):
        self.slider.setTickInterval(val)

    def setValue(self, val):
        self.slider.setValue(val)

    def getValue(self):
        return self.slider.value()

    def updateLineEdit(self):
        self.lineEdit.setText(str(self.slider.value()))

    def updateSlider(self):
        self.slider.setValue(float(self.lineEdit.text()))