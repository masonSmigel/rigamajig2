"""
Collapseable Widget
"""

from PySide2 import QtGui
from PySide2 import QtWidgets

from rigamajig2.shared import common
from rigamajig2.ui.widgets import collapseableWidget

breakpointStylesheet = (f"""
                    QCheckBox {{
                        spacing: 5px;
                    }}

                    QCheckBox::indicator {{
                        width: 13px;
                        height: 13px;
                    }}

                    QCheckBox::indicator:unchecked {{
                        image: url({common.ICONS_PATH}/breakpoint_unchecked.png);
                    }}

                    QCheckBox::indicator:unchecked:hover {{
                        image: url({common.ICONS_PATH}/breakpoint_hover.png);
                    }}

                    QCheckBox::indicator:unchecked:pressed {{
                        image: url({common.ICONS_PATH}/breakpoint_checkedPress.png);
                    }}

                    QCheckBox::indicator:checked {{
                        image: url({common.ICONS_PATH}/breakpoint_checked.png);
                    }}

                    QCheckBox::indicator:checked:hover {{
                        image: url({common.ICONS_PATH}/breakpoint_checked.png);
                    }}

                    QCheckBox::indicator:checked:pressed {{
                        image: url({common.ICONS_PATH}/breakpoint_checkedPress.png);
                    }}
                    """)


class BuilderHeader(collapseableWidget.CollapsibleWidget):
    headerCheckedColor = QtGui.QColor(78, 116, 125)
    headerDefaultColor = QtWidgets.QPushButton().palette().color(QtGui.QPalette.Button)

    def __init__(self, text, parent=None, addCheckbox=True):
        super(BuilderHeader, self).__init__(text, parent, addCheckbox)

        # set the check of the header to set-checked method.
        self.headerWidget.checkbox.clicked.connect(self.setChecked)
        if self.headerWidget.hasCheckBox:
            self.headerWidget.checkbox.setStyleSheet(breakpointStylesheet)

    def setChecked(self, checked):
        super(BuilderHeader, self).setChecked(checked)

        color = self.headerCheckedColor if checked else self.headerDefaultColor
        self.setHeaderBackground(color=color)
