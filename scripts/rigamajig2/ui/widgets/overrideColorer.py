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

        self.set_color_swatch(self.get_color())

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
        self.color_le.textChanged.connect(self.update_swatch)
        self.apply_color_btn.clicked.connect(self.apply_color)

    def create_context_menu(self):
        self.colorPresets_menu = QtWidgets.QMenu()
        for color in sorted(rig_color.getAvailableColors()):
            action = QtWidgets.QAction(color, self)
            action.setIcon(QtGui.QIcon(self.__get_pixmap_from_name(color)))
            self.colorPresets_menu.addAction(action)
            action.triggered.connect(partial(self.set_color_text, color))
        return self.colorPresets_menu

    def get_color(self):
        color = self.color_le.text()
        if not color: color = self.color_le.placeholderText()
        return str(color)

    def set_color_swatch(self, color):
        """
        set the color
        :param color: color as a string
        """
        self.color_swatch.setPixmap(self.__get_pixmap_from_name(color))

    def set_color_text(self, text):
        self.color_le.setText(text)

    def update_swatch(self):
        color = self.color_le.text()
        if color in rig_color.COLORS:
            self.set_color_swatch(color=color)

    def __get_pixmap_from_name(self, name):
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtGui.QColor(rig_color.COLORS[name][0], rig_color.COLORS[name][1], rig_color.COLORS[name][2]))
        return pixmap

    def apply_color(self):
        selection = cmds.ls(sl=True, type='transform')
        color = self.get_color()
        if color not in rig_color.COLORS:
            raise RuntimeError("{} is not a valid color".format(color))
        if selection:
            rig_color.setOverrideColor(selection, color)

    def mousePressEvent(self, event):
        super(OverrideColorer, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            p = self.mapToGlobal(event.pos())  # or QtGui.QCursor.pos()
            menu = self.create_context_menu()
            action = menu.exec_(p)
