"""
main component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
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


class Arm(rigamajig2.maya.cmpts.base.Base):
    DEFAULT_CONTROL_NAMES = ['clavical', 'shoulderSwing', 'shoulder_fk', 'elbow_fk', 'wrist_fk', 'arm_ik', 'arm_pv']

    def __init__(self, name, input=[], size=1, controlNames=None):
        """
        Create a main control
        :param name:
        :param input: list of input joints. This must be a length of 4
        :type input: list
        """
        super(Arm, self).__init__(name, input=input, size=size)
        self.side = common.getSide(self.name)
        self.controlNames = controlNames

        self.metaData['component_side'] = self.side

        # TODO: cleanup control names. this is kinda dumb
        if self.controlNames is None:
            self.controlNames = self.DEFAULT_CONTROL_NAMES

        # noinspection PyTypeChecker
        if len(self.input) != 4:
            raise RuntimeError('Input list must have a length of 4')

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control = cmds.createNode('transform', n=self.name + '_control', parent=self.root)
        self.spaces = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root)

        # define the control names
        claviCtlName = "{}_{}".format(self.controlNames[0], self.side)
        SwingCtlName = "{}_{}".format(self.controlNames[1], self.side)
        shoulCtlName = "{}_{}".format(self.controlNames[2], self.side)
        elbowCtlName = "{}_{}".format(self.controlNames[3], self.side)
        wirstCtlName = "{}_{}".format(self.controlNames[4], self.side)
        armIkCtlName = "{}_{}".format(self.controlNames[5], self.side)
        armPvCtlName = "{}_{}".format(self.controlNames[6], self.side)

        # clavical/swing controls
        self.clavical = rig_control.createAtObject(claviCtlName, hierarchy=['trsBuffer'], hideAttrs=['v', 's'],
                                                   size=self.size, color='blue', parent=self.control, shape='square',
                                                   xformObj=self.input[0])
        self.shoulderSwing = rig_control.createAtObject(SwingCtlName, hierarchy=['trsBuffer', 'spaces_trs'],
                                                        hideAttrs=['v', 's'], size=self.size, color='blue',
                                                        parent=self.clavical[-1], shape='square',
                                                        xformObj=self.input[1])
        # fk controls
        self.shoulder = rig_control.createAtObject(shoulCtlName, hierarchy=['trsBuffer', 'spaces_trs'],
                                                   hideAttrs=['v', 't', 's'], size=self.size, color='blue',
                                                   parent=self.control, shape='circle', shapeAim='x',
                                                   xformObj=self.input[1])
        self.elbow = rig_control.createAtObject(elbowCtlName, hierarchy=['trsBuffer'], hideAttrs=['v', 't', 's'],
                                                size=self.size, color='blue', parent=self.shoulder[-1], shape='circle',
                                                shapeAim='x', xformObj=self.input[2])
        self.wrist = rig_control.createAtObject(wirstCtlName, hierarchy=['trsBuffer'], hideAttrs=['v', 't', 's'],
                                                size=self.size, color='blue', parent=self.elbow[-1], shape='circle',
                                                shapeAim='x', xformObj=self.input[3])

        # Ik controls
        self.arm_ik = rig_control.create(armIkCtlName, hierarchy=['trsBuffer', 'spaces_trs'], hideAttrs=['s', 'v'],
                                         size=self.size, color='blue', parent=self.control, shape='cube',
                                         position=cmds.xform(self.input[-1], q=True, ws=True, t=True))
        pv_pos = ikfk.IkFkLimb.getPoleVectorPos(self.input[1:], magnitude=0)
        self.arm_pv = rig_control.create(armPvCtlName, hierarchy=['trsBuffer', 'spaces_trs'], hideAttrs=['r', 's', 'v'],
                                         size=self.size, color='blue', shape='diamond', position=pv_pos,
                                         parent=self.control, shapeAim='z')

        # add the controls to our controller list
        self.fkControls = [self.shoulder[-1], self.elbow[-1], self.wrist[-1]]
        self.ikControls = [self.arm_ik[-1], self.arm_pv[-1]]
        self.controlers += [self.clavical[-1], self.shoulderSwing[-1]] + self.fkControls + self.ikControls

    def rigSetup(self):
        """Add the rig setup"""
        self.ikfk = ikfk.IkFkLimb(self.input[1:])
        self.ikfk.setGroup(self.name + '_ikfk')
        self.ikfk.create()
        self.ikJnts = self.ikfk.getIkJointList()
        self.fkJnts = self.ikfk.getFkJointList()

        cmds.parent(self.ikfk.getGroup(), self.root)

        # create a pole vector contraint
        cmds.poleVectorConstraint(self.arm_pv[-1], self.ikfk.getHandle())

        self._ikStartTgt, self._ikEndTgt = self.ikfk.createStretchyIk(self.ikfk.getHandle(), grp=self.ikfk.getGroup())

        # connect the shoulderSwing to the other chains
        cmds.parentConstraint(self.shoulderSwing[-1], self.shoulder[0], mo=True)
        cmds.parentConstraint(self.shoulderSwing[-1], self.ikfk.getIkJointList()[0], mo=True)
        cmds.parentConstraint(self.shoulderSwing[-1], self._ikStartTgt, mo=True)

        # connect fk controls to fk joints
        rigamajig2.maya.skeleton.connectChains([self.shoulder[-1], self.elbow[-1], self.wrist[-1]], self.fkJnts)

        # connect the IkHandle to the end Target
        cmds.pointConstraint(self.arm_ik[-1], self._ikEndTgt, mo=True)
        cmds.orientConstraint(self.arm_ik[-1], self.ikfk.getIkJointList()[-1], mo=True)

        # TODO: add a better tiwst. look at eyad's arrow pv system.
        # maybe implement that, but use an attribute not a control

        # connect twist of ikHandle to ik arm
        cmds.addAttr(self.ikfk.getGroup(), ln='twist', at='float', k=True)
        cmds.connectAttr("{}.{}".format(self.ikfk.getGroup(), 'twist'), "{}.{}".format(self.ikfk.getHandle(), 'twist'))

        self.setupProxyAttributes()
        self.ikfkMatchSetup()

    def postRigSetup(self):
        # connect the blend chain to the bind chain
        rigamajig2.maya.skeleton.connectChains(self.ikfk.getBlendJointList(), self.input[1:])
        ikfk.IkFkBase.connnectIkFkVisibility(self.ikfk.getGroup(), 'ikfk', ikList=self.ikControls, fkList=self.fkControls)

    def connect(self):
        """Create the connection"""
        spaces.create(self.shoulderSwing[1], self.shoulderSwing[-1], parent=self.spaces)
        spaces.create(self.arm_ik[1], self.arm_ik[-1], parent=self.spaces, defaultName='world')
        spaces.create(self.arm_pv[1], self.arm_pv[-1], parent=self.spaces, defaultName='world')

        # TODO: rework all this in a smarter way
        spaces.addSpace(self.arm_pv[1], [self.arm_ik[-1]], nameList=['hand'], constraintType='parent')
        spaces.addSpace(self.arm_ik[1], [self.shoulderSwing[-1]], nameList=['shoulder'], constraintType='parent')
        # if the main control exists connect the world space
        if cmds.objExists('trs_motion'):
            spaces.addSpace(self.shoulderSwing[1], ['trs_motion'], nameList=['world'], constraintType='orient')

    def setAttrs(self):
        """Set some attributes to values that make more sense for the inital setup."""
        cmds.setAttr("{}.{}".format(self.arm_ik[-1], 'softStretch'), 0.2)

    def finalize(self):
        rigamajig2.maya.attr.lockAndHide(self.root, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.control, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.spaces, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.ikfk.getGroup(), rigamajig2.maya.attr.TRANSFORMS + ['v'])

    # --------------------------------------------------------------------------------
    # helper functions to shorten functions.
    # --------------------------------------------------------------------------------
    def ikfkMatchSetup(self):
        """Setup the ikFKMatching"""
        wristIkOffset = cmds.createNode('transform', name="{}_ikMatch".format(self.input[3]), p=self.fkJnts[-1])
        rig_transform.matchTransform(self.arm_ik[-1], wristIkOffset)
        rigamajig2.maya.attr.lock(wristIkOffset, ['t', 'r', 's', 'v'])

        # add required data to the ikFkSwitchGroup
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkJnts[:-1] + [wristIkOffset], 'fkMatchList', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.ikJnts, 'ikMatchList', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkControls, 'fkControls', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), [self.arm_ik[-1], self.arm_pv[-1]], 'ikControls', 'matchNode')

    def setupProxyAttributes(self):
        for control in self.controlers:
            rigamajig2.maya.attr.addSeparator(control, '----')
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'ikfk'), self.controlers)
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretch'), self.arm_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretchTop'), self.arm_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretchBot'), self.arm_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'softStretch'), self.arm_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'pvPin'), [self.arm_ik[-1], self.arm_pv[-1]])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'twist'), self.arm_ik[-1])
