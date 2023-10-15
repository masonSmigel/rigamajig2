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
from PySide2 import QtWidgets

# RIGAMAJIG2
from rigamajig2.ui.builder_ui.widgets import builderHeader


class BuilderSection(QtWidgets.QWidget):
    """ Model layout for the builder UI """

    WIDGET_TITLE = "Builder Widget"

    def __init__(self):
        """ Constructor"""
        super(BuilderSection, self).__init__()

        self.builder = None
        self.rigEnvironment = None

        self.mainWidget = builderHeader.BuilderHeader(text=self.WIDGET_TITLE, addCheckbox=True)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.mainLayout.addWidget(self.mainWidget)

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
        """ Create widgets"""
        pass

    def createLayouts(self):
        """Create and setup out layouts"""
        pass

    def createConnections(self):
        """Create and setup connections"""
        pass

    def closeEvent(*args, **kwargs):
        """ setup anything to handle in the close event. """
        pass

    def isChecked(self):
        """Accessor method to get the checkbox of the header"""
        return self.mainWidget.isChecked()

    def setChecked(self, value):
        """ Accessor method to set the value of the checkbox"""
        self.mainWidget.setChecked(value)
