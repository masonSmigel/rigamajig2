"""
This module contains the override colorer
"""
from functools import partial

import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import rigamajig2.maya.color as rig_color


class OverrideColorer(QtWidgets.QWidget):
    """
    A small line ui to apply an override color to transform elements.

    The UI inlcudes a line edit to type in the name of the color,
    A swatch pixmap that displays a context menu of all avialable colors
    A button to apply the color to the selection
    """

    color_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(OverrideColorer, self).__init__(parent)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

        self.setColorSwatch(self.getColor())

    def createWidgets(self):
        """ Create widgets"""
        self.colorLineEdit = QtWidgets.QLineEdit()
        self.colorLineEdit.setPlaceholderText("blue")
        self.colorLineEdit.setFixedHeight(24)

        completer = QtWidgets.QCompleter()
        completerModel = QtCore.QStringListModel()
        completerModel.setStringList(rig_color.COLORS.keys())
        completer.setModel(completerModel)
        self.colorLineEdit.setCompleter(completer)

        self.colorSwatch = QtWidgets.QLabel()
        self.colorSwatch.setFixedSize(24, 24)

        self.applyColorButton = QtWidgets.QPushButton("Apply Color")
        self.applyColorButton.setFixedHeight(24)

    def createLayouts(self):
        """ Create Layouts and setup the layout"""
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(4)

        self.mainLayout.addWidget(self.colorLineEdit)
        self.mainLayout.addWidget(self.colorSwatch)
        self.mainLayout.addWidget(self.applyColorButton)

    def createConnections(self):
        """ Create connections"""
        self.colorLineEdit.textChanged.connect(self.updateColor)
        self.applyColorButton.clicked.connect(self.applyColor)

    def createContextMenu(self):
        """ Create a context menu """
        self.colorPresetsMenu = QtWidgets.QMenu()
        for color in sorted(rig_color.getAvailableColors()):
            action = QtWidgets.QAction(color, self)
            action.setIcon(QtGui.QIcon(self._getPixmapFromName(color)))
            self.colorPresetsMenu.addAction(action)
            action.triggered.connect(partial(self.setColorText, color))
        return self.colorPresetsMenu

    def getColor(self):
        """ Get color from the color line edit"""
        color = self.colorLineEdit.text()
        if not color: color = self.colorLineEdit.placeholderText()
        return str(color)

    def setColorSwatch(self, color):
        """
        set the color
        :param color: color as a string
        """
        self.colorSwatch.setPixmap(self._getPixmapFromName(color))

    def setColorText(self, text):
        """ Set the color text """
        self.colorLineEdit.setText(text)

    def updateColor(self):
        """ Update the swatch based on the color"""
        color = self.colorLineEdit.text()
        if color in rig_color.COLORS:
            self.setColorSwatch(color=color)

    def _getPixmapFromName(self, name):
        """ Get the matching pixmap from a given name"""
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtGui.QColor(rig_color.COLORS[name][0], rig_color.COLORS[name][1], rig_color.COLORS[name][2]))
        return pixmap

    def applyColor(self):
        """ Apply the color to the active selection """
        selection = cmds.ls(sl=True, type='transform')
        color = self.getColor()
        if color not in rig_color.COLORS:
            raise RuntimeError("{} is not a valid color".format(color))
        if selection:
            rig_color.setOverrideColor(selection, color)

    def mousePressEvent(self, event):
        """ Override the default behavior of the mouse press event"""
        super(OverrideColorer, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            p = self.mapToGlobal(event.pos())  # or QtGui.QCursor.pos()
            menu = self.createContextMenu()
            action = menu.exec_(p)
