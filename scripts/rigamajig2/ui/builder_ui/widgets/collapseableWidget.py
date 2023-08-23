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

from rigamajig2.shared import common

darkPalette = QtGui.QPalette()

# base
darkPalette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(180, 180, 180))
darkPalette.setColor(QtGui.QPalette.Button, QtGui.QColor(66, 66, 66))
darkPalette.setColor(QtGui.QPalette.Light, QtGui.QColor(180, 180, 180))
darkPalette.setColor(QtGui.QPalette.Midlight, QtGui.QColor(90, 90, 90))
darkPalette.setColor(QtGui.QPalette.Dark, QtGui.QColor(35, 35, 35))
darkPalette.setColor(QtGui.QPalette.Text, QtGui.QColor(180, 180, 180))
darkPalette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(180, 180, 180))
darkPalette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(180, 180, 180))
darkPalette.setColor(QtGui.QPalette.Base, QtGui.QColor(42, 42, 42))
darkPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
darkPalette.setColor(QtGui.QPalette.Shadow, QtGui.QColor(20, 20, 20))
darkPalette.setColor(QtGui.QPalette.Link, QtGui.QColor(56, 252, 196))
darkPalette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(72, 72, 72))
darkPalette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(53, 53, 53))
darkPalette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(180, 180, 180))
darkPalette.setColor(QtGui.QPalette.LinkVisited, QtGui.QColor(80, 80, 80))

# disabled
darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, QtGui.QColor(127, 127, 127))
darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(127, 127, 127))
darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtGui.QColor(127, 127, 127))
darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, QtGui.QColor(80, 80, 80))
darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText, QtGui.QColor(127, 127, 127))


class breakpointCheckbox(QtWidgets.QCheckBox):

    def __init__(self, *args, **kwargs):
        super(breakpointCheckbox, self).__init__(*args, **kwargs)

        styleSheet = (f"""
                    QCheckBox {{
                        spacing: 5px;
                    }}
                    
                    QCheckBox::indicator {{
                        width: 13px;
                        height: 13px;
                    }}
                    
                    QCheckBox::indicator:unchecked {{
                        image: url({common.ICONS_PATH}/breakpoint_unchecked.png);
                    }}
                    
                    QCheckBox::indicator:unchecked:hover {{
                        image: url({common.ICONS_PATH}/breakpoint_hover.png);
                    }}
                    
                    QCheckBox::indicator:unchecked:pressed {{
                        image: url({common.ICONS_PATH}/breakpoint_checkedPress.png);
                    }}
                    
                    QCheckBox::indicator:checked {{
                        image: url({common.ICONS_PATH}/breakpoint_checked.png);
                    }}
                    
                    QCheckBox::indicator:checked:hover {{
                        image: url({common.ICONS_PATH}/breakpoint_checked.png);
                    }}
                    
                    QCheckBox::indicator:checked:pressed {{
                        image: url({common.ICONS_PATH}/breakpoint_checkedPress.png);
                    }}
                    """)
        self.setStyleSheet(styleSheet)


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
            self.checkbox = breakpointCheckbox()

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

        # set the size policy so collapseable widgets size correctly
        # when parented to another collapseable widget
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)

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

    def setDarkPallete(self):
        """ Set the background color of the pallete"""
        self.setPalette(darkPalette)
        self.setAutoFillBackground(True)

    def onHeaderClicked(self):
        """ expand or close the ui when the header is clicked"""
        self.setExpanded(not self.headerWidget.isExpanded())

    def isChecked(self):
        """Return the state of the checkbox if one exists. """
        if self.headerWidget.hasCheckBox:
            if self.headerWidget.checkbox.isChecked():
                return True
        return False


class BuilderHeader(CollapsibleWidget):

    headerCheckedColor = QtGui.QColor(78, 116, 125)
    headerDefaultColor = QtWidgets.QPushButton().palette().color(QtGui.QPalette.Button)

    def __init__(self, text, parent=None, addCheckbox=False):
        super(BuilderHeader, self).__init__(text, parent, addCheckbox)

        # set the check of the header to set-checked method.
        self.headerWidget.checkbox.clicked.connect(self.setChecked)

    def setChecked(self, checked):
        super(BuilderHeader, self).setChecked(checked)

        color = self.headerCheckedColor if checked else self.headerDefaultColor
        self.setHeaderBackground(color=color)
