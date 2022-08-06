"""
This module contains the override colorer
"""
import os
from functools import partial

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds

import rigamajig2.maya.color as rig_color


class OverrideColorer(QtWidgets.QWidget):
    color_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(OverrideColorer, self).__init__(parent)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

        self.setColorSwatch(self.getColor())

    def create_widgets(self):
        self.color_le = QtWidgets.QLineEdit()
        self.color_le.setPlaceholderText("blue")
        self.color_le.setFixedHeight(24)

        completer = QtWidgets.QCompleter()
        completer_model = QtCore.QStringListModel()
        completer_model.setStringList(rig_color.COLORS.keys())
        completer.setModel(completer_model)
        self.color_le.setCompleter(completer)

        self.color_swatch = QtWidgets.QLabel()
        self.color_swatch.setFixedSize(24, 24)

        self.apply_color_btn = QtWidgets.QPushButton("Apply Color")
        self.apply_color_btn.setFixedHeight(24)

    def create_layouts(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)

        self.main_layout.addWidget(self.color_le)
        self.main_layout.addWidget(self.color_swatch)
        self.main_layout.addWidget(self.apply_color_btn)

    def create_connections(self):
        self.color_le.textChanged.connect(self.updateColor)
        self.apply_color_btn.clicked.connect(self.applyColor)

    def createContextMenu(self):
        self.colorPresets_menu = QtWidgets.QMenu()
        for color in sorted(rig_color.getAvailableColors()):
            action = QtWidgets.QAction(color, self)
            action.setIcon(QtGui.QIcon(self._getPixmapFromName(color)))
            self.colorPresets_menu.addAction(action)
            action.triggered.connect(partial(self.setColorText, color))
        return self.colorPresets_menu

    def getColor(self):
        """ Get color from the color line edit"""
        color = self.color_le.text()
        if not color: color = self.color_le.placeholderText()
        return str(color)

    def setColorSwatch(self, color):
        """
        set the color
        :param color: color as a string
        """
        self.color_swatch.setPixmap(self._getPixmapFromName(color))

    def setColorText(self, text):
        """ Set the color text """
        self.color_le.setText(text)

    def updateColor(self):
        """ Update the swatch based on the color"""
        color = self.color_le.text()
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
