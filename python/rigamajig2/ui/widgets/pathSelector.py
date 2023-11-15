"""
This module contains the file selector widget
"""
import os

import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets

from rigamajig2.ui import showInFolder
from rigamajig2.ui.resources import Resources


class PathSelector(QtWidgets.QWidget):
    """ Widget to select valid file or folder paths. Emits the pathUpdated signal when the path is changed."""

    pathUpdated = QtCore.Signal(str)

    def __init__(
            self,
            label=None,
            caption='Select a file or Folder',
            fileFilter="All Files (*.*)",
            fileMode=1,
            relativePath=None,
            parent=None
    ):
        """
        :param label: label to give the path selector
        :param caption: hover over caption
        :param fileFilter: List of file type filters to the dialog. Multiple filters should be separated by double semi-colons.
        :param fileMode: Indicate what the dialog is to return.
                         0 Any file, whether it exists or not.
                         1 A single existing file.
                         2 The name of a directory. Both directories and files are displayed in the dialog.
                         3 The name of a directory. Only directories are displayed in the dialog.
                         4 Then names of one or more existing files.

        :param relativePath: if a relative path is set the path is stored relative to this path.
        :param parent: Pyqt parent for the widget
        """
        super(PathSelector, self).__init__(parent)
        self.caption = caption
        self.fileFilter = fileFilter
        self.fileMode = fileMode
        self.relativePath = relativePath
        self.label = label

        self.pathLabel = QtWidgets.QLabel()

        self.pathLineEdit = QtWidgets.QLineEdit()
        self.pathLineEdit.setPlaceholderText("path/to/file/or/folder")
        self.pathLineEdit.editingFinished.connect(self.emitPathUpdatedSignal)

        self.selectPathButton = QtWidgets.QPushButton()
        self.selectPathButton.setIcon(Resources.getIcon(":returnArrow.png"))
        self.selectPathButton.setFixedSize(24, 19)
        self.selectPathButton.setToolTip(self.caption)
        self.selectPathButton.setFlat(True)
        self.selectPathButton.clicked.connect(self.pickPath)

        self.showInFolderButton = QtWidgets.QPushButton()
        self.showInFolderButton.setIcon(Resources.getIcon(":fileOpen.png"))
        self.showInFolderButton.setFixedSize(24, 19)
        self.showInFolderButton.setToolTip("Show in Folder")
        self.showInFolderButton.setFlat(True)
        self.showInFolderButton.clicked.connect(self.showInFolder)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(4)
        if self.label is not None:
            self.mainLayout.addWidget(self.pathLabel)
            self.setLabelText(self.label)
            self.pathLabel.setFixedWidth(60)

        self.mainLayout.addWidget(self.pathLineEdit)
        self.mainLayout.addWidget(self.selectPathButton)
        self.mainLayout.addWidget(self.showInFolderButton)

    def setPath(self, path):
        """ Set the widgets path"""
        self.pathLineEdit.setText(path)

    def pickPath(self, path=None):
        """
        Pick a path from the file selector
        :param path:
        :return:
        """
        currentPath = self.getPath(absoultePath=True)

        if not path:
            fileInfo = QtCore.QFileInfo(currentPath)
            if not fileInfo.exists():
                currentPath = cmds.workspace(q=True, dir=True)

            newPath = cmds.fileDialog2(
                ds=2,
                cap=self.caption,
                ff=self.fileFilter,
                fm=self.fileMode,
                okc='Select',
                dir=currentPath
            )

            newPath = newPath[0] if newPath else None

            # next select the new path.
            self.selectPath(newPath)
            self.emitPathUpdatedSignal()

    def selectPath(self, path=None):
        """
        Select an existing path. this is smarter than set path because it will create a dailog and check if the path exists.
        :param path:
        :return:
        """
        if not path:
            self.pathLineEdit.setText('')
            return

        if path:
            # here we can check if there is a set relative path and set it properly.
            # if the newPath is not absoulte we can skip this
            if self.relativePath and os.path.isabs(path):
                path = os.path.relpath(path, self.relativePath)
            self.pathLineEdit.setText(path)
            self.pathLineEdit.setToolTip(path)

    def showInFolder(self):
        """ show the given file in the enclosing folder"""
        filePath = self.getPath()
        showInFolder.showInFolder(filePath=filePath)

    def getPath(self, absoultePath=True):
        """
        Get the path of the widget.
        if a relative path is set get the absoulte path
        """

        if self.pathLineEdit.text():
            if self.relativePath and absoultePath:
                return os.path.abspath(os.path.join(self.relativePath, self.pathLineEdit.text()))
            else:
                return self.pathLineEdit.text()

    def setRelativePath(self, relativeTo):
        """ Set the path display relative to a folder """
        self.relativePath = relativeTo

    def setLabelText(self, text):
        """ Set the label text"""
        self.pathLabel.setText(text)

    def emitPathUpdatedSignal(self):
        """Emit a signal that the path has been updated """
        self.pathUpdated.emit(self.getPath())