"""
main component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.container
import rigamajig2.maya.node
import rigamajig2.maya.attr
import rigamajig2.maya.skeleton

import logging

logger = logging.getLogger(__name__)


class Arm(rigamajig2.maya.cmpts.base.Base):
    def __init__(self, name, input=[], size=1):
        """
        Create a main control
        :param name:
        :param input: list of input joints. This must be a length of 4
        :type input: list
        """
        super(Arm, self).__init__(name, input=input, size=size)
        self.side = common.getSide(self.name)
        self.metaData['component_side'] = self.side

        # noinspection PyTypeChecker
        if len(self.input) != 4:
            logger.error('Input list must have a length of 4')

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control = cmds.createNode('transform', n=self.name + '_control', parent=self.root)

        # clavical/swing controls
        self.clavical = rig_control.createAtObject("clavical_{}".format(self.side), hierarchy=['trsBuffer'],
                                                   size=self.size, color='blue', parent=self.control, shape='square',
                                                   xformObj=self.input[0])
        self.shoulderSwing = rig_control.createAtObject("shoulderSwing_{}".format(self.side),
                                                        hierarchy=['trsBuffer', 'spaces_trs'],
                                                        hideAttrs=['v', 's'], size=self.size, color='blue',
                                                        parent=self.clavical[-1],
                                                        shape='square', xformObj=self.input[1])
        # fk controls
        self.shoulder = rig_control.createAtObject("shoulder_fk_{}".format(self.side),
                                                   hierarchy=['trsBuffer', 'spaces_trs'], hideAttrs=['v', 't', 's'],
                                                   size=self.size, color='blue', parent=self.control, shape='circle',
                                                   xformObj=self.input[1], shapeAim='x')
        self.elbow = rig_control.createAtObject("elbow_fk_{}".format(self.side), hierarchy=['trsBuffer'],
                                                hideAttrs=['v', 't', 's'],
                                                size=self.size, color='blue', parent=self.shoulder[-1], shape='circle',
                                                xformObj=self.input[2], shapeAim='x')
        self.wrist = rig_control.createAtObject("wrist_fk_{}".format(self.side), hierarchy=['trsBuffer'],
                                                hideAttrs=['v', 't', 's'],
                                                size=self.size, color='blue', parent=self.elbow[-1], shape='circle',
                                                xformObj=self.input[3], shapeAim='x')

        # Ik controls
        self.arm_ik = rig_control.create("arm_ik_{}".format(self.side), hierarchy=['trsBuffer', 'spaces_trs'],
                                         hideAttrs=['s', 'v'], size=self.size, color='blue',
                                         parent=self.control,
                                         shape='cube', position=cmds.xform(self.input[-1], q=True, ws=True, t=True))
        pv_pos = ikfk.IkFkLimb.getPoleVectorPos(self.input[1:])
        self.arm_pv = rig_control.create("arm_pv_{}".format(self.side), hierarchy=['trsBuffer', 'spaces_trs'],
                                         hideAttrs=['r', 's', 'v'],
                                         size=self.size, color='blue', shape='pyramid', position=pv_pos,
                                         parent=self.control, shapeAim='z')

        # add the controls to our controller list
        self.controlers += [self.clavical[-1], self.shoulderSwing[-1], self.shoulder[-1], self.elbow[-1],
                            self.wrist[-1], self.arm_ik[-1], self.arm_pv[-1]]

    def rigSetup(self):
        """Add the self.rig setup"""
        self.ikfk = ikfk.IkFkLimb(self.input[1:])
        self.ikfk.setGroup(self.root)
        self.ikfk.create()
        self._ikStartTgt, self._ikEndTgt = self.ikfk.createStretchyIk(self.ikfk.getHandle(), grp=self.ikfk.getGroup())

        # connect the shoulderSwing to the other chains
        cmds.parentConstraint(self.shoulderSwing[-1], self.shoulder[0], mo=True)
        cmds.parentConstraint(self.shoulderSwing[-1], self.ikfk.getIkJointList()[0], mo=True)
        cmds.parentConstraint(self.shoulderSwing[-1], self._ikStartTgt, mo=True)

        # connect fk controls to fk joints
        rigamajig2.maya.skeleton.connectChains([self.shoulder[-1], self.elbow[-1], self.wrist[-1]],
                                               self.ikfk.getFkJointList())

        # connect the IkHandle to the end Target
        cmds.pointConstraint(self.arm_ik[-1], self._ikEndTgt, mo=True)
        cmds.orientConstraint(self.arm_ik[-1], self.ikfk.getIkJointList()[-1], mo=True)

        # create a pole vector contraint
        cmds.poleVectorConstraint(self.arm_pv[-1], self.ikfk.getHandle())

        self.setupProxyAttributes()

    def postRigSetup(self):
        # connect the blend chain to the bind chain
        rigamajig2.maya.skeleton.connectChains(self.ikfk.getBlendJointList(), self.input[1:])

    def setupProxyAttributes(self):
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.root, 'ikfk'), self.controlers)

        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.root, 'stretch'), self.arm_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.root, 'stretchTop'), self.arm_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.root, 'stretchBot'), self.arm_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.root, 'softStretch'), self.arm_ik[-1])

    def finalize(self):
        pass

    def setAttrs(self):
        """
        Set some attributes to values that make more sense
        """
        cmds.setAttr("{}.{}".format(self.arm_ik[-1], 'softStretch'), 0.2)