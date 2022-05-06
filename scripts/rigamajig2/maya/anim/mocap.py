"""
functions to connect mocap to character rig
"""
import sys, os
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import rigamajig2.maya.transform
import rigamajig2.maya.data.abstract_data as abstract_data
from rigamajig2.ui.widgets import pathSelector


def prepSkeleton(namespace=None, mocapData=dict()):
    """
    prepare the skeleton for mocap ipmort
    :param namespace: namespace of the character
    :param mocapData: dictionary of mocap data
    """
    if "prepAttrs" not in mocapData.keys():
        raise RuntimeError("Mocap Data is invalid")

    for attr in mocapData["prepAttrs"]:

        # if using a namespace add that to the attribute name
        if namespace:
            control = "{}:{}".format(namespace, attr)
        else:
            control = attr

        cmds.setAttr(control, mocapData['prepAttrs'][attr])


def connectMocapData(namespace=None, mocapData=dict(), applyToLayer=False):
    """
    connect the mocap data to the rig
    :param namespace: namespace of the character
    :param mocapData: dictionary of mocap data
    :param applyToLayer: bake the animation onto an animaton layer
    """
    if "joints" not in mocapData.keys():
        raise RuntimeError("Mocap Data is invalid")

    controls = list()
    for srcJoint in mocapData["joints"]:
        # check if the transfer locator exists, if it does delete it then re-create
        tmp_locator = "{}_mocap_trs".format(srcJoint)
        if cmds.objExists(tmp_locator):
            cmds.delete(tmp_locator)
        tmp_locator = cmds.spaceLocator(name="{}_mocap_trs".format(srcJoint))

        # get the name of the control
        control = mocapData["joints"][srcJoint]['control']
        if namespace:
            control = "{}:{}".format(namespace, control)
        controls.append(control)

        # position the locator. it matches the position of the joint but the orientation of the control
        cmds.parent(tmp_locator, srcJoint)
        rigamajig2.maya.transform.matchTranslate(srcJoint, tmp_locator)
        rigamajig2.maya.transform.matchRotate(control, tmp_locator)

        # setup a constraint between the tmp_locator and the control
        constraint = mocapData["joints"][srcJoint]['constraint']
        if constraint == 'orient':
            cmds.orientConstraint(tmp_locator, control, mo=True)
        elif constraint == "point":
            cmds.pointConstraint(tmp_locator, control, mo=True)
        else:
            cmds.parentConstraint(tmp_locator, control, mo=True)

    # bake the control to the keys.
    min_time = cmds.playbackOptions(q=True, min=True)
    max_time = cmds.playbackOptions(q=True, max=True)
    cmds.bakeResults(controls, simulation=True, time=(min_time, max_time), hi='none',
                     sampleBy=1, oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=True,
                     sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False,
                     removeBakedAnimFromLayer=True, bakeOnOverrideLayer=applyToLayer,
                     shape=False)


class MocapImportDialog(QtWidgets.QDialog):
    WINDOW_TITLE = "Apply Mocap Data"

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = MocapImportDialog()

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

        super(MocapImportDialog, self).__init__(maya_main_window)
        self.rig_env = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(300, 250)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        self.update_namespaces()

    def create_widgets(self):
        self.import_fbx_btn = QtWidgets.QPushButton("Import FBX")
        self.cleanup_namespaces_btn = QtWidgets.QPushButton("Cleanup Namespaces")
        self.mocap_template_pathSelector = pathSelector.PathSelector(cap='Select a Mocap Template',
                                                                     ff="JSON Files (*.json)", fm=1)
        self.namespace_cb = QtWidgets.QComboBox()
        self.apply_to_layer_chbx = QtWidgets.QCheckBox("Apply to Layer")
        self.apply_to_layer_chbx.setChecked(False)
        self.connect_data_btn = QtWidgets.QPushButton("Connect to Rig")

    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        main_layout.addWidget(QtWidgets.QLabel("1. Import fbx data: "))
        main_layout.addWidget(self.import_fbx_btn)
        main_layout.addWidget(self.cleanup_namespaces_btn)

        main_layout.addStretch()

        main_layout.addWidget(QtWidgets.QLabel("2. Select a mocap template file: "))
        main_layout.addWidget(self.mocap_template_pathSelector)

        main_layout.addStretch()
        main_layout.addWidget(QtWidgets.QLabel("3. Select a character namespace: "))

        namespace_layout = QtWidgets.QHBoxLayout()
        namespace_layout.addWidget(QtWidgets.QLabel("Character Namespace: "))
        namespace_layout.addWidget(self.namespace_cb)
        main_layout.addLayout(namespace_layout)

        main_layout.addStretch()

        main_layout.addWidget(QtWidgets.QLabel("3. Pose the rig to match the fbx data start position. "))
        main_layout.addStretch()

        main_layout.addWidget(QtWidgets.QLabel("4. Apply the mocap data to the rig: "))
        main_layout.addWidget(self.apply_to_layer_chbx)
        main_layout.addWidget(self.connect_data_btn)

    def create_connections(self):
        self.import_fbx_btn.clicked.connect(self.import_fbx)
        self.cleanup_namespaces_btn.clicked.connect(self.cleanup_namespaces)
        self.connect_data_btn.clicked.connect(self.connect_mocap_data)

    def update_namespaces(self):
        self.namespace_cb.clear()
        toExclude = ('UI', 'shared')
        for ns_find in (x for x in cmds.namespaceInfo(':', listOnlyNamespaces=True, recurse=True, fn=True) if
                        x not in toExclude):
            self.namespace_cb.addItem(ns_find)

    def import_fbx(self):
        path = cmds.fileDialog2(ds=2, cap="Select FBX mocap data", ff="FBX (*.fbx)", fm=1,
                                okc='Select', dir=cmds.workspace(q=True, dir=True))
        if path:
            path = path[0]
            cmds.file(path, i=True, f=True, rnn=True, importFrameRate=False, importTimeRange="combine")

            # delete some unessesary nodes
            for obj in ["System", "Unlabeled_Markers"]:
                if cmds.objExists(obj):
                    cmds.delete(obj)

            # ensure the framerate is set to intergers.
            # Sometimes importing the fbx with a mismatched framerate can cause fractional keys.
            # this is ensures the timerange works before baking the simulaiton
            int_min = int(cmds.playbackOptions(q=True, min=True))
            int_max = int(cmds.playbackOptions(q=True, max=True))
            cmds.playbackOptions(min=int_min, ast=int_min)
            cmds.playbackOptions(max=int_max, aet=int_max)
            cmds.currentTime(int_min)

    def connect_mocap_data(self):
        """
        connect the mocap data to the rig
        """

        path = self.mocap_template_pathSelector.get_path()
        namespace = self.namespace_cb.currentText()
        applyToLayer = self.apply_to_layer_chbx.isChecked()

        if not os.path.exists(path):
            raise RuntimeError("Mocap template is invalid or not specified")

        d = abstract_data.AbstractData()
        d.read(path)
        data = d.getData()

        prepSkeleton(namespace, data)
        connectMocapData(namespace, data, applyToLayer=applyToLayer)

    def cleanup_namespaces(self):
        """
        cleanup unused namespaces
        :return:
        """
        toExclude = ('UI', 'shared')
        ns_dict = {}
        for ns_find in (x for x in cmds.namespaceInfo(':', listOnlyNamespaces=True, recurse=True, fn=True) if
                        x not in toExclude):
            ns_dict.setdefault(len(ns_find.split(":")), []).append(ns_find)

        for i, lvl in enumerate(reversed(ns_dict.keys())):
            for namespace in ns_dict[lvl]:
                if not len(cmds.ls("{}:*".format(namespace))) > 0:
                    cmds.namespace(removeNamespace=namespace, mergeNamespaceWithParent=True)
        self.update_namespaces()
