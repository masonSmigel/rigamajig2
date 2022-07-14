import sys

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui


class CollapsibleHeader(QtWidgets.QWidget):
    COLLASPED_PIXMAP = QtGui.QPixmap(':teRightArrow.png')
    EXPANDED_PIXMAP = QtGui.QPixmap(':teDownArrow.png')

    clicked = QtCore.Signal()

    def __init__(self, text, parent=None, addCheckbox=False):
        super(CollapsibleHeader, self).__init__(parent)

        self.setAutoFillBackground(True)
        self.set_background_color(None)

        self._haschbx = addCheckbox

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedWidth(self.COLLASPED_PIXMAP.width())

        if addCheckbox:
            self.checkbox = QtWidgets.QCheckBox()

        self.text_label = QtWidgets.QLabel()
        self.text_label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.addWidget(self.icon_label)
        if addCheckbox:
            self.main_layout.addWidget(self.checkbox)
        self.main_layout.addWidget(self.text_label)
        self.main_layout.addStretch()

        self.set_text(text)
        self.set_expanded(False)

    def set_text(self, text):
        self.text_label.setText("<b>{0}<b>".format(text))

    def set_background_color(self, color=None):
        if not color:
            color = QtWidgets.QPushButton().palette().color(QtGui.QPalette.Button)

        pallete = self.palette()
        pallete.setColor(QtGui.QPalette.Window, color)
        self.setPalette(pallete)

    def is_expanded(self):
        return self._expanded

    def set_expanded(self, expanded):
        self._expanded = expanded

        if self._expanded:
            self.icon_label.setPixmap(self.EXPANDED_PIXMAP)
        else:
            self.icon_label.setPixmap(self.COLLASPED_PIXMAP)

    def mouseReleaseEvent(self, event):
        self.clicked.emit()


class CollapsibleWidget(QtWidgets.QWidget):

    def __init__(self, text, parent=None, addCheckbox=False):
        super(CollapsibleWidget, self).__init__(parent)

        self.header_wdg = CollapsibleHeader(text, addCheckbox=addCheckbox)
        self.header_wdg.clicked.connect(self.on_header_clicked)

        self.body_wdg = QtWidgets.QWidget()
        self.body_layout = QtWidgets.QVBoxLayout(self.body_wdg)
        self.body_layout.setContentsMargins(4, 2, 4, 2)
        self.body_layout.setSpacing(5)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.header_wdg)
        self.main_layout.addWidget(self.body_wdg)

        self.set_expanded(False)

    def addWidget(self, widget):
        """ override default addWidget to add one to the body widget instead"""
        self.body_layout.addWidget(widget)

    def addLayout(self, layout):
        """ override default addLayout to add one to the body widget instead"""
        self.body_layout.addLayout(layout)

    def addSpacing(self, spacing=10):
        """ override the default addSpacing to add one to the body widget instead"""
        self.body_layout.addSpacing(spacing)

    def set_expanded(self, expanded):
        self.header_wdg.set_expanded(expanded)
        self.body_wdg.setVisible(expanded)

    def set_checked(self, checked):
        self.header_wdg.checkbox.setChecked(checked)

    def set_header_background_color(self, color):
        self.header_wdg.set_background_color(color)

    def set_widget_background_color(self, color):
        pallete = self.palette()
        pallete.setColor(QtGui.QPalette.Window, color)
        self.setAutoFillBackground(True)
        self.setPalette(pallete)

    def on_header_clicked(self):
        self.set_expanded(not self.header_wdg.is_expanded())

    def isChecked(self):
        if self.header_wdg._haschbx:
            if self.header_wdg.checkbox.isChecked():
                return True
        return False


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)
