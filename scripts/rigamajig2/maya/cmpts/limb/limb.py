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


# pylint:disable=too-many-instance-attributes
class Limb(rigamajig2.maya.cmpts.base.Base):
    """
    Limb component
    The limb component has an Fk and Ik control blend.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    # pylint:disable=too-many-arguments
    def __init__(self, name, input, size=1, ikSpaces=None, pvSpaces=None,
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

        if ikSpaces is None:
            ikSpaces = dict()

        if pvSpaces is None:
            pvSpaces = dict()

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
        self.cmptSettings['gimble_fkName'] = inputBaseNames[3] + "Gimble_fk"
        self.cmptSettings['limb_ikName'] = self.name.split("_")[0] + "_ik"
        self.cmptSettings['gimble_ikName'] = self.name.split("_")[0] + "Gimble_ik"
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

        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))
        self.guidePoleVector = live.createlivePoleVector(self.input[1:4])
        cmds.parent(self.guidePoleVector, self.guidesHierarchy)
        pvLineName = "{}_pvLine".format(self.name)
        ikLineName = "{}_ikLine".format(self.name)
        rig_control.createDisplayLine(self.input[2], self.guidePoleVector, pvLineName, self.guidesHierarchy)
        rig_control.createDisplayLine(self.input[1], self.input[3], ikLineName, self.guidesHierarchy)

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
            parent=self.controlHierarchy,
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
        self.joint1Fk = rig_control.createAtObject(
            self.joint1_fkName,
            self.side,
            orig=True, spaces=True,
            hideAttrs=['v'] + hideAttrs,
            size=self.size, color='blue',
            parent=self.controlHierarchy,
            shape='circle',
            shapeAim='x',
            xformObj=self.input[1]
            )
        self.joint2Fk = rig_control.createAtObject(
            self.joint2_fkName, self.side,
            orig=True,
            hideAttrs=['v'] + hideAttrs,
            size=self.size,
            color='blue',
            parent=self.joint1Fk.name,
            shape='circle',
            shapeAim='x',
            xformObj=self.input[2]
            )
        self.joint3Fk = rig_control.createAtObject(
            self.joint3_fkName, self.side,
            orig=True,
            hideAttrs=['v'] + hideAttrs,
            size=self.size,
            color='blue',
            parent=self.joint2Fk.name,
            shape='circle',
            shapeAim='x',
            xformObj=self.input[3]
            )
        self.joint3GimbleFk = rig_control.createAtObject(
            self.gimble_fkName,
            self.side,
            orig=True,
            hideAttrs=['v', 't', 's'],
            size=self.size,
            color='blue',
            parent=self.joint3Fk.name,
            shape='circle',
            shapeAim='x',
            xformObj=self.input[3]
            )

        # Ik controls
        self.limbIk = rig_control.create(
            self.limb_ikName,
            self.side,
            orig=True,
            spaces=True,
            hideAttrs=['v'] + hideAttrs,
            size=self.size,
            color='blue',
            parent=self.controlHierarchy,
            shape='cube',
            position=cmds.xform(self.input[3], q=True, ws=True, t=True)
            )

        self.limbGimbleIk = rig_control.create(
            self.gimble_ikName,
            self.side,
            orig=True,
            hideAttrs=['v', 's'],
            size=self.size,
            color='blue',
            parent=self.limbIk.name,
            shape='sphere',
            position=cmds.xform(self.input[3], q=True, ws=True, t=True)
            )

        # pv_pos = ikfk.IkFkLimb.getPoleVectorPos(self.input[1:4], magnitude=0)
        poleVectorPos = cmds.xform(self.guidePoleVector, q=True, ws=True, t=True)
        self.limbPv = rig_control.create(
            self.limb_pvName,
            self.side,
            orig=True, spaces=True,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='blue',
            shape='diamond',
            position=poleVectorPos,
            parent=self.controlHierarchy,
            shapeAim='z'
            )

        # if we dont want to use proxy attributes then create an attribute to hold attributes
        if not self.useProxyAttrs:
            self.ikfkControl = rig_control.createAtObject(
                self.name,
                orig=True,
                hideAttrs=['t', 'r', 's', 'v'],
                size=self.size,
                color='lightorange',
                shape='peakedCube',
                xformObj=self.input[3],
                parent=self.controlHierarchy,
                shapeAim='x')

        if self.addTwistJoints and self.addBendies:
            self.bendControlHierarchy = cmds.createNode(
                "transform",
                n=self.name + "_bendControl",
                parent=self.controlHierarchy
                )

            self.bend1 = rig_control.create(
                self.bend1Name,
                self.side,
                orig=True,
                hideAttrs=['v', 'r', 's'],
                size=self.size,
                color='blue',
                shape='circle', shapeAim='x',
                position=cmds.xform(self.input[1], q=True, ws=True, t=True),
                parent=self.bendControlHierarchy
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
                parent=self.bendControlHierarchy
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
                parent=self.bendControlHierarchy
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
                parent=self.bendControlHierarchy
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
                parent=self.bendControlHierarchy
                )

            # aim the controls down the chain
            bendAimList = [b.orig for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]
            aimVector = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(self.input[1], allowNegative=True))
            rig_transform.aimChain(bendAimList, aimVector=aimVector, upVector=(0, 0, 1),
                                   worldUpObject=self.limbPv.orig)

            self.bendControls = [b.name for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]

        # add the controls to our controller list
        self.fkControls = [self.joint1Fk.name, self.joint2Fk.name, self.joint3Fk.name, self.joint3GimbleFk.name]
        self.ikControls = [self.limbIk.name, self.limbGimbleIk.name, self.limbPv.name]
        self.controlers += [self.limbBase.name, self.limbSwing.name] + self.fkControls + self.ikControls

    # pylint:disable=too-many-statements
    def rigSetup(self):
        """Add the rig setup"""
        self.ikfk = ikfk.IkFkLimb(self.input[1:4])
        self.ikfk.setGroup(self.name + '_ikfk')
        self.ikfk.create(params=self.paramsHierarchy)
        self.ikJnts = self.ikfk.getIkJointList()
        self.fkJnts = self.ikfk.getFkJointList()

        cmds.parent(self.ikfk.getGroup(), self.rootHierarchy)

        # create a pole vector contraint
        cmds.poleVectorConstraint(self.limbPv.name, self.ikfk.getHandle())

        self._ikStartTgt, self._ikEndTgt = self.ikfk.createStretchyIk(self.ikfk.getHandle(),
                                                                      grp=self.ikfk.getGroup(),
                                                                      params=self.paramsHierarchy)

        # connect the limbSwing to the other chains
        rig_transform.connectOffsetParentMatrix(self.limbSwing.name, self.joint1Fk.orig, s=False, sh=False)
        rig_transform.connectOffsetParentMatrix(self.limbSwing.name, self.ikfk.getIkJointList()[0], s=False)
        rig_transform.connectOffsetParentMatrix(self.limbSwing.name, self._ikStartTgt)

        # connect fk controls to fk joints
        for ctl, jnt in zip([self.joint1Fk.name, self.joint2Fk.name, self.joint3GimbleFk.name], self.fkJnts):
            rig_transform.connectOffsetParentMatrix(ctl, jnt)
            rig_attr.lock(jnt, rig_attr.TRANSFORMS + ['v'])

        # connect the IkHandle to the end Target
        cmds.pointConstraint(self.limbGimbleIk.name, self._ikEndTgt, mo=True)
        # TODO: think about a way to take this out. use OffsetParentMatrix instead
        cmds.orientConstraint(self.limbGimbleIk.name, self.ikfk.getIkJointList()[-1], mo=True)

        # decompose the scale of the gimble control
        worldMatrix = "{}.worldMatrix[0]".format(self.limbIk.name)
        parentInverse = "{}.worldInverseMatrix[0]".format(self.ikfk.getIkJointList()[-2])
        offset = rig_transform.offsetMatrix(self.limbIk.name, self.ikfk.getIkJointList()[-1])
        rigamajig2.maya.node.multMatrix([list(om2.MMatrix(offset)), worldMatrix, parentInverse],
                                        self.ikfk.getIkJointList()[-1], s=True,
                                        name='{}_scale'.format(self.ikfk.getIkJointList()[-1]))

        # connect twist of ikHandle to ik arm
        cmds.addAttr(self.paramsHierarchy, ln='twist', at='float', k=True)
        cmds.connectAttr("{}.{}".format(self.paramsHierarchy, 'twist'), "{}.{}".format(self.ikfk.getHandle(), 'twist'))

        # if not using proxy attributes then setup our ikfk controller
        if not self.useProxyAttrs:
            rig_transform.connectOffsetParentMatrix(self.input[3], self.ikfkControl.orig)

        if self.addTwistJoints:
            self.twistHierarchy = cmds.createNode("transform", n="{}_twist".format(self.name), p=self.rootHierarchy)

            uppTargets, uppSpline = spline.addTwistJoints(self.input[1], self.input[2], name=self.name + "_upp_twist",
                                                          bindParent=self.input[1], rigParent=self.twistHierarchy)
            lowTargets, lowSpline = spline.addTwistJoints(self.input[2], self.input[3], name=self.name + "_low_twist",
                                                          bindParent=self.input[2], rigParent=self.twistHierarchy)

            # calculate an inverted rotation to negate the upp twist start.
            # This gives a more natural twist down the limb
            twistMultMatrix, twistDecompose = rigamajig2.maya.node.multMatrix(
                ["{}.worldMatrix".format(self.input[1]), "{}.worldInverseMatrix".format(
                    self.input[0])], outputs=[""], name="{}_invStartTist".format(uppSpline._startTwist))
            # add in a blendMatrix to allow us to
            cmds.addAttr(self.paramsHierarchy, ln='uppCounterTwist', at='float', k=True, dv=1, min=0, max=1)

            blendMatrix = cmds.createNode("blendMatrix", name="{}_conterTwist".format(uppSpline._startTwist))
            cmds.connectAttr("{}.matrixSum".format(twistMultMatrix),"{}.target[0].targetMatrix".format(blendMatrix))
            cmds.connectAttr("{}.outputMatrix".format(blendMatrix), "{}.inputMatrix".format(twistDecompose), f=True)

            cmds.connectAttr("{}.uppCounterTwist".format(self.paramsHierarchy), "{}.envelope".format(blendMatrix))

            if "-" not in rig_transform.getAimAxis(self.input[1]):
                rigamajig2.maya.node.unitConversion("{}.outputRotate".format(twistDecompose),
                                                    output="{}.r".format(uppSpline._startTwist),
                                                    conversionFactor=-1,
                                                    name="{}_invStartTwistRev".format(self.input[1]))
                ro = [5, 3, 4, 1, 2, 0][cmds.getAttr('{}.rotateOrder'.format(self.input[1]))]
                cmds.setAttr("{}.{}".format(uppSpline._startTwist, 'rotateOrder'), ro)
            else:
                cmds.connectAttr("{}.outputRotate".format(twistDecompose), "{}.r".format(uppSpline._startTwist))

            # tag the new joints as bind joints
            for jnt in uppSpline.getJointList() + lowSpline.getJointList():
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
                rig_transform.connectOffsetParentMatrix(self.bend1.name, uppTargets[0], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend2.name, uppTargets[1], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend3.name, uppTargets[2], mo=True)

                rig_transform.connectOffsetParentMatrix(self.bend3.name, lowTargets[0], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend4.name, lowTargets[1], mo=True)
                rig_transform.connectOffsetParentMatrix(self.bend5.name, lowTargets[2], mo=True)

            # create attributes for the volume factor
            volumePlug = rig_attr.createAttr(self.paramsHierarchy, "volumeFactor", 'float', value=1, minValue=0)
            cmds.connectAttr(volumePlug, "{}.{}".format(uppSpline.getGroup(), "volumeFactor"))
            cmds.connectAttr(volumePlug, "{}.{}".format(lowSpline.getGroup(), "volumeFactor"))

            # re-create a smoother interpolation:
            scaleList = list(uppSpline._ikJointList)
            for i in range(len(scaleList)):
                percent = i / float(len(scaleList) - 1)
                value = mathUtils.lerp(0, 1, percent)
                cmds.setAttr("{}.scale_{}".format(uppSpline._group, uppSpline._ikJointList.index(scaleList[i])), value)

            scaleList = list(lowSpline._ikJointList)
            for i in range(len(scaleList)):
                percent = i / float(len(scaleList) - 1)
                value = mathUtils.lerp(1, 0, percent)
                cmds.setAttr("{}.scale_{}".format(lowSpline._group, lowSpline._ikJointList.index(scaleList[i])),
                             value)

            # if the module is using the twisty bendy controls then we need to create a visibly control
            rig_attr.createAttr(self.paramsHierarchy, "bendies", "bool", value=1, keyable=True, channelBox=True)

            for bendieCtl in self.bendControls:
                rig_control.connectControlVisiblity(self.paramsHierarchy, "bendies", bendieCtl)


        self.createIkFkMatchSetup()

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        rigamajig2.maya.joint.connectChains(self.ikfk.getBlendJointList(), self.input[1:4])
        ikfk.IkFkBase.connectVisibility(self.paramsHierarchy, 'ikfk', ikList=self.ikControls, fkList=self.fkControls)

        if self.addTwistJoints:
            for jnt in [self.input[1], self.input[2]]:
                cmds.setAttr("{}.{}".format(jnt, "drawStyle"), 2)

        # connect the base to the main bind chain
        rigamajig2.maya.joint.connectChains(self.limbBase.name, self.input[0])

    def setupAnimAttrs(self):

        if self.useProxyAttrs:
            for control in self.controlers:
                rig_attr.addSeparator(control, '----')
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'ikfk'), self.controlers)
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'stretch'), self.limbIk.name)
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'stretchTop'), self.limbIk.name)
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'stretchBot'), self.limbIk.name)
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'softStretch'), self.limbIk.name)
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'pvPin'), [self.limbIk.name, self.limbPv.name])
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'twist'), self.controlers)
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'uppCounterTwist'), self.limbIk.name)
            if self.addTwistJoints and self.addBendies:
                rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'volumeFactor'), self.limbIk.name)
                rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'bendies'), self.limbIk.name)
        else:
            rig_attr.driveAttribute('ikfk', self.paramsHierarchy, self.ikfkControl.name)
            rig_attr.driveAttribute('stretch', self.paramsHierarchy, self.ikfkControl.name)
            rig_attr.driveAttribute('stretchTop', self.paramsHierarchy, self.ikfkControl.name)
            rig_attr.driveAttribute('stretchBot', self.paramsHierarchy, self.ikfkControl.name)
            rig_attr.driveAttribute('softStretch', self.paramsHierarchy, self.ikfkControl.name)
            rig_attr.driveAttribute('pvPin', self.paramsHierarchy, self.ikfkControl.name)
            rig_attr.driveAttribute('uppCounterTwist', self.paramsHierarchy, self.ikfkControl.name)
            if self.addTwistJoints and self.addBendies:
                rig_attr.driveAttribute('volumeFactor', self.paramsHierarchy, self.ikfkControl.name)
                rig_attr.driveAttribute('bendies', self.paramsHierarchy, self.ikfkControl.name)

        # create a visability control for the ikGimble control
        rig_attr.createAttr(self.limbIk.name, "gimble", attributeType='bool', value=0, keyable=False, channelBox=True)
        rig_control.connectControlVisiblity(self.limbIk.name, "gimble", controls=self.limbGimbleIk.name)

        rig_attr.createAttr(self.joint3Fk.name, "gimble", attributeType='bool', value=0, keyable=False, channelBox=True)
        rig_control.connectControlVisiblity(self.joint3Fk.name, "gimble", controls=self.joint3GimbleFk.name)

    def connect(self):
        """Create the connection"""

        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.limbBase.orig, s=False, sh=False, mo=True)

        # setup the spaces
        spaces.create(self.limbSwing.spaces, self.limbSwing.name, parent=self.spacesHierarchy)
        spaces.create(self.joint1Fk.spaces, self.joint1Fk.name, parent=self.spacesHierarchy)
        spaces.create(self.limbIk.spaces, self.limbIk.name, parent=self.spacesHierarchy, defaultName='world')
        spaces.create(self.limbPv.spaces, self.limbPv.name, parent=self.spacesHierarchy, defaultName='world')

        # if the main control exists connect the world space
        if cmds.objExists('trs_motion'):
            spaces.addSpace(self.limbSwing.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')
            spaces.addSpace(self.joint1Fk.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')

        if self.ikSpaces:
            ikspaceValues = [self.ikSpaces[k] for k in self.ikSpaces.keys()]
            spaces.addSpace(self.limbIk.spaces, ikspaceValues, self.ikSpaces.keys(), 'parent')

        if self.pvSpaces:
            pvSpaceValues = [self.pvSpaces[k] for k in self.pvSpaces.keys()]
            spaces.addSpace(self.limbPv.spaces, pvSpaceValues, self.pvSpaces.keys(), 'parent')

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        rig_attr.lockAndHide(self.rootHierarchy, rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.controlHierarchy, rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.spacesHierarchy, rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.ikfk.getGroup(), rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.paramsHierarchy, rig_attr.TRANSFORMS + ['v'])

    def setAttrs(self):
        """ Set some attributes to values that make more sense for the inital setup."""
        if self.useProxyAttrs:
            cmds.setAttr("{}.{}".format(self.limbIk.name, 'softStretch'), 0.2)
        else:
            cmds.setAttr("{}.{}".format(self.ikfkControl.name, 'softStretch'), 0.2)

    # --------------------------------------------------------------------------------
    # helper functions to shorten functions.
    # --------------------------------------------------------------------------------
    def createIkFkMatchSetup(self):
        """Setup the ikFKMatching"""
        wristIkOffset = cmds.createNode('transform', name="{}_ikMatch".format(self.input[3]), p=self.fkJnts[-1])
        fkJointsMatchList = self.fkJnts[:-1] + [wristIkOffset]
        rig_transform.matchTransform(self.limbIk.name, wristIkOffset)
        rig_attr.lock(wristIkOffset, ['t', 'r', 's', 'v'])

        # add required data to the ikFkSwitchGroup
        # give the node that will store the ikfkSwitch attribute
        if not self.useProxyAttrs:
            meta.createMessageConnection(self.ikfk.getGroup(), self.ikfkControl.name, "ikfkControl")
        meta.createMessageConnection(self.ikfk.getGroup(), fkJointsMatchList, 'fkMatchList', 'matchNode')
        meta.createMessageConnection(self.ikfk.getGroup(), self.ikJnts, 'ikMatchList', 'matchNode')
        meta.createMessageConnection(self.ikfk.getGroup(), self.fkControls, 'fkControls', 'matchNode')
        meta.createMessageConnection(self.ikfk.getGroup(), self.ikControls, 'ikControls', 'matchNode')

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=None):
        """static method to create input joints"""
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        guidePositions = {
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

            position = guidePositions[key]
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
