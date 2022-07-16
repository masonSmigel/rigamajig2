#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: initalize_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
import ast
import os
import re
import sys
from functools import partial

# MAYA
import maya.cmds as cmds
from shiboken2.shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
from rigamajig2.maya import meta as meta
from rigamajig2.maya.rig_builder import builder as builder
from rigamajig2.ui.widgets import pathSelector, collapseableWidget
from rigamajig2.ui.builder_ui import constants
from rigamajig2.maya.rig_builder.builder import COMPONENTS, GUIDES

ICON_PATH = os.path.abspath(os.path.join(__file__, '../../../../../icons'))


class InitializeWidget(QtWidgets.QWidget):

    def __init__(self, builder=None):
        super(InitializeWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.main_collapseable_widget = collapseableWidget.CollapsibleWidget('Initialize Rig', addCheckbox=True)
        self.cmpt_path_selector = pathSelector.PathSelector("cmpts:",
                                                            cap="Select a Component File",
                                                            ff=constants.JSON_FILTER,
                                                            fm=1)
        self.load_components_btn = QtWidgets.QPushButton("Load Cmpts")
        self.append_components_btn = QtWidgets.QPushButton("Append Cmpts")
        self.save_components_btn = QtWidgets.QPushButton("Save Cmpts")
        self.save_components_btn.setIcon(QtGui.QIcon(":save.png"))
        self.add_components_btn = QtWidgets.QPushButton("Add Components")
        self.add_components_btn.setIcon(QtGui.QIcon(":freeformOff.png"))
        self.cmpt_manager = ComponentManager()

        self.initalize_build_btn = QtWidgets.QPushButton("Initalize Components")
        self.initalize_build_btn.setFixedHeight(constants.LARGE_BTN_HEIGHT)
        self.guide_path_selector = pathSelector.PathSelector("guides:",
                                                             cap="Select a guide file",
                                                             ff=constants.JSON_FILTER,
                                                             fm=1)
        self.load_guides_btn = QtWidgets.QPushButton("Load Guides")
        self.save_guides_btn = QtWidgets.QPushButton("Save Guides")

    def createLayouts(self):
        # setup the main layout.
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.main_collapseable_widget.addWidget(self.cmpt_path_selector)

        cmpt_btn_layout = QtWidgets.QHBoxLayout()
        cmpt_btn_layout.setSpacing(4)

        guide_load_layout = QtWidgets.QHBoxLayout()
        guide_load_layout.addWidget(self.load_guides_btn)
        guide_load_layout.addWidget(self.save_guides_btn)

        cmpt_load_layout = QtWidgets.QHBoxLayout()
        cmpt_load_layout.addWidget(self.load_components_btn)
        cmpt_load_layout.addWidget(self.save_components_btn)
        cmpt_load_layout.addWidget(self.add_components_btn)
        self.main_collapseable_widget.addLayout(cmpt_load_layout)

        self.main_collapseable_widget.addWidget(self.cmpt_manager)
        self.main_collapseable_widget.addWidget(self.initalize_build_btn)
        self.main_collapseable_widget.addLayout(cmpt_btn_layout)
        self.main_collapseable_widget.addWidget(self.guide_path_selector)
        self.main_collapseable_widget.addLayout(guide_load_layout)

        # add the widget to the main layout
        self.main_layout.addWidget(self.main_collapseable_widget)

    def createConnections(self):
        self.load_guides_btn.clicked.connect(self.load_guides)
        self.save_guides_btn.clicked.connect(self.save_guides)
        self.load_components_btn.clicked.connect(self.load_components)
        self.save_components_btn.clicked.connect(self.save_components)

        self.add_components_btn.clicked.connect(self.cmpt_manager.show_add_component_dialog)
        self.initalize_build_btn.clicked.connect(self.initalize_rig)

    def setBuilder(self, builder):
        rigEnv = builder.get_rig_env()
        self.builder = builder
        self.cmpt_path_selector.set_relativeTo(rigEnv)
        self.guide_path_selector.set_relativeTo(rigEnv)
        self.cmpt_manager.set_rig_builder(self.builder)

        # reset the UI
        self.cmpt_manager.clear_cmpt_tree()

        # update data within the rig
        cmptsFile = self.builder.get_rig_data(self.builder.get_rig_file(), COMPONENTS)
        if cmptsFile:
            self.cmpt_path_selector.set_path(cmptsFile)

        guidesFile = self.builder.get_rig_data(self.builder.get_rig_file(), GUIDES)
        if guidesFile:
            self.guide_path_selector.set_path(guidesFile)

    def runWidget(self):
        self.load_components()
        self.initalize_rig()

    @property
    def isChecked(self):
        return self.main_collapseable_widget.isChecked()

    # CONNECTIONS
    def load_components(self):
        self.builder.set_cmpts(list())
        self.builder.load_components(self.cmpt_path_selector.get_abs_path())
        self.builder.load_component_settings(self.cmpt_path_selector.get_abs_path())
        self.cmpt_manager.load_list_from_builder()

    def save_components(self):
        self.builder.load_meta_settings()
        self.builder.save_components(self.cmpt_path_selector.get_abs_path())

    def load_guides(self):
        self.builder.load_guide_data(self.guide_path_selector.get_abs_path())

    def save_guides(self):
        self.builder.save_guide_data(self.guide_path_selector.get_abs_path())

    def initalize_rig(self):
        self.builder.initalize()
        self.builder.load_component_settings()
        self.cmpt_manager.load_cmpts_from_scene()


def _get_cmpt_icon(cmpt):
    """ get the component icon from the module.Class of the component"""
    return QtGui.QIcon(os.path.join(ICON_PATH, "{}.png".format(cmpt.split('.')[0])))


def get_cmpt_object(module_name=None):

    tmp_builder = builder.Builder()

    cmptDict = tmp_builder.getComponentRefDict()
    if module_name not in list(cmptDict.keys()):
        # this is a work around to account for the fact that some old .rig files use the cammel cased components
        module, cls = module_name.split('.')
        new_class = cls[0].lower() + cls[1:]
        tmp_module_name = module + "." + new_class
        if tmp_module_name in list(cmptDict.keys()):
            module_name = tmp_module_name

    module_path = cmptDict[module_name][0]
    class_name = cmptDict[module_name][1]
    module_object = __import__(module_path, globals(), locals(), ["*"], 0)
    class_ = getattr(module_object, class_name)

    return class_


class ComponentManager(QtWidgets.QWidget):
    component_icons = dict()

    def __init__(self, builder=None, *args, **kwargs):
        super(ComponentManager, self).__init__(*args, **kwargs)

        self.builder = builder

        self.scriptjob_number = -1

        self.create_actions()
        self.create_widgets()
        self.create_layouts()
        self.setFixedHeight(280)

    def create_actions(self):
        self.select_container_action = QtWidgets.QAction("Select Container", self)
        self.select_container_action.setIcon(QtGui.QIcon(":out_container.png"))
        self.select_container_action.triggered.connect(self.select_container)

        self.editComponentSettings_action = QtWidgets.QAction("Edit Component Parameters")
        self.editComponentSettings_action.setIcon(QtGui.QIcon(":toolSettings.png"))

        self.createSymetricalComponent = QtWidgets.QAction("Create Mirroed Component")
        self.createSymetricalComponent.setIcon(QtGui.QIcon(":kinMirrorJoint_S.png"))

        self.mirrorComponentSettings_action = QtWidgets.QAction("Mirror Component Parameters")
        self.mirrorComponentSettings_action.setIcon(QtGui.QIcon(":QR_mirrorGuidesRightToLeft.png"))

        self.reload_cmpt_action = QtWidgets.QAction("Reload Cmpts from Scene", self)
        self.reload_cmpt_action.setIcon(QtGui.QIcon(":refresh.png"))
        self.reload_cmpt_action.triggered.connect(self.load_cmpts_from_scene)

        self.del_cmpt_action = QtWidgets.QAction("Delete Cmpt", self)
        self.del_cmpt_action.setIcon(QtGui.QIcon(":trash.png"))
        self.del_cmpt_action.triggered.connect(self.delete_cmpt)

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
        self.component_tree.addAction(self.editComponentSettings_action)
        self.component_tree.addAction(self.createSymetricalComponent)
        self.component_tree.addAction(self.mirrorComponentSettings_action)
        self.component_tree.addAction(self.reload_cmpt_action)
        self.component_tree.addAction(self.del_cmpt_action)

    def create_layouts(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.minimumSize()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)
        self.main_layout.addWidget(self.component_tree)

    def set_scriptjob_enabled(self, enabled):
        if enabled and self.scriptjob_number < 0:
            self.scriptjob_number = cmds.scriptJob(event=["NewSceneOpened", partial(self.load_cmpts_from_scene)],
                                                   protected=True)
        elif not enabled and self.scriptjob_number > 0:
            cmds.scriptJob(kill=self.scriptjob_number, f=True)
            self.scriptjob_number = -1

    def add_component(self, name, cmpt_type, build_step='unbuilt', container=None):
        rowcount = self.component_tree.topLevelItemCount()
        item = QtWidgets.QTreeWidgetItem(rowcount)
        item.setSizeHint(0, QtCore.QSize(item.sizeHint(0).width(), 24))  # set height

        # set the nessesary text.
        item.setText(0, name)
        item.setFont(0, QtGui.QFont())

        item.setText(1, cmpt_type)
        item.setText(2, build_step)

        item.setTextColor(1, QtGui.QColor(156, 156, 156))
        item.setTextColor(2, QtGui.QColor(156, 156, 156))

        # set the icon
        cmpt_icon = _get_cmpt_icon(cmpt_type)
        item.setIcon(0, cmpt_icon)

        # set the data
        if container:
            item.setData(QtCore.Qt.UserRole, 0, container)

        self.component_tree.addTopLevelItem(item)
        return item

    def create_component(self,name, cmpt_type, input, rigParent):
        cmpt_obj = get_cmpt_object(cmpt_type)
        cmpt = cmpt_obj(name=name, input=ast.literal_eval(str(input)), rigParent=rigParent)

        self.add_component(name=name, cmpt_type=cmpt_type, build_step='unbuilt', container=None)
        self.builder.append_cmpts([cmpt])

    def load_cmpts_from_scene(self):
        """ load exisiting components from the scene"""
        self.clear_cmpt_tree()
        components = meta.getTagged('component')

        for component in components:
            name = cmds.getAttr("{}.name".format(component))
            cmpt_type = cmds.getAttr("{}.type".format(component))
            build_step_str = cmds.attributeQuery("build_step", n=component, le=True)[0].split(":")
            build_step = build_step_str[cmds.getAttr("{}.build_step".format(component))]
            isSubComponent = meta.hasTag(component, "subComponent")
            if not isSubComponent:
                self.add_component(name=name, cmpt_type=cmpt_type, build_step=build_step, container=component)

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

    def get_selected_item(self):
        """ get the selected items in the component tree"""
        return [item for item in self.component_tree.selectedItems()]

    def get_component_obj(self, item=None):
        if not item:
            item = self.get_selected_item()[0]

        item_dict = self.get_data_from_item(item)
        cmpt = self.builder.find_cmpt(item_dict['name'], item_dict['type'])
        return cmpt

    def select_container(self):
        """ select the container node of the selected components """
        cmds.select(cl=True)
        for item in self.get_selected_item():
            item_dict = self.get_data_from_item(item)
            cmds.select(item_dict['container'], add=True)

    def edit_cmpt(self):
        items = self.get_selected_item()
        for item in items:
            item_dict = self.get_data_from_item(item)
            self.builder.edit_single_cmpt(item_dict['name'], item_dict['type'])

            self.update_cmpt_from_scene(item)

    def build_cmpt(self):
        items = self.get_selected_item()
        for item in items:
            item_dict = self.get_data_from_item(item)

            self.builder.build_single_cmpt(item_dict['name'], item_dict['type'])
            self.update_cmpt_from_scene(item)

    def delete_cmpt(self):
        items = self.get_selected_item()
        for item in items:
            component = self.get_component_obj(item)
            if component.getContainer():
                component.deleteSetup()
            self.component_tree.takeTopLevelItem(self.component_tree.indexOfTopLevelItem(item))

            self.builder.cmpt_list.remove(component)

    def clear_cmpt_tree(self):
        """ clear the component tree"""
        try:
            if self.component_tree.topLevelItemCount() > 0:
                self.component_tree.clear()
        except RuntimeError:
            pass

    def set_rig_builder(self, builder):
        self.builder = builder

    def load_list_from_builder(self):
        self.clear_cmpt_tree()

        if not self.builder:
            raise RuntimeError("No valid rig builder found")
        for cmpt in self.builder.get_cmpt_list():
            name = cmpt.name
            cmpt_type = cmpt.cmpt_type
            build_step_str = ['unbuilt', 'initalize', 'build', 'connect', 'finalize', 'optimize']
            build_step = build_step_str[cmpt.getStep()]

            self.add_component(name=name, cmpt_type=cmpt_type, build_step=build_step)

    def update_cmpt_from_scene(self, item):
        item_dict = self.get_data_from_item(item)
        container = item_dict['container']

        name = cmds.getAttr("{}.name".format(container))
        cmpt = cmds.getAttr("{}.type".format(container))
        build_step_str = cmds.attributeQuery("build_step", n=container, le=True)[0].split(":")
        build_step = build_step_str[cmds.getAttr("{}.build_step".format(container))]

        item.setText(0, name)
        item.setText(1, cmpt)
        item.setText(2, build_step)

    def showEvent(self, e):
        super(ComponentManager, self).showEvent(e)
        self.set_scriptjob_enabled(True)

    def show_add_component_dialog(self):

        dialog = CreateCmptDialog()
        dialog.new_cmpt_created.connect(self.create_component)
        dialog.show()


class CreateCmptDialog(QtWidgets.QDialog):
    WINDOW_TITLE = "Create New Component"

    new_cmpt_created = QtCore.Signal(str, str, str, str)

    def __init__(self, cmpt_manager=None):
        if sys.version_info.major < 3:
            maya_main_window = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            maya_main_window = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(CreateCmptDialog, self).__init__(maya_main_window)
        self.cmpt_manager = cmpt_manager

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(400, 180)
        self.resize(400, 340)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

        self.update_comboBox()

    def create_widgets(self):
        self.name_le = QtWidgets.QLineEdit()

        self.component_type_cb = QtWidgets.QComboBox()
        self.component_type_cb.setMinimumHeight(30)
        self.component_type_cb.setMaxVisibleItems(15)
        self.component_type_cb.setMaxVisibleItems(30)

        self.create_input_joints_btn = QtWidgets.QPushButton("Create Input Joints")

        self.input_le = QtWidgets.QLineEdit()
        self.input_le.setPlaceholderText("[]")
        self.load_sel_as_input_btn = QtWidgets.QPushButton("<")
        self.load_sel_as_input_btn.setMaximumWidth(30)

        self.rigParent_le = QtWidgets.QLineEdit()
        self.rigParent_le.setPlaceholderText("None")
        self.load_sel_as_rigParent_btn = QtWidgets.QPushButton("<")
        self.load_sel_as_rigParent_btn.setMaximumWidth(30)

        self.discription_te = QtWidgets.QTextEdit()
        self.discription_te.setReadOnly(True)

        self.apply_close_btn = QtWidgets.QPushButton("Create and Close")
        self.apply_btn = QtWidgets.QPushButton("Create")
        self.close_btn = QtWidgets.QPushButton("Cancel")

    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("name:"))
        name_layout.addWidget(self.name_le)
        name_layout.addSpacing(30)
        name_layout.addWidget(QtWidgets.QLabel("type:"))
        name_layout.addWidget(self.component_type_cb)

        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.input_le)
        input_layout.addWidget(self.load_sel_as_input_btn)

        rigParent_layout = QtWidgets.QHBoxLayout()
        rigParent_layout.addWidget(self.rigParent_le)
        rigParent_layout.addWidget(self.load_sel_as_rigParent_btn)

        widget_layout = QtWidgets.QFormLayout()
        widget_layout.addRow(QtWidgets.QLabel("input:"), input_layout)
        widget_layout.addRow(QtWidgets.QLabel("rigParent:"), rigParent_layout)

        apply_btn_layout = QtWidgets.QHBoxLayout()
        apply_btn_layout.addWidget(self.apply_close_btn)
        apply_btn_layout.addWidget(self.apply_btn)
        apply_btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(name_layout)
        main_layout.addWidget(self.create_input_joints_btn)
        main_layout.addLayout(widget_layout)
        main_layout.addSpacing(5)
        main_layout.addWidget(self.discription_te)
        main_layout.addLayout(apply_btn_layout)

    def create_connections(self):
        self.load_sel_as_input_btn.clicked.connect(self.add_selection_as_input)
        self.load_sel_as_rigParent_btn.clicked.connect(self.add_selection_as_rigParent)
        self.component_type_cb.currentIndexChanged.connect(self.update_discription)
        self.close_btn.clicked.connect(self.close)
        self.apply_btn.clicked.connect(self.apply)
        self.apply_close_btn.clicked.connect(self.apply_and_close)

    def update_comboBox(self):
        self.component_type_cb.clear()
        tmp_builder = builder.Builder()
        for i, component in enumerate(sorted(tmp_builder.getComponents())):
            self.component_type_cb.addItem(component)
            self.component_type_cb.setItemIcon(i, QtGui.QIcon(_get_cmpt_icon(component)))

    def update_discription(self):
        self.discription_te.clear()

        cmpt_type = self.component_type_cb.currentText()

        cmpt_object  = get_cmpt_object(cmpt_type)

        docstring = cmpt_object.__init__.__doc__
        if docstring:
            docstring = re.sub(" {4}", "", docstring.strip())

        self.discription_te.setText(docstring)

    def add_selection_as_input(self):
        self.input_le.clear()
        sel = cmds.ls(sl=True)
        sel_list = list()
        for s in sel:
            sel_list.append(str(s))

        self.input_le.setText(str(sel_list))

    def add_selection_as_rigParent(self):
        self.rigParent_le.clear()
        sel = cmds.ls(sl=True)

        if len(sel) > 0:
            self.rigParent_le.setText(str(sel[0]))

    def apply(self):
        cmpt_type = self.component_type_cb.currentText()

        name = self.name_le.text() or None
        input = self.input_le.text() or []
        rigParent = self.rigParent_le.text() or None

        # emit the data to the create_component mehtod of the component manager.
        # if the type is main then we can ignore the input.
        if name and cmpt_type == 'main.Main':
            self.new_cmpt_created.emit(name, cmpt_type, "[]", rigParent)
        elif name and input:
            self.new_cmpt_created.emit(name, cmpt_type, input, rigParent)

    def apply_and_close(self):
        self.apply()
        self.close()