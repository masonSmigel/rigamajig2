"""
main component
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2

import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.constrain as constrain
import rigamajig2.maya.node
import rigamajig2.maya.attr
import rigamajig2.maya.joint
import rigamajig2.maya.rig.spline as spline

import logging

logger = logging.getLogger(__name__)


class Limb(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, ikSpaces=dict(), pvSpaces=dict(),
                 useProxyAttrs=True, useScale=True, addTwistJoints=True, addBendies=True,
                 rigParent=str()):
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
        :param useScale: use scale on the controls
        :type useScale: bool
        """
        super(Limb, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptData['component_side'] = self.side
        # initalize cmpt settings.
        self.cmptSettings['useProxyAttrs'] = useProxyAttrs
        self.cmptSettings['useScale'] = useScale
        self.cmptSettings['addTwistJoints'] = addTwistJoints
        self.cmptSettings['addBendies'] = addBendies

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

        self.cmptSettings['bend1Name'] = self.name.split("_")[0] + "_1_bend"
        self.cmptSettings['bend2Name'] = self.name.split("_")[0] + "_2_bend"
        self.cmptSettings['bend3Name'] = self.name.split("_")[0] + "_3_bend"
        self.cmptSettings['bend4Name'] = self.name.split("_")[0] + "_4_bend"
        self.cmptSettings['bend5Name'] = self.name.split("_")[0] + "_5_bend"

        self.cmptSettings['ikSpaces'] = ikSpaces
        self.cmptSettings['pvSpaces'] = pvSpaces

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        if self.useScale:
            hideAttrs = []
        else:
            hideAttrs = ['s']

        # limbBase/swing controls
        self.limbBase = rig_control.createAtObject(self.limbBaseName, self.side,
                                                   hierarchy=['trsBuffer'], hideAttrs=['v'] + hideAttrs,
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
                                                    hideAttrs=['v', 't'] + hideAttrs, size=self.size, color='blue',
                                                    parent=self.control_hrc, shape='circle', shapeAim='x',
                                                    xformObj=self.input[1])
        self.joint2_fk = rig_control.createAtObject(self.joint2_fkName, self.side,
                                                    hierarchy=['trsBuffer'], hideAttrs=['v', 't'] + hideAttrs,
                                                    size=self.size, color='blue', parent=self.joint1_fk[-1],
                                                    shape='circle', shapeAim='x', xformObj=self.input[2])
        self.joint3_fk = rig_control.createAtObject(self.joint3_fkName, self.side,
                                                    hierarchy=['trsBuffer'], hideAttrs=['v', 't'] + hideAttrs,
                                                    size=self.size, color='blue', parent=self.joint2_fk[-1],
                                                    shape='circle', shapeAim='x', xformObj=self.input[3])
        self.joint3Gimble_fk = rig_control.createAtObject(self.joint3Gimble_fkName, self.side,
                                                          hierarchy=['trsBuffer'], hideAttrs=['v', 't', 's'],
                                                          size=self.size, color='blue', parent=self.joint3_fk[-1],
                                                          shape='circle', shapeAim='x', xformObj=self.input[3])

        # Ik controls
        self.limb_ik = rig_control.create(self.limb_ikName, self.side,
                                          hierarchy=['trsBuffer', 'spaces_trs'],
                                          hideAttrs=['v'] + hideAttrs, size=self.size, color='blue',
                                          parent=self.control_hrc,
                                          shape='cube', position=cmds.xform(self.input[3], q=True, ws=True, t=True))

        self.limbGimble_ik = rig_control.create(self.limbGimble_ikName, self.side,
                                                hierarchy=['trsBuffer'], hideAttrs=['v', 's'], size=self.size,
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
                                                           hierarchy=['trsBuffer'], hideAttrs=['t', 'r', 's', 'v'],
                                                           size=self.size, color='lightorange', shape='peakedCube',
                                                           xformObj=self.input[3], parent=self.control_hrc,
                                                           shapeAim='x')

        if self.addTwistJoints and self.addBendies:
            self.bend_ctl_hrc = cmds.createNode("transform", n=self.name + "_bendControl", parent=self.control_hrc)

            self.bend1 = rig_control.create(self.bend1Name, self.side, hierarchy=['trsBuffer'],
                                            hideAttrs=['v', 'r','s'], size=self.size,
                                            color='blue', shape='circle', shapeAim='x',
                                            position=cmds.xform(self.input[1], q=True, ws=True, t=True),
                                            parent=self.bend_ctl_hrc)

            bend2_pos = mathUtils.nodePosLerp(self.input[1], self.input[2], 0.5)
            self.bend2 = rig_control.create(self.bend2Name, self.side,
                                            hierarchy=['trsBuffer'], hideAttrs=['v', 's'], size=self.size,
                                            color='blue', shape='circle', shapeAim='x',
                                            position=bend2_pos, parent=self.bend_ctl_hrc)

            self.bend3 = rig_control.create(self.bend3Name, self.side,
                                            hierarchy=['trsBuffer'], hideAttrs=['v', 'r', 's'], size=self.size,
                                            color='blue', shape='circle', shapeAim='x',
                                            position=cmds.xform(self.input[2], q=True, ws=True, t=True),
                                            parent=self.bend_ctl_hrc)

            bend4_pos = mathUtils.nodePosLerp(self.input[2], self.input[3], 0.5)
            self.bend4 = rig_control.create(self.bend2Name, self.side,
                                            hierarchy=['trsBuffer'], hideAttrs=['v', 's'], size=self.size,
                                            color='blue', shape='circle', shapeAim='x',
                                            position=bend4_pos, parent=self.bend_ctl_hrc)

            self.bend5 = rig_control.create(self.bend4Name, self.side,
                                            hierarchy=['trsBuffer'], hideAttrs=['v','r', 's'], size=self.size,
                                            color='blue', shape='circle', shapeAim='x',
                                            position=cmds.xform(self.input[3], q=True, ws=True, t=True),
                                            parent=self.bend_ctl_hrc)

            bend_aim_list = [b[0] for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]
            aimVector = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(self.input[1], allowNegative=True))
            for i in range(len(bend_aim_list)):
                upVector = (0, 0, 1)

                if i == 4:
                    aimVector = mathUtils.scalarMult(aimVector, -1)
                    cmds.delete(cmds.aimConstraint(bend_aim_list[i - 1], bend_aim_list[i], aim=aimVector, u=upVector,
                                                   wut='object', wuo=self.limb_pv[0], mo=False))
                else:
                    cmds.delete(cmds.aimConstraint(bend_aim_list[i + 1], bend_aim_list[i], aim=aimVector, u=upVector,
                                                   wut='object', wuo=self.limb_pv[0], mo=False))
            self.bendControls = [b[-1] for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]

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
        rig_transform.connectOffsetParentMatrix(self.limbSwing[-1], self.joint1_fk[0])
        rig_transform.connectOffsetParentMatrix(self.limbSwing[-1], self.ikfk.getIkJointList()[0], s=False)
        rig_transform.connectOffsetParentMatrix(self.limbSwing[-1], self._ikStartTgt)

        # connect fk controls to fk joints
        rigamajig2.maya.joint.connectChains([self.joint1_fk[-1], self.joint2_fk[-1], self.joint3Gimble_fk[-1]],
                                            self.fkJnts)

        # connect the IkHandle to the end Target
        cmds.pointConstraint(self.limbGimble_ik[-1], self._ikEndTgt, mo=True)
        # TODO: think about a way to take this out. use OffsetParentMatrix instead
        cmds.orientConstraint(self.limbGimble_ik[-1], self.ikfk.getIkJointList()[-1], mo=True)
        # decompose the scale of the gimble control
        cmds.connectAttr("{}.{}".format(self.limb_ik[-1], 's'), "{}.{}".format(self.ikfk.getIkJointList()[-1], 's'))

        # connect twist of ikHandle to ik arm
        cmds.addAttr(self.ikfk.getGroup(), ln='twist', at='float', k=True)
        cmds.connectAttr("{}.{}".format(self.ikfk.getGroup(), 'twist'), "{}.{}".format(self.ikfk.getHandle(), 'twist'))

        # if not using proxy attributes then setup our ikfk controller
        if not self.useProxyAttrs:
            rig_transform.connectOffsetParentMatrix(self.input[3], self.ikfk_control[0])

        if self.addTwistJoints:
            self.twist_hrc = cmds.createNode("transform", n="{}_twist".format(self.name), p=self.root_hrc)

            upp_targets, upp_spline = spline.addTwistJoints(self.input[1], self.input[2], name=self.name + "_upp_twist",
                                                            bind_parent=self.input[1], rig_parent=self.twist_hrc)
            low_targets, low_spline = spline.addTwistJoints(self.input[2], self.input[3], name=self.name + "_low_twist",
                                                            bind_parent=self.input[2], rig_parent=self.twist_hrc)

            # calculate an inverted rotation to negate the upp twist start.
            # This gives a more natural twist down the limb
            twist_mm, twist_dcmp = rigamajig2.maya.node.multMatrix(["{}.worldMatrix".format(self.input[1]), "{}.worldInverseMatrix".format(
                                                                    self.input[0])], outputs=[""], name="{}_invStartTist".format(upp_spline._startTwist))
            if "-" not in rig_transform.getAimAxis(self.input[1]):
                rigamajig2.maya.node.unitConversion("{}.outputRotate".format(twist_dcmp),
                                                    output="{}.r".format(upp_spline._startTwist),
                                                    conversionFactor=-1,
                                                    name="{}_invStartTwistRev".format(self.input[1]))
                ro = [5, 3, 4, 1, 2, 0][cmds.getAttr('{}.rotateOrder'.format(self.input[1]))]
                cmds.setAttr("{}.{}".format(upp_spline._startTwist, 'rotateOrder'), ro)
            else:
                cmds.connectAttr("{}.outputRotate".format(twist_dcmp), "{}.r".format(upp_spline._startTwist))

            # tag the new joints as bind joints
            for jnt in upp_spline.getJointList() + low_spline.getJointList():
                meta.tag(jnt, "bind")
            meta.untag([self.input[1], self.input[2]], "bind")

            aimVector = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(self.input[1], allowNegative=True))
            if self.addBendies:
                rig_transform.connectOffsetParentMatrix(self.input[1], self.bend1[0], mo=True)
                rig_transform.connectOffsetParentMatrix(self.input[2], self.bend3[0], mo=True)
                rig_transform.connectOffsetParentMatrix(self.input[3], self.bend5[0], mo=True)

                # out aim contraints will use the offset groups as an up rotation vector
                cmds.pointConstraint(self.bend1[-1], self.bend3[-1], self.bend2[0])
                cmds.aimConstraint(self.bend3[-1], self.bend2[0], aim=aimVector, u=(0, 1, 0),
                                   wut='objectrotation', wuo=self.bend1[0], mo=True)
                cmds.pointConstraint(self.bend3[-1], self.bend5[-1], self.bend4[0])
                cmds.aimConstraint(self.bend5[-1], self.bend4[0], aim=aimVector, u=(0, 1, 0),
                                   wut='objectrotation', wuo=self.bend3[0], mo=True)

                # create the twist setup
                rig_transform.connectOffsetParentMatrix(self.bend1[-1], upp_targets[0], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend2[-1], upp_targets[1], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend3[-1], upp_targets[2], mo=True)

                rig_transform.connectOffsetParentMatrix(self.bend3[-1], low_targets[0], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend4[-1], low_targets[1], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend5[-1], low_targets[2], mo=True)

            # create attributes for the volume factor
            volumePlug = rigamajig2.maya.attr.addAttr(self.ikfk.getGroup(), "volumeFactor", 'float',value=1, minValue=0)
            cmds.connectAttr(volumePlug, "{}.{}".format(upp_spline.getGroup(), "volumeFactor"))
            cmds.connectAttr(volumePlug, "{}.{}".format(low_spline.getGroup(), "volumeFactor"))

            # re-create a smoother interpolation:
            setScaleList = list(upp_spline._ikJointList)
            for i in range(len(setScaleList)):
                percent = i / float(len(setScaleList) - 1)
                value = mathUtils.lerp(0, 1, percent)
                cmds.setAttr("{}.scale_{}".format(upp_spline._group, upp_spline._ikJointList.index(setScaleList[i])), value)

            setScaleList = list(low_spline._ikJointList)
            for i in range(len(setScaleList)):
                percent = i / float(len(setScaleList) - 1)
                value = mathUtils.lerp(1, 0, percent)
                cmds.setAttr("{}.scale_{}".format(low_spline._group, low_spline._ikJointList.index(setScaleList[i])), value)

        self.ikfkMatchSetup()

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        rigamajig2.maya.joint.connectChains(self.ikfk.getBlendJointList(), self.input[1:4])
        ikfk.IkFkBase.connectVisibility(self.ikfk.getGroup(), 'ikfk', ikList=self.ikControls, fkList=self.fkControls)

        # connect the base to the main bind chain
        rigamajig2.maya.joint.connectChains(self.limbBase[-1], self.input[0])

    def setupAnimAttrs(self):

        if self.useProxyAttrs:
            for control in self.controlers:
                rigamajig2.maya.attr.addSeparator(control, '----')
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'ikfk'), self.controlers)
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretch'), self.limb_ik[-1])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretchTop'), self.limb_ik[-1])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'stretchBot'), self.limb_ik[-1])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'softStretch'), self.limb_ik[-1])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'pvPin'),[self.limb_ik[-1], self.limb_pv[-1]])
            rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'twist'), self.limb_ik[-1])
            if self.addTwistJoints and self.addBendies:
                rigamajig2.maya.attr.addProxy('{}.{}'.format(self.ikfk.getGroup(), 'volumeFactor'), self.limb_ik[-1])
        else:
            rigamajig2.maya.attr.driveAttribute('ikfk', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('stretch', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('stretchTop', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('stretchBot', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('softStretch', self.ikfk.getGroup(), self.ikfk_control[-1])
            rigamajig2.maya.attr.driveAttribute('pvPin', self.ikfk.getGroup(), self.ikfk_control[-1])
            if self.addTwistJoints and self.addBendies:
                rigamajig2.maya.attr.driveAttribute('volumeFactor', self.ikfk.getGroup(), self.ikfk_control[-1])

    def connect(self):
        """Create the connection"""

        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.limbBase[0], mo=True)

        # setup the spaces
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
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkJnts[:-1] + [wristIkOffset], 'fkMatchList',
                                      'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.ikJnts, 'ikMatchList', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkControls, 'fkControls', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.ikControls, 'ikControls', 'matchNode')
