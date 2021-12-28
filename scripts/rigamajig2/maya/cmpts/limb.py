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
import rigamajig2.maya.node
import rigamajig2.maya.attr
import rigamajig2.maya.skeleton

import logging

logger = logging.getLogger(__name__)


class Limb(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, ikSpaces=dict(), pvSpaces=dict(), useProxyAttrs=True):
        """
        Create a main control
        :param name: name of the components
        :type name: str
        :param input: list of input joints. This must be a length of 4
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param: ikSpaces: dictionary of key and space for the ik control.
        :type ikSpaces: dict
        :param: pvSpaces: dictionary of key and space for the pv control.
        :type pvSpaces: dict
        :useProxyAttrs: use proxy attributes instead of an ikfk control
        :type useProxyAttrs: bool
        """
        super(Limb, self).__init__(name, input=input, size=size)
        self.side = common.getSide(self.name)

        self.metaData['component_side'] = self.side
        # initalize cmpt settings.
        self.cmptSettings['useProxyAttrs'] = useProxyAttrs
        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.cmptSettings['limbBaseName'] = inputBaseNames[0]
        self.cmptSettings['limbSwingName'] = inputBaseNames[1] + "Swing"
        self.cmptSettings['joint1_fkName'] = inputBaseNames[1] + "_fk"
        self.cmptSettings['joint2_fkName'] = inputBaseNames[2] + "_fk"
        self.cmptSettings['joint3_fkName'] = inputBaseNames[3] + "_fk"
        self.cmptSettings['joint3Gimble_fkName'] = inputBaseNames[3] + "Gimble_fk"
        self.cmptSettings['limb_ikName'] = self.name.split("_")[0] + "_ik"
        self.cmptSettings['limbGimble_ikName'] = self.name.split("_")[0] + "Gimble_ik"
        self.cmptSettings['limb_pvName'] = self.name.split("_")[0] + "_pv"
        self.cmptSettings['ikSpaces'] = ikSpaces
        self.cmptSettings['pvSpaces'] = pvSpaces

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        # limbBase/swing controls
        self.limbBase = rig_control.createAtObject(self.limbBaseName, self.side,
                                                   hierarchy=['trsBuffer'], hideAttrs=['v', 's'],
                                                   size=self.size, color='blue', parent=self.control_hrc,
                                                   shape='square', xformObj=self.input[0])
        self.limbSwing = rig_control.createAtObject(self.limbSwingName, self.side,
                                                    hierarchy=['trsBuffer', 'spaces_trs'],
                                                    hideAttrs=['v', 's'], size=self.size, color='blue',
                                                    parent=self.limbBase[-1], shape='square',
                                                    xformObj=self.input[1])

        # fk controls
        self.joint1_fk = rig_control.createAtObject(self.joint1_fkName, self.side,
                                                    hierarchy=['trsBuffer', 'spaces_trs'],
                                                    hideAttrs=['v', 't', 's'], size=self.size, color='blue',
                                                    parent=self.control_hrc, shape='circle', shapeAim='x',
                                                    xformObj=self.input[1])
        self.joint2_fk = rig_control.createAtObject(self.joint2_fkName, self.side,
                                                    hierarchy=['trsBuffer'], hideAttrs=['v', 't', 's'],
                                                    size=self.size, color='blue', parent=self.joint1_fk[-1],
                                                    shape='circle', shapeAim='x', xformObj=self.input[2])
        self.joint3_fk = rig_control.createAtObject(self.joint3_fkName, self.side,
                                                    hierarchy=['trsBuffer'], hideAttrs=['v', 't', 's'],
                                                    size=self.size, color='blue', parent=self.joint2_fk[-1],
                                                    shape='circle', shapeAim='x', xformObj=self.input[3])
        self.joint3Gimble_fk = rig_control.createAtObject(self.joint3Gimble_fkName, self.side,
                                                          hierarchy=['trsBuffer'], hideAttrs=['v', 't', 's'],
                                                          size=self.size, color='blue', parent=self.joint3_fk[-1],
                                                          shape='circle', shapeAim='x', xformObj=self.input[3])

        # Ik controls
        self.limb_ik = rig_control.create(self.limb_ikName, self.side,
                                          hierarchy=['trsBuffer', 'spaces_trs'],
                                          hideAttrs=['s', 'v'], size=self.size, color='blue', parent=self.control_hrc,
                                          shape='cube', position=cmds.xform(self.input[3], q=True, ws=True, t=True))

        self.limbGimble_ik = rig_control.create(self.limbGimble_ikName, self.side,
                                                hierarchy=['trsBuffer'], hideAttrs=['s', 'v'], size=self.size,
                                                color='blue', parent=self.limb_ik[-1], shape='sphere',
                                                position=cmds.xform(self.input[3], q=True, ws=True, t=True))

        pv_pos = ikfk.IkFkLimb.getPoleVectorPos(self.input[1:4], magnitude=0)
        self.limb_pv = rig_control.create(self.limb_pvName, self.side,
                                          hierarchy=['trsBuffer', 'spaces_trs'],
                                          hideAttrs=['r', 's', 'v'], size=self.size, color='blue', shape='diamond',
                                          position=pv_pos, parent=self.control_hrc, shapeAim='z')

        # if we dont want to use proxy attributes then create an attribute to hold attributes
        if not self.useProxyAttrs:
            self.ikfk_control = rig_control.createAtObject(self.name,
                                                           hierarchy=['trsBuffer'], hideAttrs=['t','r', 's', 'v'],
                                                           size=self.size, color='lightorange', shape='peakedCube',
                                                           xformObj=self.input[3], parent=self.control_hrc,
                                                           shapeAim='x')

        # add the controls to our controller list
        self.fkControls = [self.joint1_fk[-1], self.joint2_fk[-1], self.joint3_fk[-1], self.joint3Gimble_fk[-1]]
        self.ikControls = [self.limb_ik[-1], self.limbGimble_ik[-1], self.limb_pv[-1]]
        self.controlers += [self.limbBase[-1], self.limbSwing[-1]] + self.fkControls + self.ikControls

    def rigSetup(self):
        """Add the rig setup"""
        self.ikfk = ikfk.IkFkLimb(self.input[1:4])
        self.ikfk.setGroup(self.name + '_ikfk')
        self.ikfk.create()
        self.ikJnts = self.ikfk.getIkJointList()
        self.fkJnts = self.ikfk.getFkJointList()

        cmds.parent(self.ikfk.getGroup(), self.root_hrc)

        # create a pole vector contraint
        cmds.poleVectorConstraint(self.limb_pv[-1], self.ikfk.getHandle())

        self._ikStartTgt, self._ikEndTgt = self.ikfk.createStretchyIk(self.ikfk.getHandle(), grp=self.ikfk.getGroup())

        # connect the limbSwing to the other chains
        cmds.parentConstraint(self.limbSwing[-1], self.joint1_fk[0], mo=True)
        cmds.parentConstraint(self.limbSwing[-1], self.ikfk.getIkJointList()[0], mo=True)
        cmds.parentConstraint(self.limbSwing[-1], self._ikStartTgt, mo=True)

        # connect fk controls to fk joints
        rigamajig2.maya.skeleton.connectChains([self.joint1_fk[-1], self.joint2_fk[-1], self.joint3Gimble_fk[-1]],
                                               self.fkJnts)

        # connect the IkHandle to the end Target
        cmds.pointConstraint(self.limbGimble_ik[-1], self._ikEndTgt, mo=True)
        cmds.orientConstraint(self.limbGimble_ik[-1], self.ikfk.getIkJointList()[-1], mo=True)

        # connect twist of ikHandle to ik arm
        cmds.addAttr(self.ikfk.getGroup(), ln='twist', at='float', k=True)
        cmds.connectAttr("{}.{}".format(self.ikfk.getGroup(), 'twist'), "{}.{}".format(self.ikfk.getHandle(), 'twist'))

        # if not using proxy attributes then setup our ikfk controller
        if not self.useProxyAttrs:
            cmds.parentConstraint(self.input[3], self.ikfk_control[0], mo=False)

        self.ikfkMatchSetup()

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        rigamajig2.maya.skeleton.connectChains(self.ikfk.getBlendJointList(), self.input[1:4])
        ikfk.IkFkBase.connectVisibility(self.ikfk.getGroup(), 'ikfk', ikList=self.ikControls, fkList=self.fkControls)

        # connect the base to the main bind chain
        rigamajig2.maya.skeleton.connectChains(self.limbBase[-1], self.input[0])

    def setupAnimAttrs(self):

        if self.useProxyAttrs:
            for control in self.controlers:
                rigamajig2.maya.attr.addSeparator(control, '----')
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'ikfk'), self.controlers)
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretch'), self.limb_ik[-1])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretchTop'), self.limb_ik[-1])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretchBot'), self.limb_ik[-1])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'softStretch'), self.limb_ik[-1])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'pvPin'),
                                          [self.limb_ik[-1], self.limb_pv[-1]])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'twist'), self.limb_ik[-1])
        else:
            rigamajig2.maya.attr.driveAttribute('ikfk', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('stretch', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('stretchTop', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('stretchBot', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('softStretch', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('pvPin', self.ikfk.getGroup(), self.ikfk_control[-1])

    def connect(self):
        """Create the connection"""
        spaces.create(self.limbSwing[1], self.limbSwing[-1], parent=self.spaces_hrc)
        spaces.create(self.limb_ik[1], self.limb_ik[-1], parent=self.spaces_hrc, defaultName='world')
        spaces.create(self.limb_pv[1], self.limb_pv[-1], parent=self.spaces_hrc, defaultName='world')

        # if the main control exists connect the world space
        if cmds.objExists('trs_motion'):
            spaces.addSpace(self.limbSwing[1], ['trs_motion'], nameList=['world'], constraintType='orient')

        if self.ikSpaces:
            spaces.addSpace(self.limb_ik[1], [self.ikSpaces[k] for k in self.ikSpaces.keys()], self.ikSpaces.keys(), 'parent')

        if self.pvSpaces:
            spaces.addSpace(self.limb_pv[1], [self.pvSpaces[k] for k in self.pvSpaces.keys()], self.pvSpaces.keys(), 'parent')

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        rigamajig2.maya.attr.lockAndHide(self.root_hrc, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.control_hrc, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.spaces_hrc, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lockAndHide(self.ikfk.getGroup(), rigamajig2.maya.attr.TRANSFORMS + ['v'])

    def showAdvancedProxy(self):
        """Show Advanced Proxy"""
        import rigamajig2.maya.rig.live as live

        self.proxySetupGrp = cmds.createNode("transform", n=self.proxySetupGrp)
        tmpPv = live.createlivePoleVector(self.input[1:4])
        cmds.parent(tmpPv, self.proxySetupGrp)
        rig_control.createDisplayLine(self.input[2], tmpPv, "{}_pvLine".format(self.name), self.proxySetupGrp, 'temp')
        rig_control.createDisplayLine(self.input[1], self.input[3], "{}_ikLine".format(self.name), self.proxySetupGrp,
                                      "temp")

    def setAttrs(self):
        """ Set some attributes to values that make more sense for the inital setup."""
        if self.useProxyAttrs:
            cmds.setAttr("{}.{}".format(self.limb_ik[-1], 'softStretch'), 0.2)
        else:
            cmds.setAttr("{}.{}".format(self.ikfk_control[-1], 'softStretch'), 0.2)

    # --------------------------------------------------------------------------------
    # helper functions to shorten functions.
    # --------------------------------------------------------------------------------
    def ikfkMatchSetup(self):
        """Setup the ikFKMatching"""
        wristIkOffset = cmds.createNode('transform', name="{}_ikMatch".format(self.input[3]), p=self.fkJnts[-1])
        rig_transform.matchTransform(self.limb_ik[-1], wristIkOffset)
        rigamajig2.maya.attr.lock(wristIkOffset, ['t', 'r', 's', 'v'])

        # add required data to the ikFkSwitchGroup
        # TODO: try to check this out. maybe use the ikfk group instead of the attribute
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkJnts[:-1] + [wristIkOffset], 'fkMatchList','matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.ikJnts, 'ikMatchList', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkControls, 'fkControls', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.ikControls, 'ikControls', 'matchNode')
