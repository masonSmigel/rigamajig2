"""
This file contains the UI for the main rig builder
"""
import sys

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

from rigamajig2.ui.widgets import pathSelector


class RigamajigBuilderUi(QtWidgets.QDialog):
    WINDOW_TITLE = "Rigamajig2 Builder"

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = RigamajigBuilderUi()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self):
        if sys.version_info.major < 3:
            maya_main_window = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            maya_main_window = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(RigamajigBuilderUi, self).__init__(maya_main_window)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(375, 825)

        self.create_actions()
        self.create_menus()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_actions(self):
        # FILE
        self.load_rig_file_action = QtWidgets.QAction("Load Rig File", self)
        self.load_rig_file_action.triggered.connect(self.load_rig_file)

        self.save_rig_file_action = QtWidgets.QAction("Save Rig File", self)
        self.save_rig_file_action.triggered.connect(self.save_rig_file)

        # UTILS
        # ...

        # HELP
        self.show_documentation_action = QtWidgets.QAction("Documentation", self)
        self.show_documentation_action.triggered.connect(self.show_documentation)

        self.show_about_action = QtWidgets.QAction("About", self)
        self.show_about_action.triggered.connect(self.show_about)

    def create_menus(self):
        """create menu actions"""
        self.main_menu = QtWidgets.QMenuBar()

        file_menu = self.main_menu.addMenu("File")
        file_menu.addAction(self.load_rig_file_action)
        file_menu.addAction(self.save_rig_file_action)

        utils_menu = self.main_menu.addMenu("Utils")
        tools_menu = self.main_menu.addMenu("Tools")

        help_menu = self.main_menu.addMenu("Help")
        help_menu.addAction(self.show_documentation_action)
        help_menu.addAction(self.show_about_action)

    def create_widgets(self):
        self.rig_path_selector = pathSelector.PathSelector(cap='Select a Rig File', ff="Rig Files (*.rig)", fm=1)

        self.create_rig_env_btn = QtWidgets.QPushButton("Create rig env")
        self.create_rig_env_btn.setToolTip("Create a new rig enviornment from scratch")

        self.clone_rig_env_btn = QtWidgets.QPushButton("Clone rig env")
        self.create_rig_env_btn.setToolTip("Create a new rig enviornment from an existing enviornment")

    def create_layouts(self):
        rig_env_btn_layout = QtWidgets.QHBoxLayout()
        rig_env_btn_layout.addWidget(self.create_rig_env_btn)
        rig_env_btn_layout.addWidget(self.clone_rig_env_btn)

        rig_env_layout = QtWidgets.QVBoxLayout()
        rig_env_layout.addWidget(self.rig_path_selector)
        rig_env_layout.addLayout(rig_env_btn_layout)

        rig_env_grp = QtWidgets.QGroupBox('Rig Enviornment')
        rig_env_grp.setLayout(rig_env_layout)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        main_layout.setMenuBar(self.main_menu)
        main_layout.addWidget(rig_env_grp)
        main_layout.addStretch()

    def create_connections(self):
        self.create_rig_env_btn.clicked.connect(self.create_rig_env)
        self.clone_rig_env_btn.clicked.connect(self.clone_rig_env)
        # self.rig_file_path_select_btn.clicked.connect(self.select_rig_file)

    # Connections
    def load_rig_file(self):
        pass

    def save_rig_file(self):
        pass

    def show_documentation(self):
        pass

    def show_about(self):
        pass

    def set_rig_file(self, path=None):
        self.rig_path_selector.select_path(path=path)

    def load_data_from_rig_file(self):
        pass

    def create_rig_env(self):
        print "TODO : create a rig environment"

    def clone_rig_env(self):
        print "TODO : clone a rig environment"


if __name__ == '__main__':
    try:
        rigamajig_builder_dialog.close()
        rigamajig_builder_dialog.deleteLater()
    except:
        pass

    rigamajig_builder_dialog = RigamajigBuilderUi()
    rigamajig_builder_dialog.show()

    rigamajig_builder_dialog.set_rig_file(
        path='/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/biped.rig')
