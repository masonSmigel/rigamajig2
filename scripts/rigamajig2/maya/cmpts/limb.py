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


class Limb(rigamajig2.maya.cmpts.base.Base):

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
        super(Limb, self).__init__(name, input=input, size=size)
        self.side = common.getSide(self.name)

        self.metaData['component_side'] = self.side
        # initalize cmpt settings.

        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.cmptSettings['limbBaseName'] = inputBaseNames[0]
        self.cmptSettings['limbSwingName'] = inputBaseNames[1] + "Swing"
        self.cmptSettings['joint1_fkName'] = inputBaseNames[1] + "_fk"
        self.cmptSettings['joint2_fkName'] = inputBaseNames[2] + "_fk"
        self.cmptSettings['joint3_fkName'] = inputBaseNames[3] + "_fk"
        self.cmptSettings['limb_ikName'] = self.name.split("_")[0] + "_ik"
        self.cmptSettings['limb_pvName'] = self.name.split("_")[0] + "_pv"
        self.cmptSettings['ikSpaces'] = ikSpaces
        self.cmptSettings['pvSpaces'] = pvSpaces

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control = cmds.createNode('transform', n=self.name + '_control', parent=self.root)
        self.spaces = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root)

        # limbBase/swing controls
        self.limbBase = rig_control.createAtObject(self._userSettings['limbBaseName'], self.side,
                                                   hierarchy=['trsBuffer'], hideAttrs=['v', 's'],
                                                   size=self.size, color='blue', parent=self.control,
                                                   shape='square', xformObj=self.input[0])
        self.limbSwing = rig_control.createAtObject(self._userSettings['limbSwingName'], self.side,
                                                    hierarchy=['trsBuffer', 'spaces_trs'],
                                                    hideAttrs=['v', 's'], size=self.size, color='blue',
                                                    parent=self.limbBase[-1], shape='square',
                                                    xformObj=self.input[1])

        # fk controls
        self.joint1_fk = rig_control.createAtObject(self._userSettings['joint1_fkName'], self.side,
                                                    hierarchy=['trsBuffer', 'spaces_trs'],
                                                    hideAttrs=['v', 't', 's'], size=self.size, color='blue',
                                                    parent=self.control, shape='circle', shapeAim='x',
                                                    xformObj=self.input[1])
        self.joint2_fk = rig_control.createAtObject(self._userSettings['joint2_fkName'], self.side,
                                                    hierarchy=['trsBuffer'], hideAttrs=['v', 't', 's'],
                                                    size=self.size, color='blue', parent=self.joint1_fk[-1],
                                                    shape='circle', shapeAim='x', xformObj=self.input[2])
        self.joint3_fk = rig_control.createAtObject(self._userSettings['joint3_fkName'], self.side,
                                                    hierarchy=['trsBuffer'], hideAttrs=['v', 't', 's'],
                                                    size=self.size, color='blue', parent=self.joint2_fk[-1],
                                                    shape='circle', shapeAim='x', xformObj=self.input[3])

        # Ik controls
        self.limb_ik = rig_control.create(self._userSettings['limb_ikName'], self.side,
                                          hierarchy=['trsBuffer', 'spaces_trs'],
                                          hideAttrs=['s', 'v'], size=self.size, color='blue', parent=self.control,
                                          shape='cube', position=cmds.xform(self.input[-1], q=True, ws=True, t=True))
        pv_pos = ikfk.IkFkLimb.getPoleVectorPos(self.input[1:], magnitude=0)
        self.limb_pv = rig_control.create(self._userSettings['limb_pvName'], self.side,
                                          hierarchy=['trsBuffer', 'spaces_trs'],
                                          hideAttrs=['r', 's', 'v'], size=self.size, color='blue', shape='diamond',
                                          position=pv_pos, parent=self.control, shapeAim='z')

        # add the controls to our controller list
        self.fkControls = [self.joint1_fk[-1], self.joint2_fk[-1], self.joint3_fk[-1]]
        self.ikControls = [self.limb_ik[-1], self.limb_pv[-1]]
        self.controlers += [self.limbBase[-1], self.limbSwing[-1]] + self.fkControls + self.ikControls

    def rigSetup(self):
        """Add the rig setup"""
        self.ikfk = ikfk.IkFkLimb(self.input[1:])
        self.ikfk.setGroup(self.name + '_ikfk')
        self.ikfk.create()
        self.ikJnts = self.ikfk.getIkJointList()
        self.fkJnts = self.ikfk.getFkJointList()

        cmds.parent(self.ikfk.getGroup(), self.root)

        # create a pole vector contraint
        cmds.poleVectorConstraint(self.limb_pv[-1], self.ikfk.getHandle())

        self._ikStartTgt, self._ikEndTgt = self.ikfk.createStretchyIk(self.ikfk.getHandle(), grp=self.ikfk.getGroup())

        # connect the limbSwing to the other chains
        cmds.parentConstraint(self.limbSwing[-1], self.joint1_fk[0], mo=True)
        cmds.parentConstraint(self.limbSwing[-1], self.ikfk.getIkJointList()[0], mo=True)
        cmds.parentConstraint(self.limbSwing[-1], self._ikStartTgt, mo=True)

        # connect fk controls to fk joints
        rigamajig2.maya.skeleton.connectChains([self.joint1_fk[-1], self.joint2_fk[-1], self.joint3_fk[-1]], self.fkJnts)

        # connect the IkHandle to the end Target
        cmds.pointConstraint(self.limb_ik[-1], self._ikEndTgt, mo=True)
        cmds.orientConstraint(self.limb_ik[-1], self.ikfk.getIkJointList()[-1], mo=True)

        # connect twist of ikHandle to ik arm
        cmds.addAttr(self.ikfk.getGroup(), ln='twist', at='float', k=True)
        cmds.connectAttr("{}.{}".format(self.ikfk.getGroup(), 'twist'), "{}.{}".format(self.ikfk.getHandle(), 'twist'))

        self.setupProxyAttributes()
        self.ikfkMatchSetup()

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        rigamajig2.maya.skeleton.connectChains(self.ikfk.getBlendJointList(), self.input[1:])
        ikfk.IkFkBase.connnectIkFkVisibility(self.ikfk.getGroup(), 'ikfk', ikList=self.ikControls, fkList=self.fkControls)

    def connect(self):
        """Create the connection"""
        spaces.create(self.limbSwing[1], self.limbSwing[-1], parent=self.spaces)
        spaces.create(self.limb_ik[1], self.limb_ik[-1], parent=self.spaces, defaultName='world')
        spaces.create(self.limb_pv[1], self.limb_pv[-1], parent=self.spaces, defaultName='world')

        # if the main control exists connect the world space
        if cmds.objExists('trs_motion'):
            spaces.addSpace(self.limbSwing[1], ['trs_motion'], nameList=['world'], constraintType='orient')

        if self._userSettings['ikSpaces']:
            spaces.addSpace(self.limb_ik[1], [self._userSettings['ikSpaces'][k] for k in self._userSettings['ikSpaces'].keys()],
                            self._userSettings['ikSpaces'].keys(), 'parent')

        if self._userSettings['pvSpaces']:
            spaces.addSpace(self.limb_pv[1], [self._userSettings['pvSpaces'][k] for k in self._userSettings['pvSpaces'].keys()],
                            self._userSettings['pvSpaces'].keys(), 'parent')

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        rigamajig2.maya.attr.lockAndHide(self.root, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.control, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.spaces, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.ikfk.getGroup(), rigamajig2.maya.attr.TRANSFORMS + ['v'])

    def showAdvancedProxy(self):
        """Show Advanced Proxy"""
        import rigamajig2.maya.rig.live as live

        self.proxySetupGrp = cmds.createNode("transform", n=self.proxySetupGrp)
        tmpPv = live.createlivePoleVector(self.input[1:])
        cmds.parent(tmpPv, self.proxySetupGrp)
        rig_control.createDisplayLine(self.input[2], tmpPv, "{}_pvLine".format(self.name), self.proxySetupGrp,'temp')
        rig_control.createDisplayLine(self.input[1], self.input[3], "{}_ikLine".format(self.name), self.proxySetupGrp, "temp")

    # --------------------------------------------------------------------------------
    # helper functions to shorten functions.
    # --------------------------------------------------------------------------------
    def ikfkMatchSetup(self):
        """Setup the ikFKMatching"""
        wristIkOffset = cmds.createNode('transform', name="{}_ikMatch".format(self.input[3]), p=self.fkJnts[-1])
        rig_transform.matchTransform(self.limb_ik[-1], wristIkOffset)
        rigamajig2.maya.attr.lock(wristIkOffset, ['t', 'r', 's', 'v'])

        # add required data to the ikFkSwitchGroup
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkJnts[:-1] + [wristIkOffset], 'fkMatchList', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.ikJnts, 'ikMatchList', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkControls, 'fkControls', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), [self.limb_ik[-1], self.limb_pv[-1]], 'ikControls', 'matchNode')

    def setupProxyAttributes(self):
        for control in self.controlers:
            rigamajig2.maya.attr.addSeparator(control, '----')
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'ikfk'), self.controlers)
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretch'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretchTop'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretchBot'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'softStretch'), self.limb_ik[-1])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'pvPin'), [self.limb_ik[-1], self.limb_pv[-1]])
        rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'twist'), self.limb_ik[-1])
