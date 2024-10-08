#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: builderSection.py
    author: masonsmigel
    date: 10/2023
    description:

"""
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from rigamajig2.ui.resources import Resources
from rigamajig2.ui.widgets import collapseableWidget

breakpointStylesheet = f"""
                    QCheckBox {{
                        spacing: 5px;
                    }}

                    QCheckBox::indicator {{
                        width: 13px;
                        height: 13px;
                    }}

                    QCheckBox::indicator:unchecked {{
                        image: url(:breakpointUnchecked.png);
                    }}

                    QCheckBox::indicator:unchecked:hover {{
                        image: url(:breakpointHover.png);
                    }}

                    QCheckBox::indicator:unchecked:pressed {{
                        image: url(:breakpointCheckedPress.png);
                    }}

                    QCheckBox::indicator:checked {{
                        image: url(:breakpointChecked.png);
                    }}

                    QCheckBox::indicator:checked:hover {{
                        image: url(:breakpointChecked.png);
                    }}

                    QCheckBox::indicator:checked:pressed {{
                        image: url(:breakpointCheckedPress.png);
                    }}
                    """


class BuilderHeader(collapseableWidget.CollapsibleWidget):
    headerCheckedColor = QtGui.QColor(78, 116, 125)

    def __init__(self, text, parent=None, addCheckbox=True):
        super(BuilderHeader, self).__init__(text, parent, addCheckbox)

        # set the check of the header to set-checked method.
        self.headerWidget.checkbox.clicked.connect(self.setChecked)
        if self.headerWidget.hasCheckBox:
            self.headerWidget.checkbox.setStyleSheet(breakpointStylesheet)

        self.runWidgetButton = QtWidgets.QPushButton()
        self.runWidgetButton.setIcon(Resources.getIcon(":icons/general/skip-forward"))
        self.runWidgetButton.setFlat(True)
        self.runWidgetButton.setFixedSize(QtCore.QSize(16, 16))

        self.headerWidget.mainLayout.addWidget(self.runWidgetButton)

    def setChecked(self, checked):
        super(BuilderHeader, self).setChecked(checked)

        color = self.headerCheckedColor if checked else self.palette().color(QtGui.QPalette.Button)
        self.setHeaderBackground(color=color)


class BuilderSection(QtWidgets.QWidget):
    """Model layout for the builder UI"""

    WIDGET_TITLE = "Builder Widget"

    def __init__(self, builderDialog):
        """Constructor"""
        super(BuilderSection, self).__init__(parent=builderDialog)

        self.builderDialog = builderDialog

        self.builder = None
        self.rigEnvironment = None

        self.mainWidget = BuilderHeader(text=self.WIDGET_TITLE, addCheckbox=True, parent=self)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.mainLayout.addWidget(self.mainWidget)

        self.mainWidget.runWidgetButton.clicked.connect(self._runWidget)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    @QtCore.Slot()
    def _runWidget(self):
        """
        Run any functions you that should be run to build the widget.
        Reimplement in subclass
        """
        raise NotImplementedError(f"Not implemented in {self.__class__}")

    @QtCore.Slot()
    def _setBuilder(self, builder):
        """Set the builder for the widget."""
        self.builder = builder

    def createWidgets(self):
        """Create widgets"""
        pass

    def createLayouts(self):
        """Create and setup out layouts"""
        pass

    def createConnections(self):
        """Create and setup connections"""
        pass

    def closeEvent(*args, **kwargs):
        """setup anything to handle in the close event."""
        pass

    def isChecked(self):
        """Accessor method to get the checkbox of the header"""
        return self.mainWidget.isChecked()

    def setChecked(self, value):
        """Accessor method to set the value of the checkbox"""
        self.mainWidget.setChecked(value)

    def postRigFileModifiedEvent(self):
        """Post the builder modified event"""
        if self.builderDialog.rigFileIsModified:
            return None
        self.builderDialog.rigFileModifiedSignal.emit()
