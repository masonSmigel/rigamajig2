"""
Collapseable Widget
"""
import sys

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui


class CollapsibleHeader(QtWidgets.QWidget):
    """
    Collapsible Header. Used in the collapseable widget.
    """
    COLLASPED_PIXMAP = QtGui.QPixmap(':teRightArrow.png')
    EXPANDED_PIXMAP = QtGui.QPixmap(':teDownArrow.png')

    clicked = QtCore.Signal()

    def __init__(self, text, parent=None, addCheckbox=False):
        """
        Constructor for the header widget
        :param text: Text of the title
        :param parent: Ui parent
        :param addCheckbox: Add a checkbox to the ui header
        """
        super(CollapsibleHeader, self).__init__(parent)

        self.setAutoFillBackground(True)
        self.setBackgroundColor(None)

        self.hasCheckBox = addCheckbox

        self.iconLabel = QtWidgets.QLabel()
        self.iconLabel.setFixedWidth(self.COLLASPED_PIXMAP.width())

        if addCheckbox:
            self.checkbox = QtWidgets.QCheckBox()

        self.textLabel = QtWidgets.QLabel()
        self.textLabel.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.mainLayout.addWidget(self.iconLabel)
        if addCheckbox:
            self.mainLayout.addWidget(self.checkbox)
        self.mainLayout.addWidget(self.textLabel)
        self.mainLayout.addStretch()

        self.setText(text)
        self.setExpanded(False)

    def setText(self, text):
        """ Set the header text"""
        self.textLabel.setText("<b>{0}<b>".format(text))

    def setChecked(self, checked):
        """Set the checkbox to true or false"""
        self.checkbox.setChecked(checked)

    def setBackgroundColor(self, color=None):
        """ Set the header background"""
        if not color:
            color = QtWidgets.QPushButton().palette().color(QtGui.QPalette.Button)

        pallete = self.palette()
        pallete.setColor(QtGui.QPalette.Window, color)
        self.setPalette(pallete)

    def isExpanded(self):
        """return the state of the header"""
        return self._expanded

    def setExpanded(self, expanded):
        """ set the expanded state of the header"""
        self._expanded = expanded

        if self._expanded:
            self.iconLabel.setPixmap(self.EXPANDED_PIXMAP)
        else:
            self.iconLabel.setPixmap(self.COLLASPED_PIXMAP)

    def mouseReleaseEvent(self, event):
        """Emit a signal on mouse release"""
        self.clicked.emit()


class CollapsibleWidget(QtWidgets.QWidget):
    """
    Collpsible widget acts like a maya collapsible widget.

    It can be expanded and contracted to save ui space.
    It allows the user to manage the widgets and layouts added to the self.bodyWidget
    by using methods like addWidget(), addlayout() and addSpacing()
    """

    def __init__(self, text, parent=None, addCheckbox=False):
        super(CollapsibleWidget, self).__init__(parent)

        self.headerWidget = CollapsibleHeader(text, addCheckbox=addCheckbox)
        self.headerWidget.clicked.connect(self.onHeaderClicked)

        self.bodyWidget = QtWidgets.QWidget()
        self.bodyLayout = QtWidgets.QVBoxLayout(self.bodyWidget)
        self.bodyLayout.setContentsMargins(4, 2, 4, 2)
        self.bodyLayout.setSpacing(5)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.headerWidget)
        self.mainLayout.addWidget(self.bodyWidget)

        self.setExpanded(False)

    def addWidget(self, widget):
        """ override default addWidget to add one to the body widget instead"""
        self.bodyLayout.addWidget(widget)

    def addLayout(self, layout):
        """ override default addLayout to add one to the body widget instead"""
        self.bodyLayout.addLayout(layout)

    def addSpacing(self, spacing=10):
        """ Override the default addSpacing to add one to the body widget instead"""
        self.bodyLayout.addSpacing(spacing)

    def setExpanded(self, expanded):
        """ Set the expanded state of the UI"""
        self.headerWidget.setExpanded(expanded)
        self.bodyWidget.setVisible(expanded)

    def setChecked(self, checked):
        """ Set the checked state of the UI"""
        self.headerWidget.checkbox.setChecked(checked)

    def setHeaderBackground(self, color):
        """ Set the header color """
        self.headerWidget.setBackgroundColor(color)

    def setWidgetBackground(self, color):
        """ Set the background color of the pallete"""
        pallete = self.palette()
        pallete.setColor(QtGui.QPalette.Window, color)
        self.setAutoFillBackground(True)
        self.setPalette(pallete)

    def onHeaderClicked(self):
        """ expand or close the ui when the header is clicked"""
        self.setExpanded(not self.headerWidget.isExpanded())

    def isChecked(self):
        """Return the state of the checkbox if one exists. """
        if self.headerWidget.hasCheckBox:
            if self.headerWidget.checkbox.isChecked():
                return True
        return False
