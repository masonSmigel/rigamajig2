"""
Arm component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.limb.limb
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform

import logging

logger = logging.getLogger(__name__)


class Arm(rigamajig2.maya.cmpts.limb.limb.Limb):
    def __init__(self, name, input=[], size=1, ikSpaces=dict(), pvSpaces=dict(),
                 useProxyAttrs=True, useScale=True, rigParent=str()):
        """
        Arm Component (subclass of limb rig)

        :param name: component name. To add a side use a side token
        :type name: str
        :param input: list of 4 joints starting with the clavical and ending with the wrist.
        :type input: list
        :param size: default size of the controls.
        :type size: float
        :param rigParent: connect the component to a rigParent.
        :type rigParent: str
        :param: ikSpaces: dictionary of key and space for the ik control. formated as {"attrName": object}
        :type ikSpaces: dict
        :param: pvSpaces: dictionary of key and space for the pv control. formated as {"attrName": object}
        :type pvSpaces: dict
        :param useProxyAttrs: use proxy attributes instead of an ikfk control
        :type useProxyAttrs: bool
        """
        # noinspection PyTypeChecker
        if len(input) != 4:
            raise RuntimeError('Input list must have a length of 4')

        super(Arm, self).__init__(name, input=input, size=size, ikSpaces=ikSpaces, pvSpaces=pvSpaces,
                                  useProxyAttrs=useProxyAttrs, useScale=useScale, rigParent=rigParent)

    def setInitalData(self):
        self.cmptSettings['ikSpaces']['shoulder'] = self.cmptSettings['limbSwingName'] + '_' + self.side
        self.cmptSettings['pvSpaces']['hand'] = self.cmptSettings['limb_ikName'] + '_' + self.side

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Arm, self).initalHierachy()

    def rigSetup(self):
        """Add the rig setup"""
        super(Arm, self).rigSetup()

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        super(Arm, self).postRigSetup()

    def connect(self):
        """Create the connection"""
        super(Arm, self).connect()

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        super(Arm, self).finalize()

    @staticmethod
    def createInputJoints():
        """static method to create input joints"""
        pass