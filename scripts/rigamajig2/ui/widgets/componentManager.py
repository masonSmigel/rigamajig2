""" Component Manager"""
import sys
import os

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

import rigamajig2.maya.meta as meta
import rigamajig2.maya.rig.builder as builder

ICON_PATH = os.path.abspath(os.path.join(__file__, '../../../../../icons'))


class ComponentManager(QtWidgets.QWidget):
    component_icons = dict()

    def __init__(self, *args, **kwargs):
        super(ComponentManager, self).__init__(*args, **kwargs)

        self.create_actions()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        self.setFixedHeight(280)

    def create_actions(self):
        self.select_container_action = QtWidgets.QAction("Select Container", self)
        self.select_container_action.setIcon(QtGui.QIcon(":play_S_100.png"))
        self.select_container_action.triggered.connect(self.select_container)

    def create_widgets(self):
        self.component_tree = QtWidgets.QTreeWidget()
        self.component_tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.component_tree.setHeaderHidden(True)
        self.component_tree.setAlternatingRowColors(True)

        self.component_tree.setIndentation(5)
        self.component_tree.setColumnCount(3)
        self.component_tree.setUniformRowHeights(True)
        self.component_tree.setColumnWidth(0, 130)
        self.component_tree.setColumnWidth(1, 120)
        self.component_tree.setColumnWidth(2, 60)

        self.component_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.component_tree.addAction(self.select_container_action)

        self.reload_cmpt_btn = QtWidgets.QPushButton(QtGui.QIcon(":refresh.png"), "")
        self.remove_cmpt_btn = QtWidgets.QPushButton(QtGui.QIcon(":hotkeyFieldClear.png"), "")
        self.cmpt_settings_btn = QtWidgets.QPushButton(QtGui.QIcon(":QR_settings.png"), "")
        self.add_cmpt_btn = QtWidgets.QPushButton(QtGui.QIcon(":freeformOff.png"), "Add Component")

    def create_layouts(self):
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()
        btn_layout.addWidget(self.reload_cmpt_btn)
        btn_layout.addWidget(self.remove_cmpt_btn)
        btn_layout.addWidget(self.cmpt_settings_btn)
        btn_layout.addWidget(self.add_cmpt_btn)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.minimumSize()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)
        self.main_layout.addWidget(self.component_tree)
        self.main_layout.addLayout(btn_layout)

    def create_connections(self):
        self.reload_cmpt_btn.clicked.connect(self.load_cmpts_from_scene)
        self.add_cmpt_btn.clicked.connect(self.create_context_menu)

    def add_component(self, name, cmpt, build_step='unbuilt', container=None):
        rowcount = self.component_tree.topLevelItemCount()
        item = QtWidgets.QTreeWidgetItem(rowcount)
        item.setSizeHint(0, QtCore.QSize(item.sizeHint(0).width(), 24))  # set height

        # set the nessesary text.
        item.setText(0, name)
        item.setFont(0, QtGui.QFont())

        item.setText(1, cmpt)
        item.setText(2, build_step)

        item.setTextColor(1, QtGui.QColor(156, 156, 156))
        item.setTextColor(2, QtGui.QColor(156, 156, 156))

        # set the icon
        cmpt_icon = self.__get_cmpt_icon(cmpt)
        item.setIcon(0, cmpt_icon)

        # set the data
        if container:
            item.setData(QtCore.Qt.UserRole, 0, container)

        self.component_tree.addTopLevelItem(item)
        return item

    def load_cmpts_from_scene(self):
        """ load exisiting components from the scene"""
        self.clear_cmpt_tree()
        components = meta.getTagged('component')

        for component in components:
            name = cmds.getAttr("{}.name".format(component))
            cmpt = cmds.getAttr("{}.type".format(component))
            build_step_str = cmds.attributeQuery("build_step", n=component, le=True)[0].split(":")
            build_step = build_step_str[cmds.getAttr("{}.build_step".format(component))]
            isSubComponent = meta.hasTag(component, "subComponent")
            if not isSubComponent:
                self.add_component(name=name, cmpt=cmpt, build_step=build_step, container=component)

    def get_data_from_item(self, item):
        """
        return a dictionary of data for the item
        :return:
        """
        item_data = dict()
        item_data['name'] = item.text(0)
        item_data['type'] = item.text(1)
        item_data['step'] = item.text(2)
        item_data['container'] = item.data(QtCore.Qt.UserRole, 0)

        return item_data

    def get_all_cmpts(self):
        """ get all components in the component tree"""
        return [self.component_tree.topLevelItem(i) for i in range(self.component_tree.topLevelItemCount())]

    def get_selected_cmpts(self):
        """ get the selected items in the component tree"""
        return [item for item in self.component_tree.selectedItems()]

    def select_container(self):
        """ select the container node of the selected components """
        cmds.select(cl=True)
        for item in self.get_selected_cmpts():
            item_dict = self.get_data_from_item(item)
            cmds.select(item_dict['container'], add=True)

    def initalize_all_cmpts(self):
        """ initalize all components """
        print([item.data(QtCore.Qt.UserRole, 0) for item in self.get_all_cmpts()])

    def clear_cmpt_tree(self):
        """ clear the component tree"""
        self.component_tree.clear()

    def __get_cmpt_icon(self, cmpt):
        """ get the component icon from the module.Class of the component"""
        return QtGui.QIcon(os.path.join(ICON_PATH, "{}.png".format(cmpt.split('.')[0])))

    def create_context_menu(self):
        self.add_components_menu = QtWidgets.QMenu()
        tmp_builder = builder.Builder()
        for component in sorted(tmp_builder.getComponents()):
            action = QtWidgets.QAction(component, self)
            action.setIcon(QtGui.QIcon(self.__get_cmpt_icon(component)))
            self.add_components_menu.addAction(action)

        self.add_components_menu.exec_(QtGui.QCursor.pos())
