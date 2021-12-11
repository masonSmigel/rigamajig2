import sys

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


class CollapsibleHeader(QtWidgets.QWidget):
    COLLASPED_PIXMAP = QtGui.QPixmap(':teRightArrow.png')
    EXPANDED_PIXMAP = QtGui.QPixmap(':teDownArrow.png')

    clicked = QtCore.Signal()

    def __init__(self, text, parent=None):
        super(CollapsibleHeader, self).__init__(parent)

        self.setAutoFillBackground(True)
        self.set_background_color(None)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedWidth(self.COLLASPED_PIXMAP.width())

        self.text_label = QtWidgets.QLabel()
        self.text_label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(3, 3, 3, 3)
        self.main_layout.addWidget(self.icon_label)
        self.main_layout.addWidget(self.text_label)

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

    def __init__(self, text, parent=None):
        super(CollapsibleWidget, self).__init__(parent)

        self.header_wdg = CollapsibleHeader(text)
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

    def set_expanded(self, expanded):
        self.header_wdg.set_expanded(expanded)
        self.body_wdg.setVisible(expanded)

    def set_header_background_color(self, color):
        self.header_wdg.set_background_color(color)

    def on_header_clicked(self):
        self.set_expanded(not self.header_wdg.is_expanded())


class TestDialog(QtWidgets.QDialog):
    WINDOW_TITLE = "Test Dialog"

    def __init__(self, parent=maya_main_window()):
        super(TestDialog, self).__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(QtCore.Qt.Tool)

        self.setMinimumSize(250, 200)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.collapsible_wdg_a = CollapsibleWidget("Section A")
        self.collapsible_wdg_a.set_expanded(True)

        self.collapsible_wdg_a.set_header_background_color(QtCore.Qt.blue)
        for i in range(6):
            self.collapsible_wdg_a.addWidget(QtWidgets.QPushButton("Button {}".format(i)))

        self.collapsible_wdg_c = CollapsibleWidget("Section C")
        self.collapsible_wdg_a.addWidget(self.collapsible_wdg_c)
        for i in range(6):
            self.collapsible_wdg_c.addWidget(QtWidgets.QPushButton("Button C {}".format(i)))

        self.collapsible_wdg_b = CollapsibleWidget("Section B")
        layout = QtWidgets.QFormLayout()
        for i in range(6):
            layout.addRow("Row {0}".format(i), QtWidgets.QCheckBox())

        self.collapsible_wdg_b.addLayout(layout)

    def create_layout(self):

        self.body_wdg = QtWidgets.QWidget()

        self.body_layout = QtWidgets.QVBoxLayout(self.body_wdg)
        self.body_layout.setContentsMargins(4, 2, 4, 2)
        self.body_layout.setSpacing(3)
        self.body_layout.setAlignment(QtCore.Qt.AlignTop)

        self.body_layout.addWidget(self.collapsible_wdg_a)
        self.body_layout.addWidget(self.collapsible_wdg_b)

        self.body_scroll_area = QtWidgets.QScrollArea()
        self.body_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.body_scroll_area.setWidgetResizable(True)
        self.body_scroll_area.setWidget(self.body_wdg)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.body_scroll_area)


if __name__ == "__main__":

    try:
        test_dialog.close()  # pylint: disable=E0601
        test_dialog.deleteLater()
    except:
        pass

    test_dialog = TestDialog()
    test_dialog.show()
