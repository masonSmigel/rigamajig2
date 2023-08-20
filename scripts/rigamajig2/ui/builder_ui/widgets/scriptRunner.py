"""
Script runner widget
"""
import os.path
import sys
import subprocess
import platform
from os.path import relpath

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

import rigamajig2.shared.runScript as runScript
import rigamajig2.shared.common as common
from rigamajig2.ui import showInFolder
import rigamajig2.shared.path as rig_path

SCRIPT_FILE_FILTER = "Python (*.py) ;; Mel (*.mel)"

ITEM_HEIGHT = 18


def mayaMainWindow():
    """ Return the Maya main window widget as a Python object """
    mainWindowPointer = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(mainWindowPointer), QtWidgets.QWidget)
    else:
        return wrapInstance(long(mainWindowPointer), QtWidgets.QWidget)


RECURSION_COLORS = {0: None,
                    1: QtGui.QColor(116, 189, 224),
                    2: QtGui.QColor(204, 194, 109),
                    3: QtGui.QColor(161, 213, 172),
                    4: QtGui.QColor(85, 124, 131),
                    }


# ignore too many public methods to UI classes.
# pylint: disable = too-many-public-methods
class ScriptRunner(QtWidgets.QWidget):
    """
    Ui element to run a list of scripts in a folder
    """

    def __init__(self, rootDirectory=None, title='Scripts', *args, **kwargs):
        """
        Script runner widget class.
        The script runner conists of a list of scripts that can be modified, a scripts loaded in run in order.
        Paths relative to the root directory specified.
        :param rootDirectory: root directory of the script runner. All paths are relative to the script runner
        :param args:
        :param kwargs:
        """

        super(ScriptRunner, self).__init__(*args, **kwargs)

        self.rootDirectory = rootDirectory
        self.title = title
        self.currentScriptsList = list()

        self.createActions()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createActions(self):
        """ Create actions"""
        self.titleLabel = QtWidgets.QLabel(self.title)

        self.executeAllAction = QtWidgets.QAction("Execute All Scripts", self)
        self.executeAllAction.setIcon(QtGui.QIcon(":play_hover.png"))
        self.executeAllAction.triggered.connect(self.executeAllScripts)

        self.executeSelectedAction = QtWidgets.QAction("Run Script", self)
        self.executeSelectedAction.setIcon(QtGui.QIcon(":play_hover.png"))
        self.executeSelectedAction.triggered.connect(self.runSelectedScripts)

        self.showInFolderAction = QtWidgets.QAction("Show in Folder", self)
        self.showInFolderAction.setIcon(QtGui.QIcon(":folder-open.png"))
        self.showInFolderAction.triggered.connect(self.showInFolder)

        self.openScriptAction = QtWidgets.QAction("Open Script", self)
        self.openScriptAction.setIcon(QtGui.QIcon(":openScript.png"))
        self.openScriptAction.triggered.connect(self.openScript)

        self.addScriptAction = QtWidgets.QAction("Add Existing Script", self)
        self.addScriptAction.setIcon(QtGui.QIcon(":addCreateGeneric.png"))
        self.addScriptAction.triggered.connect(self.addScriptBrowser)

        self.newScriptAction = QtWidgets.QAction("Create New Script", self)
        self.newScriptAction.setIcon(QtGui.QIcon(":cmdWndIcon.png"))
        self.newScriptAction.triggered.connect(self.createNewScript)

        self.deleteScriptAction = QtWidgets.QAction("Remove Script", self)
        self.deleteScriptAction.setIcon(QtGui.QIcon(":trash.png"))
        self.deleteScriptAction.triggered.connect(self.deleteSelectedScripts)

    def createWidgets(self):
        """ Create Widgets """
        self.scriptList = QtWidgets.QListWidget()
        self.scriptList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.scriptList.setFixedHeight(155)
        self.scriptList.setDragDropMode(QtWidgets.QListWidget.InternalMove)
        self.scriptList.setAlternatingRowColors(True)

        self.scriptList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.scriptList.customContextMenuRequested.connect(self._createContextMenu)

    def createLayouts(self):
        """ Create layouts """
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.minimumSize()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(4)
        self.mainLayout.addWidget(self.titleLabel)
        self.mainLayout.addWidget(self.scriptList)

    def createConnections(self):
        """ Create connections"""
        pass
        # self.addScriptButton.clicked.connect(self.addScriptBrowser)
        # self.reload_scripts_btn.clicked.connect(self.reload_scripts)
        # self.createNewScriptButton.clicked.connect(self.createNewScript)
        # self.executeScriptButton.clicked.connect(self.executeAllScripts)

    def _createContextMenu(self, position):
        """Create the right click context menu"""

        menu = QtWidgets.QMenu(self.scriptList)
        menu.addAction(self.executeAllAction)
        menu.addAction(self.executeSelectedAction)
        menu.addSeparator()
        menu.addAction(self.showInFolderAction)
        menu.addAction(self.openScriptAction)
        menu.addAction(self.addScriptAction)
        menu.addAction(self.newScriptAction)
        menu.addSeparator()
        menu.addAction(self.deleteScriptAction)

        # menu .addSeparator()
        # menu .addAction(self.deleteScriptAction)

        menu.exec_(self.scriptList.mapToGlobal(position))

    def addScriptsWithRecursionData(self, scriptsDict):
        """
        add a list of script while including recusion data in the loaded script data
        """

        for recursion in scriptsDict:
            scriptsList = scriptsDict[recursion]

            for script in scriptsList:
                self._addScriptToWidget(script, data=recursion, color=RECURSION_COLORS[recursion])
                self.currentScriptsList.append(script)

    def _addScriptToWidget(self, script, data=0, color=None, top=False):
        """private method to add scripts to the list """
        fileInfo = QtCore.QFileInfo(script)
        if fileInfo.exists():
            fileName = fileInfo.fileName()
            item = QtWidgets.QListWidgetItem(fileName)
            item.setSizeHint(QtCore.QSize(0, ITEM_HEIGHT))  # set height

            # set the data
            item.setData(QtCore.Qt.UserRole, fileInfo.filePath())
            item.setToolTip(fileInfo.filePath())

            if data:
                pass
                # item.setData(QtCore.Qt.ItemDataRole, data)

            # set the icon
            if script.endswith(".py"):
                item.setIcon(QtGui.QIcon(":py_tab.png"))
            else:
                item.setIcon(QtGui.QIcon(":mel_tab.png"))

            # set the text color
            if color:
                item.setTextColor(color)

            # Add the item to the list widget
            if top:
                self.scriptList.insertItem(0, item)
            else:
                self.scriptList.addItem(item)

            return item

    def addScriptBrowser(self):
        """add script through a browswer"""
        filePath, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "", SCRIPT_FILE_FILTER)
        self._addScriptToWidget(filePath, top=True)
        if filePath:
            self.currentScriptsList.append(filePath)

    def createNewScript(self):
        """create a new script"""
        filePath, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, "Select File", "", SCRIPT_FILE_FILTER)
        if filePath:
            f = open(filePath, "w")
            f.write("")
            f.close()

            self._addScriptToWidget(filePath, top=True)
            self.currentScriptsList.append(filePath)

    def clearScript(self):
        """Clear all scripts from the UI"""
        self.scriptList.clear()
        self.currentScriptsList = list()

    def executeAllScripts(self):
        """run all script list items"""
        for item in self.getAllItems():
            self.runScript(item)

    def runSelectedScripts(self):
        """run the selected script list items"""
        for item in self.getSelectedItems():
            self.runScript(item)

    def deleteSelectedScripts(self):
        """delete the selected script list items"""
        for item in self.getSelectedItems():
            self.deleteItems(item)

    def runScript(self, item):
        """run a script list item"""
        scriptPath = item.data(QtCore.Qt.UserRole)
        runScript.runScript(scriptPath)

    def deleteItems(self, item):
        """delete a script list item"""
        self.scriptList.takeItem(self.scriptList.row(item))

    def getAllItems(self):
        """get all items in the script list"""
        return [self.scriptList.item(i) for i in range(self.scriptList.count())]

    def getSelectedItems(self):
        """get selected items in the script list"""
        return [i for i in self.scriptList.selectedItems()]

    def getCurrentScriptList(self, relativePath=None):
        """
        get a list of scripts at the current recursion level (no recursion level)
        :param relativePath:
        :return:
        """

        scriptList = list()
        for item in self.getAllItems():

            # TODO: this is a bit hacky....

            if item.textColor() == QtGui.QColor():
                scriptPath = item.data(QtCore.Qt.UserRole)

                if relativePath:
                    scriptPath = os.path.relpath(scriptPath, relativePath)

                scriptList.insert(0, scriptPath)

        return scriptList

    def showInFolder(self):
        """ Show the selected file in the enclosing folder """
        items = self.getSelectedItems()

        for item in items:
            filePath = item.data(QtCore.Qt.UserRole)
            showInFolder.showInFolder(filePath=filePath)

    def openScript(self):
        items = self.getSelectedItems()

        for item in items:
            filePath = item.data(QtCore.Qt.UserRole)
            # macOS
            if platform.system() == 'Darwin':
                subprocess.check_call(['open', filePath])
            # Windows
            elif platform.system() == 'Windows':
                os.startfile(filePath)
            # Linux
            else:
                subprocess.check_call(['xdg-open', filePath])