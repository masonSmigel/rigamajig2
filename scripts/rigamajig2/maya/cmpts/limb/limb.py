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
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.joint
import rigamajig2.maya.rig.spline as spline

import logging

logger = logging.getLogger(__name__)


class Limb(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, ikSpaces=dict(), pvSpaces=dict(),
                 useProxyAttrs=True, useScale=True, addTwistJoints=True, addBendies=True,
                 rigParent=str()):
        """
        Create a limb component. (This component is most often used as a subclass)

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
        :param useProxyAttrs: use proxy attributes instead of an ikfk control
        :type useProxyAttrs: bool
        :param useScale: use scale on the controls
        :type useScale: bool
        """
        super(Limb, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['component_side'] = self.side
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

    def createBuildGuides(self):
        """Show Advanced Proxy"""
        import rigamajig2.maya.rig.live as live

        self.guides_hrc = cmds.createNode("transform", name='{}_guide'.format(self.name))
        self.guide_pv = live.createlivePoleVector(self.input[1:4])
        cmds.parent(self.guide_pv, self.guides_hrc)
        rig_control.createDisplayLine(self.input[2], self.guide_pv, "{}_pvLine".format(self.name), self.guides_hrc)
        rig_control.createDisplayLine(self.input[1], self.input[3], "{}_ikLine".format(self.name), self.guides_hrc)

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Limb, self).initalHierachy()

        hideAttrs = [] if self.useScale else ['s']

        # limbBase/swing controls
        self.limbBase = rig_control.createAtObject(
            self.limbBaseName,
            self.side,
            orig=True,
            hideAttrs=['v'] + hideAttrs,
            size=self.size,
            color='blue',
            parent=self.control_hrc,
            shape='square',
            xformObj=self.input[0]
            )
        self.limbSwing = rig_control.createAtObject(
            self.limbSwingName,
            self.side,
            orig=True, spaces=True,
            hideAttrs=['v', 's'],
            size=self.size,
            color='blue',
            parent=self.limbBase.name,
            shape='square',
            xformObj=self.input[1]
            )

        # fk controls
        self.joint1_fk = rig_control.createAtObject(
            self.joint1_fkName,
            self.side,
            orig=True, spaces=True,
            hideAttrs=['v', 't'] + hideAttrs,
            size=self.size, color='blue',
            parent=self.control_hrc,
            shape='circle',
            shapeAim='x',
            xformObj=self.input[1]
            )
        self.joint2_fk = rig_control.createAtObject(
            self.joint2_fkName, self.side,
            orig=True,
            hideAttrs=['v', 't'] + hideAttrs,
            size=self.size,
            color='blue',
            parent=self.joint1_fk.name,
            shape='circle',
            shapeAim='x',
            xformObj=self.input[2]
            )
        self.joint3_fk = rig_control.createAtObject(
            self.joint3_fkName, self.side,
            orig=True,
            hideAttrs=['v', 't'] + hideAttrs,
            size=self.size,
            color='blue',
            parent=self.joint2_fk.name,
            shape='circle',
            shapeAim='x',
            xformObj=self.input[3]
            )
        self.joint3Gimble_fk = rig_control.createAtObject(
            self.joint3Gimble_fkName,
            self.side,
            orig=True,
            hideAttrs=['v', 't', 's'],
            size=self.size,
            color='blue',
            parent=self.joint3_fk.name,
            shape='circle',
            shapeAim='x',
            xformObj=self.input[3]
            )

        # Ik controls
        self.limb_ik = rig_control.create(
            self.limb_ikName,
            self.side,
            orig=True, spaces=True,
            hideAttrs=['v'] + hideAttrs,
            size=self.size,
            color='blue',
            parent=self.control_hrc,
            shape='cube',
            position=cmds.xform(self.input[3], q=True, ws=True, t=True)
            )

        self.limbGimble_ik = rig_control.create(
            self.limbGimble_ikName,
            self.side,
            orig=True,
            hideAttrs=['v', 's'],
            size=self.size,
            color='blue',
            parent=self.limb_ik.name,
            shape='sphere',
            position=cmds.xform(self.input[3], q=True, ws=True, t=True)
            )

        # pv_pos = ikfk.IkFkLimb.getPoleVectorPos(self.input[1:4], magnitude=0)
        pv_pos = cmds.xform(self.guide_pv, q=True, ws=True, t=True)
        self.limb_pv = rig_control.create(
            self.limb_pvName,
            self.side,
            orig=True, spaces=True,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='blue',
            shape='diamond',
            position=pv_pos,
            parent=self.control_hrc,
            shapeAim='z'
            )

        # if we dont want to use proxy attributes then create an attribute to hold attributes
        if not self.useProxyAttrs:
            self.ikfk_control = rig_control.createAtObject(
                self.name,
                orig=True,
                hideAttrs=['t', 'r', 's', 'v'],
                size=self.size,
                color='lightorange',
                shape='peakedCube',
                xformObj=self.input[3],
                parent=self.control_hrc,
                shapeAim='x')

        if self.addTwistJoints and self.addBendies:
            self.bend_ctl_hrc = cmds.createNode("transform", n=self.name + "_bendControl", parent=self.control_hrc)

            self.bend1 = rig_control.create(
                self.bend1Name,
                self.side,
                orig=True,
                hideAttrs=['v', 'r', 's'],
                size=self.size,
                color='blue',
                shape='circle', shapeAim='x',
                position=cmds.xform(self.input[1], q=True, ws=True, t=True),
                parent=self.bend_ctl_hrc
                )

            self.bend2 = rig_control.create(
                self.bend2Name,
                self.side,
                orig=True,
                hideAttrs=['v', 's'],
                size=self.size,
                color='blue',
                shape='circle',
                shapeAim='x',
                position=mathUtils.nodePosLerp(self.input[1], self.input[2], 0.5),
                parent=self.bend_ctl_hrc
                )

            self.bend3 = rig_control.create(
                self.bend3Name,
                self.side,
                orig=True,
                hideAttrs=['v', 'r', 's'],
                size=self.size,
                color='blue',
                shape='circle',
                shapeAim='x',
                position=cmds.xform(self.input[2], q=True, ws=True, t=True),
                parent=self.bend_ctl_hrc
                )

            self.bend4 = rig_control.create(
                self.bend2Name,
                self.side,
                orig=True,
                hideAttrs=['v', 's'],
                size=self.size,
                color='blue',
                shape='circle',
                shapeAim='x',
                position=mathUtils.nodePosLerp(self.input[2], self.input[3], 0.5),
                parent=self.bend_ctl_hrc
                )

            self.bend5 = rig_control.create(
                self.bend4Name, self.side,
                orig=True,
                hideAttrs=['v', 'r', 's'],
                size=self.size,
                color='blue',
                shape='circle',
                shapeAim='x',
                position=cmds.xform(self.input[3], q=True, ws=True, t=True),
                parent=self.bend_ctl_hrc
                )

            # aim the controls down the chain
            bend_aim_list = [b.orig for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]
            aimVector = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(self.input[1], allowNegative=True))
            rig_transform.aimChain(bend_aim_list, aimVector=aimVector, upVector=(0,0,1), worldUpObject=self.limb_pv.orig)

            self.bendControls = [b.name for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]

        # add the controls to our controller list
        self.fkControls = [self.joint1_fk.name, self.joint2_fk.name, self.joint3_fk.name, self.joint3Gimble_fk.name]
        self.ikControls = [self.limb_ik.name, self.limbGimble_ik.name, self.limb_pv.name]
        self.controlers += [self.limbBase.name, self.limbSwing.name] + self.fkControls + self.ikControls

    def rigSetup(self):
        """Add the rig setup"""
        self.ikfk = ikfk.IkFkLimb(self.input[1:4])
        self.ikfk.setGroup(self.name + '_ikfk')
        self.ikfk.create(params=self.params_hrc)
        self.ikJnts = self.ikfk.getIkJointList()
        self.fkJnts = self.ikfk.getFkJointList()

        cmds.parent(self.ikfk.getGroup(), self.root_hrc)

        # create a pole vector contraint
        cmds.poleVectorConstraint(self.limb_pv.name, self.ikfk.getHandle())

        self._ikStartTgt, self._ikEndTgt = self.ikfk.createStretchyIk(self.ikfk.getHandle(),
                                                                      grp=self.ikfk.getGroup(),
                                                                      params=self.params_hrc)

        # connect the limbSwing to the other chains
        rig_transform.connectOffsetParentMatrix(self.limbSwing.name, self.joint1_fk.orig, s=False, sh=False)
        rig_transform.connectOffsetParentMatrix(self.limbSwing.name, self.ikfk.getIkJointList()[0], s=False)
        rig_transform.connectOffsetParentMatrix(self.limbSwing.name, self._ikStartTgt)

        # connect fk controls to fk joints
        for ctl, jnt in zip([self.joint1_fk.name, self.joint2_fk.name, self.joint3Gimble_fk.name], self.fkJnts):
            rig_transform.connectOffsetParentMatrix(ctl, jnt)
            rig_attr.lock(jnt, rig_attr.TRANSFORMS + ['v'])

        # connect the IkHandle to the end Target
        cmds.pointConstraint(self.limbGimble_ik.name, self._ikEndTgt, mo=True)
        # TODO: think about a way to take this out. use OffsetParentMatrix instead
        cmds.orientConstraint(self.limbGimble_ik.name, self.ikfk.getIkJointList()[-1], mo=True)

        # decompose the scale of the gimble control
        worldMatrix = "{}.worldMatrix[0]".format(self.limb_ik.name)
        parentInverse = "{}.worldInverseMatrix[0]".format(self.ikfk.getIkJointList()[-2])
        offset = rig_transform.offsetMatrix(self.limb_ik.name, self.ikfk.getIkJointList()[-1])
        rigamajig2.maya.node.multMatrix([list(om2.MMatrix(offset)), worldMatrix, parentInverse],
                                        self.ikfk.getIkJointList()[-1], s=True,
                                        name='{}_scale'.format(self.ikfk.getIkJointList()[-1]))

        # connect twist of ikHandle to ik arm
        cmds.addAttr(self.params_hrc, ln='twist', at='float', k=True)
        cmds.connectAttr("{}.{}".format(self.params_hrc, 'twist'), "{}.{}".format(self.ikfk.getHandle(), 'twist'))

        # if not using proxy attributes then setup our ikfk controller
        if not self.useProxyAttrs:
            rig_transform.connectOffsetParentMatrix(self.input[3], self.ikfk_control.orig)

        if self.addTwistJoints:
            self.twist_hrc = cmds.createNode("transform", n="{}_twist".format(self.name), p=self.root_hrc)

            upp_targets, upp_spline = spline.addTwistJoints(self.input[1], self.input[2], name=self.name + "_upp_twist",
                                                            bind_parent=self.input[1], rig_parent=self.twist_hrc)
            low_targets, low_spline = spline.addTwistJoints(self.input[2], self.input[3], name=self.name + "_low_twist",
                                                            bind_parent=self.input[2], rig_parent=self.twist_hrc)

            # calculate an inverted rotation to negate the upp twist start.
            # This gives a more natural twist down the limb
            twist_mm, twist_dcmp = rigamajig2.maya.node.multMatrix(
                ["{}.worldMatrix".format(self.input[1]), "{}.worldInverseMatrix".format(
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
                rig_transform.connectOffsetParentMatrix(self.input[1], self.bend1.orig, mo=True)
                rig_transform.connectOffsetParentMatrix(self.input[2], self.bend3.orig, mo=True)
                rig_transform.connectOffsetParentMatrix(self.input[3], self.bend5.orig, mo=True)

                # out aim contraints will use the offset groups as an up rotation vector
                cmds.pointConstraint(self.bend1.name, self.bend3.name, self.bend2.orig)
                cmds.aimConstraint(self.bend3.name, self.bend2.orig, aim=aimVector, u=(0, 1, 0),
                                   wut='objectrotation', wuo=self.bend1.orig, mo=True)
                cmds.pointConstraint(self.bend3.name, self.bend5.name, self.bend4.orig)
                cmds.aimConstraint(self.bend5.name, self.bend4.orig, aim=aimVector, u=(0, 1, 0),
                                   wut='objectrotation', wuo=self.bend3.orig, mo=True)

                # create the twist setup
                rig_transform.connectOffsetParentMatrix(self.bend1.name, upp_targets[0], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend2.name, upp_targets[1], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend3.name, upp_targets[2], mo=True)

                rig_transform.connectOffsetParentMatrix(self.bend3.name, low_targets[0], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend4.name, low_targets[1], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend5.name, low_targets[2], mo=True)

            # create attributes for the volume factor
            volumePlug = rig_attr.createAttr(self.params_hrc, "volumeFactor", 'float', value=1, minValue=0)
            cmds.connectAttr(volumePlug, "{}.{}".format(upp_spline.getGroup(), "volumeFactor"))
            cmds.connectAttr(volumePlug, "{}.{}".format(low_spline.getGroup(), "volumeFactor"))

            # re-create a smoother interpolation:
            setScaleList = list(upp_spline._ikJointList)
            for i in range(len(setScaleList)):
                percent = i / float(len(setScaleList) - 1)
                value = mathUtils.lerp(0, 1, percent)
                cmds.setAttr("{}.scale_{}".format(upp_spline._group, upp_spline._ikJointList.index(setScaleList[i])),
                             value)

            setScaleList = list(low_spline._ikJointList)
            for i in range(len(setScaleList)):
                percent = i / float(len(setScaleList) - 1)
                value = mathUtils.lerp(1, 0, percent)
                cmds.setAttr("{}.scale_{}".format(low_spline._group, low_spline._ikJointList.index(setScaleList[i])),
                             value)

            # if the module is using the twisty bendy controls then we need to create a visibly control
            rig_attr.createAttr(self.params_hrc, "bendies", "bool", value=1, keyable=True, channelBox=True)
            for bendie_ctl in self.bendControls:
                shapes = cmds.listRelatives(bendie_ctl, s=True)
                for shape in shapes:
                    cmds.connectAttr("{}.{}".format(self.params_hrc, 'bendies'), "{}.{}".format(shape, 'v'))

        self.ikfkMatchSetup()

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        rigamajig2.maya.joint.connectChains(self.ikfk.getBlendJointList(), self.input[1:4])
        ikfk.IkFkBase.connectVisibility(self.params_hrc, 'ikfk', ikList=self.ikControls, fkList=self.fkControls)

        # hide the upper  and middle joints if were using twisty bendy controls
        if self.addTwistJoints:
            for jnt in [self.input[1], self.input[2]]:
                cmds.setAttr("{}.{}".format(jnt, "drawStyle"), 2)

        # connect the base to the main bind chain
        rigamajig2.maya.joint.connectChains(self.limbBase.name, self.input[0])

    def setupAnimAttrs(self):

        if self.useProxyAttrs:
            for control in self.controlers:
                rig_attr.addSeparator(control, '----')
            rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'ikfk'), self.controlers)
            rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'stretch'), self.limb_ik.name)
            rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'stretchTop'), self.limb_ik.name)
            rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'stretchBot'), self.limb_ik.name)
            rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'softStretch'), self.limb_ik.name)
            rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'pvPin'), [self.limb_ik.name, self.limb_pv.name])
            rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'twist'), self.limb_ik.name)
            if self.addTwistJoints and self.addBendies:
                rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'volumeFactor'), self.limb_ik.name)
                rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'bendies'), self.limb_ik.name)
        else:
            rig_attr.driveAttribute('ikfk', self.params_hrc, self.ikfk_control.name)
            rig_attr.driveAttribute('stretch', self.params_hrc, self.ikfk_control.name)
            rig_attr.driveAttribute('stretchTop', self.params_hrc, self.ikfk_control.name)
            rig_attr.driveAttribute('stretchBot', self.params_hrc, self.ikfk_control.name)
            rig_attr.driveAttribute('softStretch', self.params_hrc, self.ikfk_control.name)
            rig_attr.driveAttribute('pvPin', self.params_hrc, self.ikfk_control.name)
            if self.addTwistJoints and self.addBendies:
                rig_attr.driveAttribute('volumeFactor', self.params_hrc, self.ikfk_control.name)
                rig_attr.driveAttribute('bendies', self.params_hrc, self.ikfk_control.name)

    def connect(self):
        """Create the connection"""

        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.limbBase.orig, s=False, sh=False, mo=True)

        # setup the spaces
        spaces.create(self.limbSwing.spaces, self.limbSwing.name, parent=self.spaces_hrc)
        spaces.create(self.limb_ik.spaces, self.limb_ik.name, parent=self.spaces_hrc, defaultName='world')
        spaces.create(self.limb_pv.spaces, self.limb_pv.name, parent=self.spaces_hrc, defaultName='world')

        # if the main control exists connect the world space
        if cmds.objExists('trs_motion'):
            spaces.addSpace(self.limbSwing.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')

        if self.ikSpaces:
            ikspaceValues = [self.ikSpaces[k] for k in self.ikSpaces.keys()]
            spaces.addSpace(self.limb_ik.spaces, ikspaceValues, self.ikSpaces.keys(), 'parent')

        if self.pvSpaces:
            pvSpaceValues = [self.pvSpaces[k] for k in self.pvSpaces.keys()]
            spaces.addSpace(self.limb_pv.spaces, pvSpaceValues, self.pvSpaces.keys(), 'parent')

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        rig_attr.lockAndHide(self.root_hrc, rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.control_hrc, rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.spaces_hrc, rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.ikfk.getGroup(), rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.params_hrc, rig_attr.TRANSFORMS + ['v'])

    def setAttrs(self):
        """ Set some attributes to values that make more sense for the inital setup."""
        if self.useProxyAttrs:
            cmds.setAttr("{}.{}".format(self.limb_ik.name, 'softStretch'), 0.2)
        else:
            cmds.setAttr("{}.{}".format(self.ikfk_control.name, 'softStretch'), 0.2)

    # --------------------------------------------------------------------------------
    # helper functions to shorten functions.
    # --------------------------------------------------------------------------------
    def ikfkMatchSetup(self):
        """Setup the ikFKMatching"""
        wristIkOffset = cmds.createNode('transform', name="{}_ikMatch".format(self.input[3]), p=self.fkJnts[-1])
        rig_transform.matchTransform(self.limb_ik.name, wristIkOffset)
        rig_attr.lock(wristIkOffset, ['t', 'r', 's', 'v'])

        # add required data to the ikFkSwitchGroup
        # TODO: try to check this out. maybe use the ikfk group instead of the attribute
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkJnts[:-1] + [wristIkOffset], 'fkMatchList',
                                      'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.ikJnts, 'ikMatchList', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.fkControls, 'fkControls', 'matchNode')
        meta.addMessageListConnection(self.ikfk.getGroup(), self.ikControls, 'ikControls', 'matchNode')

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=None):
        """static method to create input joints"""
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        GUIDE_POSITIONS = {
            "limbBase": (0, 0, 0),
            "limb_1": (10, 0, 0),
            "limb_2": (25, 0, -2),
            "limb_3": (25, 0, 2)
            }

        joints = list()
        parent = None
        for key in ['limbBase', 'limb_1', 'limb_2', 'limb_3']:
            name = naming.getUniqueName(key, side)
            jnt = cmds.createNode("joint", name=name + "_jnt")
            if parent:
                cmds.parent(jnt, parent)

            position = GUIDE_POSITIONS[key]
            if side == 'r':
                position = (position[0] * -1, position[1], position[2])
            cmds.xform(jnt, objectSpace=True, t=position)

            # add the joints to the joint list
            joints.append(jnt)

            parent = jnt

        # orient the joints
        aimAxis = 'x'
        upAxis = 'z'
        if side == 'r':
            aimAxis = '-x'
            upAxis = '-z'
        joint.orientJoints(joints, aimAxis=aimAxis, upAxis=upAxis)
        return joints