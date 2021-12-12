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

    def createBuildGuides(self):
        """ create build guides """
        self.guides = cmds.createNode("transform", name='{}_guide'.format(self.name))
        self._heel_piv = cmds.spaceLocator(name="{}_heel".format(self.name))[0]
        self._inn_piv = cmds.spaceLocator(name="{}_inn".format(self.name))[0]
        self._out_piv = cmds.spaceLocator(name="{}_out".format(self.name))[0]

        cmds.parent(self._heel_piv, self._inn_piv, self._out_piv, self.guides)

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Leg, self).initalHierachy()
        return
        # self.toes_fk = rig_control.createAtObject(self._userSettings['toes_fkName'], self.side,
        #                                           hierarchy=['trsBuffer'],
        #                                           hideAttrs=['v', 't', 's'], size=self.size, color='blue',
        #                                           parent=self.control, shape='square', shapeAim='x',
        #                                           xformObj=self.input[4])

        # TODO: create controls for the ik piviots

    def rigSetup(self):
        """Add the rig setup"""
        super(Leg, self).rigSetup()
        # cmds.parentConstraint(self.toes_fk[-1], self.input[4])

        self.footikfk = ikfk.IkFkFoot(jointList=self.input[3:], heelPivot=self._heel_piv, innPivot=self._inn_piv, outPivot=self._out_piv)
        self.footikfk.setGroup(self.ikfk.getGroup())
        self.footikfk.create()
        ikfk.IkFkFoot.createFootRoll(self.footikfk.getPivotList(), self.footikfk.getGroup())

        cmds.parent(self._ikEndTgt, self.footikfk.getPivotList()[-2])
        cmds.parent(self.footikfk.getPivotList()[0], self.limbGimble_ik[-1])
        cmds.delete(cmds.listRelatives(self._ikEndTgt, ad=True, type='pointConstraint'))

        # Delete the proxy guides:
        cmds.delete(self.guides)

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        blendedJointlist = self.ikfk.getBlendJointList() + self.footikfk.getBlendJointList()[1:]
        print blendedJointlist
        rigamajig2.maya.skeleton.connectChains(blendedJointlist, self.input[1:])
        ikfk.IkFkBase.connnectIkFkVisibility(self.ikfk.getGroup(), 'ikfk', ikList=self.ikControls,
                                             fkList=self.fkControls)

        # connect the base to the main bind chain
        cmds.parentConstraint(self.limbBase[-1], self.input[0])
        rigamajig2.maya.attr.lock(self.input[0], rigamajig2.maya.attr.TRANSFORMS + ['v'])

    def connect(self):
        """Create the connection"""
        super(Leg, self).connect()

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        super(Leg, self).finalize()

    def setupProxyAttributes(self):
        """Setup the proxy attributes """
        super(Leg, self).setupProxyAttributes()
        rigamajig2.maya.attr.addSeparator(self.limb_ik[-1], '----')
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'roll'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'bank'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'heelSwivel'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'toeSwivel'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'toeTap'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'ballAngle'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'toeStraightAngle'), self.limb_ik[-1])
