#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: editComponentParametersDialog.py
    author: masonsmigel
    date: 08/2022
    description:

"""
import logging
import typing
from functools import partial

import maya.cmds as cmds
import maya.mel as mel
from PySide2 import QtCore
from PySide2 import QtWidgets

from rigamajig2.maya import meta
from rigamajig2.maya.components.base import BaseComponent
from rigamajig2.ui.builder.customs import mayaListWidget, mayaDictWidget, mayaStringWidget
from rigamajig2.ui.resources import Resources
from rigamajig2.ui.widgets import mayaDialog

logger = logging.getLogger(__name__)


def getNiceName(string):
    """
    Format a camelCase string into a Nice Name
    :param string:
    :return:
    """
    result = string[0].capitalize()
    previousCharacterUppercase = False
    for char in string[1:]:
        if char.isupper() and not previousCharacterUppercase:
            result += " " + char
            previousCharacterUppercase = True
        elif char == "_" or char == "-":
            result += " "
        else:
            result += char
            previousCharacterUppercase = False
    return result


class EditComponentDialog(mayaDialog.MayaDialog):
    """Edit component dialog UI"""

    WINDOW_TITLE = "Edit Component: "

    WINDOW_SIZE = (340, 600)

    windowClosedSignal = QtCore.Signal(bool)

    def __init__(self):
        super().__init__()

        self.componentWidgets: typing.List[typing.Tuple[str, QtWidgets.QWidget]] = list()

        self.currentComponent: BaseComponent or None = None

    def __create__(self):
        """Create Widgets"""
        self.nameLineEdit = QtWidgets.QLineEdit()
        self.nameLineEdit.setReadOnly(True)
        self.typeLineEdit = QtWidgets.QLineEdit()
        self.typeLineEdit.setReadOnly(True)

        self.selectContainerButton = QtWidgets.QPushButton("Select Container")
        self.selectContainerButton.setIcon(Resources.getIcon(":container.svg"))

        self.closeButton = QtWidgets.QPushButton("Close")

    def __layout__(self):
        """Create Layouts"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.mainLayout.setSpacing(4)

        # stuff for the common widget
        commonLayout = QtWidgets.QVBoxLayout()
        commonLayout.addSpacing(4)
        commonLayout.setContentsMargins(4, 4, 4, 4)

        # setup the form layout
        commonFormLayout = QtWidgets.QFormLayout()
        commonFormLayout.addRow(QtWidgets.QLabel("Name:"), self.nameLineEdit)
        commonFormLayout.addRow(QtWidgets.QLabel("Type:"), self.typeLineEdit)
        commonFormLayout.addRow(self.selectContainerButton)
        commonLayout.addLayout(commonFormLayout)

        # setup the form layout
        self.componentFormLayout = QtWidgets.QFormLayout()

        componentGroupBox = QtWidgets.QGroupBox("Parameters")
        # componentGroupBox.setHidden(True)
        componentGroupBox.setAutoFillBackground(False)
        componentGroupBox.setFlat(True)

        # scrollable area
        bodyWidget = QtWidgets.QWidget()

        bodyWidget.setLayout(self.componentFormLayout)
        bodyScrollArea = QtWidgets.QScrollArea()
        bodyScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        bodyScrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        bodyScrollArea.setWidgetResizable(True)
        bodyScrollArea.setWidget(bodyWidget)

        # scrollable widget for scrollable are
        bodyLayout = QtWidgets.QVBoxLayout()
        bodyLayout.setContentsMargins(2, 2, 2, 2)
        bodyLayout.addWidget(bodyScrollArea)

        componentGroupBox.setLayout(bodyLayout)

        # lower buttons
        lowButtonsLayout = QtWidgets.QVBoxLayout()
        lowButtonsLayout.setSpacing(4)
        lowButtonsLayout.addWidget(self.closeButton)

        self.mainLayout.addLayout(commonLayout)
        self.mainLayout.addWidget(componentGroupBox)
        self.mainLayout.addLayout(lowButtonsLayout)

    def __connect__(self):
        """Create Connections"""
        self.selectContainerButton.clicked.connect(self._selectContainer)
        self.closeButton.clicked.connect(self.close)

    def setComponent(self, component: BaseComponent) -> None:
        """
        Set the active widget to display and edit the provided component.

        :param component: The component to set as the active one.
        :raises RuntimeError: If the provided component is not initialized or its container does not exist.
        """
        self.currentComponent = component

        # check to make sure the container exists
        if not self.currentComponent.getContainer() or not cmds.objExists(self.currentComponent.getContainer()):
            raise RuntimeError("Component is not initialized. Please initialize the component to continue.")

        self.currentComponent._updateClassParameters()

        # set the title of the window to reflect the active component
        title = self.WINDOW_TITLE + " " + self.currentComponent.name
        self.setWindowTitle(title)

        self.clearWidgets()

        self.nameLineEdit.setText(self.currentComponent.name)
        self.typeLineEdit.setText(self.currentComponent.componentType)

        for key, data in self.currentComponent._componentParameters.items():
            if key in ["name", "type"]:
                continue
            self._addParameterWidget(key, data)

    def _addParameterWidget(self, parameter: str, data: typing.Dict[str, typing.Any]):
        """
        Create and add a parameter widget to the component form layout based on the provided parameter data.

        :param parameter: The name of the parameter.
        :param data: A dictionary containing information about the parameter, including its data type.
                     Expected keys: 'dataType' - The data type of the parameter.
                                    'value' - The value of the parameter.
        :return: None
        :raises KeyError: If the specified parameter type is invalid.
        """
        if data["dataType"] == "int":
            widget = QtWidgets.QSpinBox()
            widget.setValue(data["value"])
            widget.setRange(-10_000, 10_000)
            widget.valueChanged.connect(partial(self._setParameterOnContainer, parameter=parameter, widget=widget))

        elif data["dataType"] == "float":
            widget = QtWidgets.QDoubleSpinBox()
            widget.setSingleStep(0.01)
            widget.setRange(-10_000, 10_000)
            widget.setValue(data["value"])
            widget.valueChanged.connect(partial(self._setParameterOnContainer, parameter=parameter, widget=widget))

        elif data["dataType"] == "dict":
            widget = mayaDictWidget.MayaDict()
            widget.setItems(data["value"])
            widget.itemsChanged.connect(partial(self._setParameterOnContainer, parameter=parameter, widget=widget))

        elif data["dataType"] == "list":
            widget = mayaListWidget.MayaList()
            widget.setItems(data["value"])
            widget.itemsChanged.connect(partial(self._setParameterOnContainer, parameter=parameter, widget=widget))

        elif data["dataType"] == "bool":
            widget = QtWidgets.QCheckBox()
            widget.setChecked(data["value"])
            widget.stateChanged.connect(partial(self._setParameterOnContainer, parameter=parameter, widget=widget))

        elif data["dataType"] == "string":
            widget = mayaStringWidget.MayaString()
            widget.setText(data["value"])
            widget.textChanged.connect(partial(self._setParameterOnContainer, parameter=parameter, widget=widget))
        else:
            raise KeyError(f"Parameter {parameter} has invalid data {data['dataType']} is invalid")

        label = QtWidgets.QLabel(getNiceName(getNiceName(parameter) + ":"))
        if "tooltip" in data.keys():
            label.setToolTip(data["tooltip"])
        self.componentFormLayout.addRow(label, widget)
        self.componentWidgets.append((parameter, widget))

    # noinspection PyUnusedLocal
    def _setParameterOnContainer(self, value: typing.Any, parameter: str, widget: QtWidgets.QWidget) -> None:
        """
        Set the value of a specified parameter on the corresponding container based on the data from the given widget.

        :param value: This parameter is not used within the method and is included for compatibility.
        :param parameter: The name of the component parameter to set on the container.
        :param widget: The widget associated with the parameter, from which the new data will be obtained.
                       Supported widget types include MayaDict, MayaList, MayaString, QCheckBox, QLineEdit, and QSpinBox.
        :return: None
        """

        container = self.currentComponent.getContainer()

        metaNode = meta.MetaNode(container)
        if isinstance(widget, mayaDictWidget.MayaDict):
            data = widget.getData()
        elif isinstance(widget, mayaListWidget.MayaList):
            data = widget.getData()
        elif isinstance(widget, mayaStringWidget.MayaString):
            data = widget.getText()
        elif isinstance(widget, QtWidgets.QCheckBox):
            data = widget.isChecked()
        elif isinstance(widget, QtWidgets.QLineEdit):
            data = widget.text()
        elif isinstance(widget, QtWidgets.QSpinBox):
            data = widget.value()
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            data = widget.value()
        else:
            raise ValueError(f"Unable to gather data from {parameter} ({widget}")

        metaNode.setData(attr=parameter, value=data)

    def _selectContainer(self) -> None:
        """
        Select the container from the current component
        """

        container = self.currentComponent.getContainer()
        cmds.select(container, replace=True)

        melCmd = 'showEditorExact("{}")'.format(container)
        mel.eval(melCmd, lowestPriority=True)

    def closeEvent(self, *args, **kwargs):
        """Add a close event to emit the signal whenever the window is closed"""
        self.windowClosedSignal.emit(True)

    def clearWidgets(self):
        """
        Clear all widgets from the UI
        """
        self.componentWidgets = list()
        for i in reversed(range(self.componentFormLayout.count())):
            self.componentFormLayout.itemAt(i).widget().deleteLater()
