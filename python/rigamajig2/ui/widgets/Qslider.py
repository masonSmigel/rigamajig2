"""
This module contains the slider group pyside widget
"""

from PySide2 import QtCore
from PySide2 import QtWidgets


class QSlider(QtWidgets.QWidget):
    """
    Slider Widget
    """

    def __init__(self, min=0, max=10, value=0, sliderIncriment=1):
        """
        Constructor for the sliderGroup widget
        :param min: minimum value of the slider
        :param max: maximum value of the slider
        :param value: value of the slider
        :param sliderIncriment: incriment the slider increases by
        """
        super(QSlider, self).__init__()
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setFixedWidth(50)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.addWidget(self.lineEdit)
        self.mainLayout.addWidget(self.slider)

        self.slider.valueChanged.connect(self.updateLineEdit)
        self.lineEdit.textChanged.connect(self.updateSlider)

        self.setMinimun(min)
        self.setMaximum(max)
        self.setIncriment(sliderIncriment)
        self.setValue(value)

    def setMinimun(self, val):
        """ set the slider minimum"""
        self.slider.setMinimum(val)

    def setMaximum(self, val):
        """ set the slider maximum"""
        self.slider.setMaximum(val)

    def setRange(self, min, max):
        """ Set the slider range"""
        self.setMinimun(min)
        self.setMaximum(max)

    def setIncriment(self, val):
        """ Set the slider tick interval"""
        self.slider.setTickInterval(val)

    def setValue(self, val):
        """ Set the widgets value"""
        self.slider.setValue(val)

    def getValue(self):
        """ Get the widget value"""
        return self.slider.value()

    def updateLineEdit(self):
        """ Update the line edit"""
        self.lineEdit.setText(str(self.slider.value()))

    def updateSlider(self):
        """ Update the slider"""
        if int(self.lineEdit.text()) > self.slider.maximum():
            self.setMaximum(int(self.lineEdit.text()))
        self.slider.setValue(float(self.lineEdit.text()))