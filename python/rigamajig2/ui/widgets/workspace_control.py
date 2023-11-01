import sys

import maya.OpenMayaUI as omui
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import getCppPointer


class WorkspaceControl(object):

    def __init__(self, name):
        self.name = name
        self.widget = None

    def create(self, label, widget, uiScript=None):

        cmds.workspaceControl(self.name, label=label)

        if uiScript:
            cmds.workspaceControl(self.name, e=True, uiScript=uiScript)

        self.addWidgetToLayout(widget)
        self.setVisible(True)

    def restore(self, widget):
        self.addWidgetToLayout(widget)

    def addWidgetToLayout(self, widget):
        if widget:
            self.widget = widget
            self.widget.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)

            if sys.version_info.major >= 3:
                workspace_control_ptr = int(omui.MQtUtil.findControl(self.name))
                widget_ptr = int(getCppPointer(self.widget)[0])
            else:
                workspace_control_ptr = long(omui.MQtUtil.findControl(self.name))
                widget_ptr = long(getCppPointer(self.widget)[0])

            omui.MQtUtil.addWidgetToMayaLayout(widget_ptr, workspace_control_ptr)

    def exists(self):
        return cmds.workspaceControl(self.name, q=True, exists=True)

    def isVisible(self):
        return cmds.workspaceControl(self.name, q=True, visible=True)

    def setVisible(self, visible):
        if visible:
            cmds.workspaceControl(self.name, e=True, restore=True)
        else:
            cmds.workspaceControl(self.name, e=True, visible=False)

    def setLabel(self, label):
        cmds.workspaceControl(self.name, e=True, label=label)

    def isFloating(self):
        return cmds.workspaceControl(self.name, q=True, floating=True)

    def isCollapsed(self):
        return cmds.workspaceControl(self.name, q=True, collapse=True)


class DockableUI(QtWidgets.QWidget):
    WINDOW_TITLE = "DockableUI"

    ui_instance = None

    @classmethod
    def display(cls):
        if cls.ui_instance:
            cls.ui_instance.showWorkspaceControl()
        else:
            cls.ui_instance = cls()
            cls.ui_instance.showWorkspaceControl()

    @classmethod
    def get_workspace_control_name(cls):
        return "{0}WorkspaceControl".format(cls.__name__)

    @classmethod
    def getUiScript(cls):
        module_name = cls.__module__
        if module_name == "__main__":
            module_name = cls.module_name_override

        ui_script = "from {0} import {1}\n{1}.display()".format(module_name, cls.__name__)
        return ui_script

    def __init__(self):
        super(DockableUI, self).__init__()

        self.setObjectName(self.__class__.__name__)

        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(300, 250)

        self.createActions()
        self.createMenus()
        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.createWorkspaceControl()

    def createActions(self):
        pass

    def createWidgets(self):
        pass

    def createLayouts(self):
        pass

    def createConnections(self):
        pass

    def createWorkspaceControl(self):
        self.workspaceControlInstance = WorkspaceControl(self.get_workspace_control_name())
        if self.workspaceControlInstance.exists():
            self.workspaceControlInstance.restore(self)
        else:
            self.workspaceControlInstance.create(self.WINDOW_TITLE, self, uiScript=self.getUiScript())

    def showWorkspaceControl(self):
        self.workspaceControlInstance.setVisible(True)
