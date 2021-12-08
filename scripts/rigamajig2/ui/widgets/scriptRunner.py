import sys

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

import rigamajig2.shared.runScript as runScript


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


class ScriptRunner(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(ScriptRunner, self).__init__(*args, **kwargs)

        self.create_actions()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_actions(self):
        self.run_script_action = QtWidgets.QAction("Run Script", self)
        self.run_script_action.setIcon(QtGui.QIcon(":play_S_100.png"))
        self.run_script_action.triggered.connect(self.run_selected_scripts)

        self.show_in_folder_action = QtWidgets.QAction("Show in Folder", self)
        self.show_in_folder_action.setIcon(QtGui.QIcon(":folder-open.png"))
        self.show_in_folder_action.triggered.connect(self.show_in_folder)

        self.del_script_action = QtWidgets.QAction("Delete Script", self)
        self.del_script_action.setIcon(QtGui.QIcon(":trash.png"))
        self.del_script_action.triggered.connect(self.delete_selected_scripts)

    def create_widgets(self):
        self.script_list = QtWidgets.QListWidget()
        self.script_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.script_list.setFixedHeight(155)

        self.script_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.script_list.addAction(self.run_script_action)
        self.script_list.addAction(self.show_in_folder_action)
        self.script_list.addAction(self.del_script_action)

        self.add_script_btn = QtWidgets.QPushButton(QtGui.QIcon(":fileNew.png"), "")
        self.add_directory_btn = QtWidgets.QPushButton(QtGui.QIcon(":folder-closed.png"), "")
        self.clear_scripts_btn = QtWidgets.QPushButton(QtGui.QIcon(":hotkeyFieldClear.png"), "")
        self.create_new_script_btn = QtWidgets.QPushButton(QtGui.QIcon(":cmdWndIcon.png"), "")
        self.execute_scripts_btn = QtWidgets.QPushButton(QtGui.QIcon(":play_S_100.png"), "Execute All")

    def create_layouts(self):
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()
        btn_layout.addWidget(self.add_script_btn)
        btn_layout.addWidget(self.add_directory_btn)
        btn_layout.addWidget(self.clear_scripts_btn)
        btn_layout.addWidget(self.create_new_script_btn)
        btn_layout.addWidget(self.execute_scripts_btn)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.minimumSize()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)
        self.main_layout.addWidget(self.script_list)
        self.main_layout.addLayout(btn_layout)

    def create_connections(self):
        self.add_script_btn.clicked.connect(self.add_script_browser)
        self.add_directory_btn.clicked.connect(self.add_scripts_dir_browser)
        self.clear_scripts_btn.clicked.connect(self.clear_scripts)
        self.create_new_script_btn.clicked.connect(self.create_new_script)
        self.execute_scripts_btn.clicked.connect(self.execute_all_scripts)

    def add_item(self, name, data=None, icon=None):

        item = QtWidgets.QListWidgetItem(name)
        if data:
            item.setData(QtCore.Qt.UserRole, data)
        if icon:
            item.setIcon(icon)

        self.script_list.addItem(item)

    def add_script(self, script):
        file_info = QtCore.QFileInfo(script)
        if file_info.exists():
            iconProvider = QtWidgets.QFileIconProvider()
            icon = iconProvider.icon(file_info)
            self.add_item(file_info.fileName(), data=file_info.filePath(), icon=icon)

    def add_script_browser(self):
        file_path, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "",
                                                                           "Python (*.py) ;; Mel (*.mel)")
        print file_path
        self.add_script(file_path)

    def add_scripts_dir_browser(self):
        file_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", "")
        self.add_scripts_from_dir(file_path)

    def create_new_script(self):
        file_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, "Select File", "",
                                                                           "Python (*.py) ;; Mel (*.mel)")
        f = open(file_path, "w")
        f.write("")
        f.close()
        self.add_script(file_path)

    def add_scripts_from_dir(self, directory):
        file_info = QtCore.QFileInfo(directory)
        if not file_info.exists():
            return
        for script in runScript.find_scripts(directory):
            self.add_script(script)

    def clear_scripts(self):
        """Clear all scripts from the UI"""
        self.script_list.clear()

    def execute_all_scripts(self):
        for item in self.get_all_items():
            self.run_script(item)

    def run_selected_scripts(self):
        for item in self.get_sel_items():
            self.run_script(item)

    def toggle_selected_scripts(self):
        for item in self.get_sel_items():
            self.toggle_item(item)

    def delete_selected_scripts(self):
        for item in self.get_sel_items():
            self.delete_item(item)

    def run_script(self, item):
        script_path = item.data(QtCore.Qt.UserRole)
        runScript.run_script(script_path)

    def toggle_item(self, item):
        item.setFlags(QtCore.Qt.ItemIsDisabled)

    def delete_item(self, item):
        self.script_list.takeItem(self.script_list.row(item))

    def get_all_items(self):
        return [self.script_list.item(i) for i in range(self.script_list.count())]

    def get_sel_items(self):
        return [i for i in self.script_list.selectedItems()]

    def show_in_folder(self):
        items = self.get_sel_items()

        for item in items:
            file_path = item.data(QtCore.Qt.UserRole)

            if cmds.about(windows=True):
                if self.open_in_exporer(file_path):
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

    def open_in_exporer(self, file_path):
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
        self.scriptExecuter = ScriptRunner()

    def create_layout(self):

        self.body_wdg = QtWidgets.QWidget()

        self.body_layout = QtWidgets.QVBoxLayout(self.body_wdg)
        self.body_layout.setContentsMargins(4, 2, 4, 2)
        self.body_layout.setSpacing(3)
        self.body_layout.setAlignment(QtCore.Qt.AlignTop)

        self.body_layout.addWidget(self.scriptExecuter)
        self.scriptExecuter.add_scripts_from_dir(
            "/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/pre_script")
        self.scriptExecuter.add_scripts_from_dir("/Users/masonsmigel/Desktop/demo_scripts")

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
