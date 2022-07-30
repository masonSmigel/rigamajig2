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

import rigamajig2.maya.decorators
import rigamajig2.maya.transform
import rigamajig2.maya.data.abstract_data as abstract_data
from rigamajig2.ui.widgets import pathSelector


def prepSkeleton(mocapData, namespace=None):
    """
    prepare the skeleton for mocap import
    :param mocapData: dictionary of mocap data
    :param namespace: namespace of the character
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


@rigamajig2.maya.decorators.oneUndo
def connectMocapData(mocapData, namespace=None, applyToLayer=False):
    """
    connect the mocap data to the rig
    :param mocapData: dictionary of mocap data
    :param namespace: namespace of the character
    :param applyToLayer: bake the animation onto an animaton layer
    """
    if "joints" not in mocapData.keys():
        raise RuntimeError("Mocap Data is invalid")

    controls = list()
    for srcJoint in mocapData["joints"]:
        # check if the transfer locator exists, if it does delete it then re-create
        tmpLocator = "{}_mocap_trs".format(srcJoint)
        if cmds.objExists(tmpLocator):
            cmds.delete(tmpLocator)
        tmpLocator = cmds.spaceLocator(name="{}_mocap_trs".format(srcJoint))

        # get the name of the control
        control = mocapData["joints"][srcJoint]['control']
        if namespace:
            control = "{}:{}".format(namespace, control)
        controls.append(control)

        # position the locator. it matches the position of the joint but the orientation of the control
        cmds.parent(tmpLocator, srcJoint)
        rigamajig2.maya.transform.matchTranslate(srcJoint, tmpLocator)
        rigamajig2.maya.transform.matchRotate(control, tmpLocator)

        # setup a constraint between the tmp_locator and the control
        constraint = mocapData["joints"][srcJoint]['constraint']
        if constraint == 'orient':
            cmds.orientConstraint(tmpLocator, control, mo=True)
        elif constraint == "point":
            cmds.pointConstraint(tmpLocator, control, mo=True)
        else:
            cmds.parentConstraint(tmpLocator, control, mo=True)

    # bake the control to the keys.
    minTime = cmds.playbackOptions(q=True, min=True)
    maxTime = cmds.playbackOptions(q=True, max=True)
    cmds.bakeResults(controls,
                     simulation=True,
                     time=(minTime, maxTime),
                     hi='none',
                     sampleBy=1,
                     oversamplingRate=1,
                     disableImplicitControl=True,
                     preserveOutsideKeys=True,
                     sparseAnimCurveBake=False,
                     removeBakedAttributeFromLayer=False,
                     removeBakedAnimFromLayer=True,
                     bakeOnOverrideLayer=applyToLayer,
                     shape=False)


class MocapImportDialog(QtWidgets.QDialog):
    """ Dialog for the mocap import """
    WINDOW_TITLE = "Apply Mocap Data"

    dlg_instance = None

    @classmethod
    def showDialog(cls):
        """Show the dialog"""
        if not cls.dlg_instance:
            cls.dlg_instance = MocapImportDialog()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self):
        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(MocapImportDialog, self).__init__(mayaMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(300, 250)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.updateNamespaces()

    def createWidgets(self):
        """Create widgets"""
        self.importFbxButton = QtWidgets.QPushButton("Import FBX")
        self.cleanupNamespacesButton = QtWidgets.QPushButton("Cleanup Namespaces")
        self.mocapTemplatePathselector = pathSelector.PathSelector(cap='Select a Mocap Template',
                                                                   ff="JSON Files (*.json)", fm=1)
        self.namespaceComboBox = QtWidgets.QComboBox()
        self.applyToLayerCheckbox = QtWidgets.QCheckBox("Apply to Layer")
        self.applyToLayerCheckbox.setChecked(False)
        self.prepRigButton = QtWidgets.QPushButton("Prep Rig")
        self.connectDataButton = QtWidgets.QPushButton("Connect to Rig")

    def createLayouts(self):
        """Create layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(4)

        mainLayout.addWidget(QtWidgets.QLabel("1. Import fbx data: "))
        mainLayout.addWidget(self.importFbxButton)
        mainLayout.addWidget(self.cleanupNamespacesButton)

        mainLayout.addStretch()

        mainLayout.addWidget(QtWidgets.QLabel("2. Select a mocap template file: "))
        mainLayout.addWidget(self.mocapTemplatePathselector)

        mainLayout.addStretch()
        mainLayout.addWidget(QtWidgets.QLabel("3. Select a character namespace: "))

        namespaceLayout = QtWidgets.QHBoxLayout()
        namespaceLayout.addWidget(QtWidgets.QLabel("Character Namespace: "))
        namespaceLayout.addWidget(self.namespaceComboBox)
        mainLayout.addLayout(namespaceLayout)

        mainLayout.addStretch()

        mainLayout.addWidget(QtWidgets.QLabel("3. Pose the rig to match the fbx data start position. "))
        mainLayout.addStretch()

        mainLayout.addWidget(QtWidgets.QLabel("4. Apply the mocap data to the rig: "))

        optionsLayout = QtWidgets.QHBoxLayout()
        optionsLayout.addWidget(self.applyToLayerCheckbox)
        optionsLayout.addWidget(self.prepRigButton)

        mainLayout.addLayout(optionsLayout)
        mainLayout.addWidget(self.connectDataButton)

    def createConnections(self):
        """Create Pyside connections"""
        self.importFbxButton.clicked.connect(self.importFbx)
        self.cleanupNamespacesButton.clicked.connect(self.cleanupNamespaces)
        self.connectDataButton.clicked.connect(self.connectMocapData)
        self.prepRigButton.clicked.connect(self.prepareRig)

    def updateNamespaces(self):
        """update the namespace combobox"""
        self.namespaceComboBox.clear()
        toExclude = ('UI', 'shared')
        for namespacesFound in (x for x in cmds.namespaceInfo(':', listOnlyNamespaces=True, recurse=True, fn=True) if
                        x not in toExclude):
            self.namespaceComboBox.addItem(namespacesFound)

    def importFbx(self):
        """Import the mocap Fbx"""
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
            intMin = int(cmds.playbackOptions(q=True, min=True))
            intMax = int(cmds.playbackOptions(q=True, max=True))
            cmds.playbackOptions(min=intMin, ast=intMin)
            cmds.playbackOptions(max=intMax, aet=intMax)
            cmds.currentTime(intMin)

    def connectMocapData(self):
        """
        connect the mocap data to the rig
        """

        path = self.mocapTemplatePathselector.get_path()
        namespace = self.namespaceComboBox.currentText()
        applyToLayer = self.applyToLayerCheckbox.isChecked()

        if not os.path.exists(path):
            raise RuntimeError("Mocap template is invalid or not specified")

        d = abstract_data.AbstractData()
        d.read(path)
        data = d.getData()

        prepSkeleton(namespace, data)
        connectMocapData(namespace, data, applyToLayer=applyToLayer)

    def prepareRig(self):
        """Set attributes to prepare the rig to ingest mocap data"""
        path = self.mocapTemplatePathselector.get_path()
        namespace = self.namespaceComboBox.currentText()
        
        d = abstract_data.AbstractData()
        d.read(path)
        data = d.getData()

        prepSkeleton(namespace, data)

    def cleanupNamespaces(self):
        """
        cleanup unused namespaces
        :return:
        """
        toExclude = ('UI', 'shared')
        namespaceDict = {}
        for namespacesFound in (x for x in cmds.namespaceInfo(':', listOnlyNamespaces=True, recurse=True, fn=True) if
                        x not in toExclude):
            namespaceDict.setdefault(len(namespacesFound.split(":")), []).append(namespacesFound)

        for i, lvl in enumerate(reversed(namespaceDict.keys())):
            for namespace in namespaceDict[lvl]:
                if not len(cmds.ls("{}:*".format(namespace))) > 0:
                    cmds.namespace(removeNamespace=namespace, mergeNamespaceWithParent=True)
        self.updateNamespaces()
