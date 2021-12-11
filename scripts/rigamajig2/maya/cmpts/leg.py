"""
main component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.limb
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.container
import rigamajig2.maya.node
import rigamajig2.maya.attr
import rigamajig2.maya.skeleton

import logging

logger = logging.getLogger(__name__)


class Leg(rigamajig2.maya.cmpts.limb.Limb):
    def __init__(self, name, input=[], size=1, ikSpaces=dict(), pvSpaces=dict()):
        """
        Create a main control
        :param name:
        :param input: list of input joints. This must be a length of 4
        :type input: list
        :param: ikSpaces: dictionary of key and space for the ik control.
        :type ikSpaces: dict
        :param: pvSpaces: dictionary of key and space for the pv control.
        :type pvSpaces: dict
        """
        super(Leg, self).__init__(name, input=input, size=size, ikSpaces=ikSpaces, pvSpaces=pvSpaces)
        self.cmptSettings['toes_fkName'] = 'toes_fk'
        # noinspection PyTypeChecker
        if len(self.input) != 6:
            raise RuntimeError('Input list must have a length of 6')

    def setInitalData(self):
        self.cmptSettings['ikSpaces']['hip'] = self.cmptSettings['limbSwingName'] + '_' + self.side
        self.cmptSettings['pvSpaces']['foot'] = self.cmptSettings['limb_ikName'] + '_' + self.side

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Leg, self).initalHierachy()
        return
        # self.toes_fk = rig_control.createAtObject(self._userSettings['toes_fkName'], self.side,
        #                                           hierarchy=['trsBuffer'],
        #                                           hideAttrs=['v', 't', 's'], size=self.size, color='blue',
        #                                           parent=self.control, shape='square', shapeAim='x',
        #                                           xformObj=self.input[4])

        # TODO: build foot roll piviots

        # TODO: save piviot positions to the settings node

    def rigSetup(self):
        """Add the rig setup"""
        super(Leg, self).rigSetup()
        # cmds.parentConstraint(self.toes_fk[-1], self.input[4])
        # TODO: setup the foot roll

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        super(Leg, self).postRigSetup()

    def connect(self):
        """Create the connection"""
        super(Leg, self).connect()

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        super(Leg, self).finalize()
