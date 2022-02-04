"""
This module contains the file selector widget
"""
import os

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds


class PathSelector(QtWidgets.QWidget):
    def __init__(self, label=None, cap='Select a file or Folder', ff="All Files (*.*)", fm=1, relativeTo=None,
                 parent=None):
        super(PathSelector, self).__init__(parent)
        self.cap = cap
        self.ff = ff
        self.fm = fm
        self.relaiveTo = relativeTo
        self.label = label

        self.path_label = QtWidgets.QLabel()

        self.path_le = QtWidgets.QLineEdit()
        self.path_le.setPlaceholderText("path/to/file/or/folder")

        self.select_path_btn = QtWidgets.QPushButton("...")
        self.select_path_btn.setFixedSize(24, 19)
        self.select_path_btn.setToolTip(self.cap)
        self.select_path_btn.clicked.connect(self.select_path)

        self.show_in_folder_btn = QtWidgets.QPushButton(QtGui.QIcon(":fileOpen.png"), "")
        self.show_in_folder_btn.setFixedSize(24, 19)
        self.show_in_folder_btn.setToolTip("Show in Folder")
        self.show_in_folder_btn.clicked.connect(self.show_in_folder)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)
        if self.label is not None:
            self.main_layout.addWidget(self.path_label)
            self.set_label_text(self.label)
            self.path_label.setFixedWidth(50)

        self.main_layout.addWidget(self.path_le)
        self.main_layout.addWidget(self.select_path_btn)
        self.main_layout.addWidget(self.show_in_folder_btn)

    def set_path(self, path):
        self.path_le.setText(path)

    def select_path(self, path=None):
        """
        Select an existing path. this is smarter than set path because it will create a dailog and check if the path exists.
        :param path:
        :return:
        """
        current_path = self.path_le.text()
        if not current_path:
            current_path = self.path_le.placeholderText()

        if not path:
            file_info = QtCore.QFileInfo(current_path)
            if not file_info.exists():
                current_path = cmds.workspace(q=True, dir=True)

            new_path = cmds.fileDialog2(ds=2, cap=self.cap, ff=self.ff, fm=self.fm, okc='Select', dir=current_path)
            if new_path: new_path = new_path[0]
        else:
            new_path = path

        if new_path and os.path.exists(new_path):
            self.path_le.setText(self.resolve_path(new_path))

    def show_in_folder(self):
        file_path = self.get_abs_path()

        if cmds.about(windows=True):
            if self.open_in_explorer(file_path):
                return
        elif cmds.about(macOS=True):
            if self.open_in_finder(file_path):
                return

        file_info = QtCore.QFileInfo(file_path)
        if file_info.exists():
            if file_info.isDir():
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_path))
            else:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_info.path()))
        else:
            cmds.error("Invalid Directory")

    def open_in_explorer(self, file_path):
        file_info = QtCore.QFileInfo(file_path)
        args = []
        if not file_info.isDir():
            args.append("/select,")
        args.append(QtCore.QDir.toNativeSeparators(file_path))

        if QtCore.QProcess.startDetached("explorer", args):
            return True

        return False

    def open_in_finder(self, file_path):
        args = ['-e', 'tell application "Finder"', '-e', 'activate', '-e', 'select POSIX file "{0}"'.format(file_path),
                '-e', 'end tell', '-e', 'return']

        if QtCore.QProcess.startDetached("/usr/bin/osascript", args):
            return True

        return False

    def resolve_path(self, path):
        if self.relaiveTo:
            return os.path.relpath(path, self.relaiveTo)
        return path

    def get_path(self):
        return self.path_le.text()

    def get_abs_path(self):
        if self.path_le.text():
            if self.relaiveTo:
                return os.path.abspath(os.path.join(self.relaiveTo, self.path_le.text()))
            else:
                return self.path_le.text()

    def set_relativeTo(self, relativeTo):
        self.relaiveTo = relativeTo

    def set_label_text(self, text):
        self.path_label.setText(text)
