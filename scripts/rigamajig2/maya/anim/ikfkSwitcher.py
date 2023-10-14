"""
Ik FK switcher
"""
import sys
import time

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om2
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import rigamajig2.maya.meta as meta
from rigamajig2.maya import container
from rigamajig2.maya import decorators
from rigamajig2.maya.rig import control

logger = logger.getLogger(__name__)


VALID_IKFK_COMPONENTS = ["arm.arm", "leg.leg", "limb.limb"]

IDENTITY_MATRIX = [1, 0, 0, 0,
                   0, 1, 0, 0,
                   0, 0, 1, 0,
                   0, 0, 0, 1]


# TODO: add a check to see if Pole vector position flips and compensate it.

def getIkFkSwitchNode(controlNode):
    """
    Check if the given control is part of a component that can be switched.
    If so get the name of the ikfk node (node made by the ikfk module that contains metadata to switch)
    :param controlNode: specify a control to get the component from.
    :return:
    """

    # Validate the control. it must be a component type that supports IkFk switching
    if not control.isControl(controlNode):
        raise Exception("The node {} is not a rigamajig2 control".format(controlNode))

    # Get the container from the control
    componentContainer = container.getContainerFromNode(controlNode)

    # Check the component type to make sure it is a valid IKFK switchable component.
    componentType = cmds.getAttr("{}.type".format(componentContainer))
    if componentType not in VALID_IKFK_COMPONENTS:
        raise Exception("The component {} is not an ikfk switchable component. Valid types are: {}".
                        format(componentContainer, VALID_IKFK_COMPONENTS))

    # Now get the ikfk group. This node stores the data for the ikfk switch.
    nodesInComponent = container.getNodesInContainer(componentContainer)

    ikfkGroup = None
    for node in nodesInComponent:
        # check if the node has an message connection
        if cmds.attributeQuery("ikControls", node=node, ex=True):
            ikfkGroup = node
            break

    return ikfkGroup


def switchSelectedComponent(controlNodes=None, ik=None, fk=None):
    """
    Switch the components ikfk switch from the given control node.
    The user can specify a switch to ik, fk, or a smart switch by leaving both ik and fk at False.

    :param str list controlNodes: specify a control to get the component from. if None use the active selection.
    :param bool ik: if true the component will be switched to ik
    :param bool fk: if true the component will be switched to fk.
    """

    if controlNodes is None:
        if len(cmds.ls(sl=True)) > 0:
            controlNodes = cmds.ls(sl=True)
        else:
            raise Exception("Please select a control to switch components")

    # get the ikfk group
    for controlNode in controlNodes:
        ikfkGroup = getIkFkSwitchNode(controlNode=controlNode)

        # create an isntance of the IkFkSwithcer class. with that we can switch the component
        switcher = IkFkSwitch(ikfkGroup)
        if ik is None and fk is None:
            value = not cmds.getAttr("{}.ikfk".format(switcher.ikfkControl))
        elif ik:
            value = 0
        elif fk:
            value = 1

        # do the switch
        switcher.switch(value=value)


# Here we have duplicate code from the ikfk class.
# It is separate to keep the swithcer class completely un-reliant on rigamajig,
# allowing it to be used within script nodes in maya
# pylint:disable=duplicate-code

class IkFkSwitch(object):
    """Class to switch IKFK components"""

    def __init__(self, node):
        """initalize"""
        self.node = node
        self.gatherInfo()

    def gatherInfo(self):
        """Gather Ikfk component data """
        # By default the ikfkControl will  be the ikfk group.
        # However if the ikfkGroup has a message connection to an ikfkControl
        # then the connected control will be used.
        self.ikfkControl = self.node
        if cmds.attributeQuery("ikfkControl", node=self.node, ex=True):
            self.ikfkControl = meta.getMessageConnection("{}.{}".format(self.node, 'ikfkControl'))

        self.ikControls = meta.getMessageConnection("{}.{}".format(self.node, 'ikControls'))
        self.fkControls = meta.getMessageConnection("{}.{}".format(self.node, 'fkControls'))
        self.ikMatchList = meta.getMessageConnection("{}.{}".format(self.node, 'ikMatchList'))
        self.fkMatchList = meta.getMessageConnection("{}.{}".format(self.node, 'fkMatchList'))

    @decorators.oneUndo
    def switchRange(self, value, startFrame, endFrame):
        """
        Switch and match from ik to fk or vice versa for a range of time. This will key each frame of the switched controls

        :param value: value to switch to. 0=ik, 1=fk
        :param startFrame: frist frame of animation to switch from
        :param endFrame: last frame of the range to switch from
        """
        startTime = time.time()
        currentFrame = cmds.currentTime(q=True)

        if startFrame > endFrame:
            raise Exception("Start time cannot be after the end time. {}>{}".format(startFrame, endFrame))

        framesList = [x + 1 for x in range(startFrame, endFrame)]
        for frame in framesList:
            # go to the current frame
            cmds.currentTime(frame, edit=True)

            # switch and match from ik to fk
            switchedControls = self.switch(value)

            # key all the controls we switched
            for switchedControl in switchedControls:
                for channel in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                    cmds.setKeyframe(switchedControl, attribute=channel, time=frame)

        # set the frame back to the frame we started on
        cmds.currentTime(currentFrame, edit=True)

        elapsedTime = time.time() - startTime
        logger.info("Ik Fk Match Range complete in: {}".format(elapsedTime))

    def switch(self, value):
        """
        Switch and match from ik to fk or vice versa.
        :param value: value to switch to. 0=ik, 1=fk
        """

        if value == 0:
            self._setSourceAttr('{}.ikfk'.format(self.ikfkControl), value)
            self._setSourceAttr('{}.pvPin'.format(self.ikfkControl), 0)
            # self._setSourceAttr('{}.twist'.format(self.ikfkControl), 0)
            self._setSourceAttr('{}.stretch'.format(self.ikfkControl), 1)
            self._setSourceAttr('{}.stretchTop'.format(self.ikfkControl), 1)
            self._setSourceAttr('{}.stretchBot'.format(self.ikfkControl), 1)

            controls = self.ikMatchFk(self.fkMatchList, self.ikControls[0], self.ikControls[1], self.ikControls[2])
            logger.info("switched {}: ik -> fk".format(self.ikfkControl))
        else:
            self._setSourceAttr('{}.ikfk'.format(self.ikfkControl), value)
            controls = self.fkMatchIk(self.fkControls, self.ikMatchList)
            logger.info("switched {}: fk -> ik".format(self.ikfkControl))

        # return a list of all the controls switched
        return controls

    @staticmethod
    def fkMatchIk(fkControls, ikJoints):
        """
        Match Fk controls to Ik
        :param fkControls: list of fk controls
        :param ikJoints: list of Ik joints
        :return:
        """
        if not isinstance(fkControls, (list, tuple)):
            raise RuntimeError("{} must be a list of 4 fkControls controls".format(fkControls))
        if len(fkControls) < 3:
            raise RuntimeError("{} must be a length of 3 or more".format(fkControls))

        for fk, ikJnt in zip(fkControls[:-1], ikJoints):
            mat = cmds.xform(ikJnt, q=True, ws=True, matrix=True)
            cmds.xform(fk, ws=True, matrix=mat)

        # reset the gimble fk control
        cmds.xform(fkControls[-1], matrix=IDENTITY_MATRIX)

        return fkControls

    @staticmethod
    def ikMatchFk(fkMatchList, ik, ikGimble, pv):
        """
        Match Ik controls to Fk
        :param fkMatchList: list of FK joints
        :param ik: Ik Driver. This can be the IK controler or ikHandle.
        :param ikGimble: Ik Gimble control
        :param pv: Pole Vector Driver.
        """
        newPvPos = IkFkSwitch.getPoleVectorPos(fkMatchList, magnitude=0)
        endJntMatrix = cmds.xform(fkMatchList[2], q=True, ws=True, matrix=True)

        cmds.xform(ik, ws=True, matrix=endJntMatrix)
        cmds.xform(ikGimble, matrix=IDENTITY_MATRIX)
        cmds.xform(pv, ws=True, t=newPvPos)

        return ik, ikGimble, pv

    @staticmethod
    def getPoleVectorPos(matchList, magnitude=10):
        """
        Return the position for a pole vector
        :param matchList: list of transforms to get pole vector position from
        :param magnitude: magnitute (aka distance from mid joint to pole vector)
        :return: world space position for the pole vector
        """
        if len(matchList) != 3:
            raise RuntimeError("Joint list be have a length of 3")
        start = cmds.xform(matchList[0], q=True, ws=True, t=True)
        mid = cmds.xform(matchList[1], q=True, ws=True, t=True)
        end = cmds.xform(matchList[2], q=True, ws=True, t=True)

        startVector = om2.MVector(*start)
        midVector = om2.MVector(*mid)
        endVector = om2.MVector(*end)

        line = (endVector - startVector)
        point = (midVector - startVector)

        scaleValue = (line * point) / (line * line)
        projVector = (line * scaleValue) + startVector

        avLen = ((startVector - midVector).length() + (midVector - endVector).length())
        pvPositions = ((midVector - projVector).normal() * (magnitude + avLen)) + midVector

        return pvPositions

    @staticmethod
    def _setSourceAttr(attribute, value):
        connection = cmds.listConnections(attribute, s=True, d=False)
        if connection and len(connection) > 0:
            src = cmds.listConnections(attribute, s=True, d=False, plugs=True)[0]
            cmds.setAttr(src, value)
        else:
            cmds.setAttr(attribute, value)


class IkFkMatchRangeDialog(QtWidgets.QDialog):
    """ Dialog for the mocap import """
    WINDOW_TITLE = "Ik Fk Match Range"

    dlg_instance = None

    @classmethod
    def showDialog(cls):
        """Show the dialog"""
        if not cls.dlg_instance:
            cls.dlg_instance = IkFkMatchRangeDialog()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
            cls.dlg_instance.updateUi()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self):
        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(IkFkMatchRangeDialog, self).__init__(mayaMainWindow)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(300, 100)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """Create widgets"""
        self.matchToIkRadioButton = QtWidgets.QRadioButton("ik")
        self.matchToFkRadioButton = QtWidgets.QRadioButton("fk")

        self.matchToIkRadioButton.setChecked(True)

        self.startFrameSpinBox = QtWidgets.QSpinBox()
        self.endFrameSpinBox = QtWidgets.QSpinBox()

        # set the minimum to an incredibly small number
        self.startFrameSpinBox.setMinimum(-1e+6)
        self.endFrameSpinBox.setMinimum(-1e+6)
        self.startFrameSpinBox.setMaximum(1e+6)
        self.endFrameSpinBox.setMaximum(1e+6)

        self.doMatchButton = QtWidgets.QPushButton("Match Range")

    def createLayouts(self):
        """Create layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(4)

        # setup the radio button layout
        radioButtonLayout = QtWidgets.QHBoxLayout()
        radioButtonLayout.addWidget(QtWidgets.QLabel("Match to: "))
        radioButtonLayout.addWidget(self.matchToIkRadioButton)
        radioButtonLayout.addSpacing(10)
        radioButtonLayout.addWidget(self.matchToFkRadioButton)
        radioButtonLayout.addStretch()

        startEndFrameLayout = QtWidgets.QHBoxLayout()
        startEndFrameLayout.addWidget(QtWidgets.QLabel("Start Frame:"))
        startEndFrameLayout.addWidget(self.startFrameSpinBox)
        startEndFrameLayout.addSpacing(20)
        startEndFrameLayout.addWidget(QtWidgets.QLabel("End Frame:"))
        startEndFrameLayout.addWidget(self.endFrameSpinBox)

        # add all layouts tot he main layout
        mainLayout.addLayout(radioButtonLayout)
        mainLayout.addLayout(startEndFrameLayout)
        mainLayout.addWidget(self.doMatchButton)

    def createConnections(self):
        """Create Pyside connections"""
        self.doMatchButton.clicked.connect(self.doMatch)

    def updateUi(self):

        startFrame = cmds.playbackOptions(q=True, min=True)
        endFrame = cmds.playbackOptions(q=True, max=True)

        self.startFrameSpinBox.setValue(startFrame)
        self.endFrameSpinBox.setValue(endFrame)

    def doMatch(self):

        if len(cmds.ls(sl=True)) > 0:
            controlNode = cmds.ls(sl=True)[0]
            # add a warning that only the first node will be matched
            if len(cmds.ls(sl=True)) > 1:
                logger.warning("Only the First control in the selection will be matched.")
        else:
            raise Exception("Please select a control to switch components")

        ikfkGroup = getIkFkSwitchNode(controlNode)

        # create a switcher instance
        switcher = IkFkSwitch(ikfkGroup)

        switchValue = 0 if self.matchToIkRadioButton.isChecked() else 1

        switcher.switchRange(value=switchValue,
                             startFrame=self.startFrameSpinBox.value(),
                             endFrame=self.endFrameSpinBox.value())


if __name__ == '__main__':
    switchSelectedComponent("skeleton_rig:arm_ik_l")
    # switcher = IkFkSwitch('arm_l_ikfk')
    # switcher.switch(not cmds.getAttr('{}.ikfk'.format('arm_l_ikfk')))
