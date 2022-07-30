"""
Ik FK switcher
"""
import maya.cmds as cmds
import rigamajig2.maya.meta as meta
import maya.api.OpenMaya as om2
import logging
from rigamajig2.maya.rig import control
from rigamajig2.maya import container

logger = logging.getLogger(__name__)

VALID_IKFK_COMPONENTS = ["arm.arm", "leg.leg", "limb.limb"]


def switchSelectedComponent(controlNode=None, ik=None, fk=None):
    """
    Switch the components ikfk switch from the given control node.
    The user can specify a switch to ik, fk, or a smart switch by leaving both ik and fk at False.

    :param str list controlNode: spedify a control to get the component from. if None use the active selection.
    :param bool ik: if true the component will be switched to ik
    :param bool fk: if true the component will be switched to fk.
    """

    if controlNode is None:
        if len(cmds.ls(sl=True)) > 0:
            controlNode = cmds.ls(sl=True)[0]
        else:
            raise Exception("Please select a control to switch components")

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
        if cmds.attributeQuery("ikControls", node = node, ex=True):
            ikfkGroup = node
            break

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

    def switch(self, value):
        """
        Switch to ik for fk setup
        :param value: value to switch to. 0=ik, 1=fk
        """

        if value == 0:
            self._setSourceAttr('{}.ikfk'.format(self.ikfkControl), value)
            self._setSourceAttr('{}.pvPin'.format(self.ikfkControl), 0)
            # self._setSourceAttr('{}.twist'.format(self.ikfkControl), 0)
            self._setSourceAttr('{}.stretch'.format(self.ikfkControl), 1)
            self._setSourceAttr('{}.stretchTop'.format(self.ikfkControl), 1)
            self._setSourceAttr('{}.stretchBot'.format(self.ikfkControl), 1)

            self.ikMatchFk(self.fkMatchList, self.ikControls[0], self.ikControls[1], self.ikControls[2])
            logger.info("switched {}: ik -> fk".format(self.ikfkControl))
        else:
            self._setSourceAttr('{}.ikfk'.format(self.ikfkControl), value)
            self.fkMatchIk(self.fkControls, self.ikMatchList)
            logger.info("switched {}: fk -> ik".format(self.ikfkControl))

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


if __name__ == '__main__':
    switchSelectedComponent("skeleton_rig:arm_ik_l")
    # switcher = IkFkSwitch('arm_l_ikfk')
    # switcher.switch(not cmds.getAttr('{}.ikfk'.format('arm_l_ikfk')))
