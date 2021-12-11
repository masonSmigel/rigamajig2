import maya.cmds as cmds
import rigamajig2.maya.meta as meta
import maya.api.OpenMaya as om2
import rigamajig2.shared.common as common
import logging

logger = logging.getLogger(__name__)

IDENTITY_MATRIX = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


class IkFkSwitch(object):
    def __init__(self, node):
        """initalize"""
        self.node = node
        self.gatherInfo()

    def gatherInfo(self):

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
            cmds.setAttr('{}.ikfk'.format(self.node), value)

            cmds.setAttr('{}.pvPin'.format(self.node), 0)
            cmds.setAttr('{}.twist'.format(self.node), 0)
            cmds.setAttr('{}.stretch'.format(self.node), 1)
            cmds.setAttr('{}.stretchTop'.format(self.node), 1)
            cmds.setAttr('{}.stretchBot'.format(self.node), 1)

            self.ikMatchFk(self.fkMatchList, self.ikControls[0], self.ikControls[1], self.ikControls[2])
        else:
            cmds.setAttr('{}.ikfk'.format(self.node), value)
            self.fkMatchIk(self.fkControls, self.ikMatchList)

    @staticmethod
    def fkMatchIk(fkControls, ikJoints):
        """
        Match Fk controls to Ik
        :param fkControls: list of fk controls
        :param ikJoints: list of Ik joints
        :return:
        """
        if not isinstance(fkControls, (list, tuple)):
            raise RuntimeError("{} must be a list of 3 fkControls controls".format(fkControls))
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
        newPvPos = IkFkSwitch.getPoleVectorPos(fkMatchList)
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

        start_vector = om2.MVector(*start)
        mid_vector = om2.MVector(*mid)
        end_vector = om2.MVector(*end)

        line = (end_vector - start_vector)
        point = (mid_vector - start_vector)

        scale_value = (line * point) / (line * line)
        proj_vec = (line * scale_value) + start_vector

        avLen = ((start_vector - mid_vector).length() + (mid_vector - end_vector).length())
        pv_pos = ((mid_vector - proj_vec).normal() * (magnitude + avLen)) + mid_vector

        return pv_pos


if __name__ == '__main__':
    switcher = IkFkSwitch('arm_l_ikfk')
    switcher.switch(not cmds.getAttr('{}.ikfk'.format('arm_l_ikfk')))

