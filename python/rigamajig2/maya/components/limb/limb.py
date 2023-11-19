"""
main component
"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import joint
from rigamajig2.maya import mathUtils
from rigamajig2.maya import meta
from rigamajig2.maya import node
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import ikfk
from rigamajig2.maya.rig import spaces
from rigamajig2.maya.rig import spline
from rigamajig2.shared import common


class Limb(base.BaseComponent):
    """
    Limb component
    The limb component has an Fk and Ik control blend.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (109, 189, 224)

    # pylint:disable=too-many-arguments
    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
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
        :param useScale: use scale on the controls
        :type useScale: bool
        """
        super(Limb, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        self.useCallbackSwitch = True
        self.useScale = True
        self.addTwistJoints = True
        self.addBendies = True
        self.localOrientIk = True
        self.ikSpaces = {}
        self.pvSpaces = {}

        self.defineParameter(parameter="useCallbackSwitch", value=self.useCallbackSwitch, dataType="bool")
        self.defineParameter(parameter="useScale", value=self.useScale, dataType="bool")
        self.defineParameter(parameter="addTwistJoints", value=self.addTwistJoints, dataType="bool")
        self.defineParameter(parameter="addBendies", value=self.addBendies, dataType="bool")
        self.defineParameter(parameter="localOrientIk", value=self.localOrientIk, dataType="bool")

        self.defineParameter(parameter="ikSpaces", value=self.ikSpaces, dataType="dict")
        self.defineParameter(parameter="pvSpaces", value=self.pvSpaces, dataType="dict")

    def _createBuildGuides(self):
        """Show Advanced Proxy"""
        import rigamajig2.maya.rig.live as live

        self.guidesHierarchy = cmds.createNode("transform", name="{}_guide".format(self.name))
        self.guidePoleVector = live.createlivePoleVector(self.input[1:4])
        cmds.parent(self.guidePoleVector, self.guidesHierarchy)
        pvLineName = "{}_pvLine".format(self.name)
        ikLineName = "{}_ikLine".format(self.name)
        control.createDisplayLine(self.input[2], self.guidePoleVector, pvLineName, self.guidesHierarchy)
        control.createDisplayLine(self.input[1], self.input[3], ikLineName, self.guidesHierarchy)

    def _initialHierarchy(self):
        """Build the initial hirarchy"""
        super(Limb, self)._initialHierarchy()

        hideAttrs = [] if self.useScale else ["s"]

        transform.getTranslate(self.input[0])

        inputBaseNames = [x.split("_")[0] for x in self.input]

        # limbBase/swing controls
        self.limbBase = control.createAtObject(
            name=inputBaseNames[0],
            side=self.side,
            orig=True,
            hideAttrs=["v"] + hideAttrs,
            size=self.size,
            color="blue",
            parent=self.controlHierarchy,
            shape="square",
            xformObj=self.input[0],
        )
        self.limbSwing = control.createAtObject(
            name=inputBaseNames[1] + "Swing",
            side=self.side,
            orig=True,
            spaces=True,
            hideAttrs=["v", "s"],
            size=self.size,
            color="blue",
            parent=self.limbBase.name,
            shape="square",
            xformObj=self.input[1],
        )

        # fk controls
        self.joint1Fk = control.createAtObject(
            name=inputBaseNames[1] + "_fk",
            side=self.side,
            orig=True,
            spaces=True,
            hideAttrs=["v"] + hideAttrs,
            size=self.size,
            color="blue",
            parent=self.controlHierarchy,
            shape="circle",
            shapeAim="x",
            xformObj=self.input[1],
        )
        self.joint2Fk = control.createAtObject(
            name=inputBaseNames[2] + "_fk",
            side=self.side,
            orig=True,
            hideAttrs=["v"] + hideAttrs,
            size=self.size,
            color="blue",
            parent=self.joint1Fk.name,
            shape="circle",
            shapeAim="x",
            xformObj=self.input[2],
        )
        self.joint3Fk = control.createAtObject(
            name=inputBaseNames[3] + "_fk",
            side=self.side,
            orig=True,
            hideAttrs=["v"] + hideAttrs,
            size=self.size,
            color="blue",
            parent=self.joint2Fk.name,
            shape="circle",
            shapeAim="x",
            xformObj=self.input[3],
        )
        self.joint3GimbleFk = control.createAtObject(
            name=inputBaseNames[3] + "Gimble_fk",
            side=self.side,
            orig=True,
            hideAttrs=["v", "t", "s"],
            size=self.size,
            color="blue",
            parent=self.joint3Fk.name,
            shape="circle",
            shapeAim="x",
            xformObj=self.input[3],
        )

        # Ik controls
        self.limbIk = control.create(
            name=self.name.split("_")[0] + "_ik",
            side=self.side,
            orig=True,
            spaces=True,
            hideAttrs=["v"] + hideAttrs,
            size=self.size,
            color="blue",
            parent=self.controlHierarchy,
            shape="cube",
            position=cmds.xform(self.input[3], query=True, worldSpace=True, translation=True),
            rotation=cmds.xform(self.input[3], query=True, worldSpace=True, rotation=True)
            if self.localOrientIk
            else None,
        )

        self.limbGimbleIk = control.createAtObject(
            name=self.name.split("_")[0] + "Gimble_ik",
            side=self.side,
            orig=True,
            hideAttrs=["v", "s"],
            size=self.size,
            color="blue",
            parent=self.limbIk.name,
            shape="sphere",
            xformObj=self.limbIk.name,
        )

        # pv_pos = ikfk.IkFkLimb.getPoleVectorPos(self.input[1:4], magnitude=0)
        poleVectorPos = cmds.xform(self.guidePoleVector, q=True, ws=True, t=True)
        self.limbPv = control.create(
            name=self.name.split("_")[0] + "_pv",
            side=self.side,
            orig=True,
            spaces=True,
            hideAttrs=["r", "s", "v"],
            size=self.size,
            color="blue",
            shape="diamond",
            position=poleVectorPos,
            parent=self.controlHierarchy,
            shapeAim="z",
        )

        self.ikfkControl = control.createAtObject(
            name=self.name,
            orig=True,
            hideAttrs=["t", "r", "s", "v"],
            size=self.size,
            color="lightorange",
            shape="peakedCube" if not self.useCallbackSwitch else None,
            xformObj=self.input[3],
            parent=self.controlHierarchy,
            shapeAim="x",
        )

        if self.useCallbackSwitch:
            self.ikfkProxySwitch = control.createAtObject(
                self.name + "_selection_proxy",
                orig=True,
                hideAttrs=["t", "r", "s", "v"],
                size=self.size,
                color="lightorange",
                shape="peakedCube",
                xformObj=self.input[3],
                parent=self.ikfkControl.name,
                shapeAim="x",
            )

            transform.matchTransform(self.input[0], self.ikfkControl.orig)

        if self.addTwistJoints and self.addBendies:
            self.bendControlHierarchy = cmds.createNode(
                "transform", name=self.name + "_bendControl", parent=self.controlHierarchy
            )

            bendControlName = self.name.split("_")[0] + "_1_bend"
            self.bend1 = control.create(
                name=bendControlName,
                side=self.side,
                orig=True,
                hideAttrs=["v", "r", "s"],
                size=self.size,
                color="blue",
                shape="circle",
                shapeAim="x",
                position=transform.getTranslate(self.input[1]),
                parent=self.bendControlHierarchy,
            )

            self.bend2 = control.create(
                name=bendControlName,
                side=self.side,
                orig=True,
                hideAttrs=["v", "s"],
                size=self.size,
                color="blue",
                shape="circle",
                shapeAim="x",
                position=mathUtils.nodePosLerp(self.input[1], self.input[2], 0.5),
                parent=self.bendControlHierarchy,
            )

            self.bend3 = control.create(
                name=bendControlName,
                side=self.side,
                orig=True,
                hideAttrs=["v", "r", "s"],
                size=self.size,
                color="blue",
                shape="circle",
                shapeAim="x",
                position=transform.getTranslate(self.input[2]),
                parent=self.bendControlHierarchy,
            )

            self.bend4 = control.create(
                name=bendControlName,
                side=self.side,
                orig=True,
                hideAttrs=["v", "s"],
                size=self.size,
                color="blue",
                shape="circle",
                shapeAim="x",
                position=mathUtils.nodePosLerp(self.input[2], self.input[3], 0.5),
                parent=self.bendControlHierarchy,
            )

            self.bend5 = control.create(
                name=bendControlName,
                side=self.side,
                orig=True,
                hideAttrs=["v", "r", "s"],
                size=self.size,
                color="blue",
                shape="circle",
                shapeAim="x",
                position=transform.getTranslate(self.input[3]),
                parent=self.bendControlHierarchy,
            )

            # aim the controls down the chain
            bendAimList = [b.orig for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]
            aimVector = transform.getVectorFromAxis(transform.getAimAxis(self.input[1], allowNegative=True))
            transform.aimChain(bendAimList, aimVector=aimVector, upVector=(0, 0, 1), worldUpObject=self.limbPv.orig)

            self.bendControls = [b.name for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]

        # add the controls to our controller list
        self.fkControls = [self.joint1Fk.name, self.joint2Fk.name, self.joint3Fk.name, self.joint3GimbleFk.name]
        self.ikControls = [self.limbIk.name, self.limbGimbleIk.name, self.limbPv.name]

    # pylint:disable=too-many-statements
    def _rigSetup(self):
        """Add the rig setup"""
        self.ikfk = ikfk.IkFkLimb(self.input[1:4])
        self.ikfk.setGroup(self.name + "_ikfk")
        self.ikfk.create(params=self.paramsHierarchy)

        cmds.parent(self.ikfk.getGroup(), self.rootHierarchy)

        # create a pole vector contraint
        cmds.poleVectorConstraint(self.limbPv.name, self.ikfk.getHandle())

        self._ikStartTgt, self._ikEndTgt = self.ikfk.createStretchyIk(
            self.ikfk.getHandle(), grp=self.ikfk.getGroup(), params=self.paramsHierarchy
        )

        # connect the limbSwing to the other chains
        transform.connectOffsetParentMatrix(self.limbSwing.name, self.joint1Fk.orig, s=False, sh=False)
        transform.connectOffsetParentMatrix(self.limbSwing.name, self.ikfk.getIkJointList()[0], s=False)
        transform.connectOffsetParentMatrix(self.limbSwing.name, self._ikStartTgt)

        # connect fk controls to fk joints
        for ctl, jnt in zip(
            [self.joint1Fk.name, self.joint2Fk.name, self.joint3GimbleFk.name], self.ikfk.getFkJointList()
        ):
            transform.connectOffsetParentMatrix(ctl, jnt)
            attr.lock(jnt, attr.TRANSFORMS + ["v"])

        # connect the IkHandle to the end Target
        cmds.pointConstraint(self.limbGimbleIk.name, self._ikEndTgt, mo=True)
        # TODO: think about a way to take this out. use OffsetParentMatrix instead
        cmds.orientConstraint(self.limbGimbleIk.name, self.ikfk.getIkJointList()[-1], mo=True)

        # create the upperArmLength
        upperArmLenTrs = cmds.createNode("transform", name=f"{self.joint2Fk.name}_len_trs")
        transform.matchTransform(self.joint2Fk.name, upperArmLenTrs)
        transform.matchRotate(self.joint1Fk.name, upperArmLenTrs)
        cmds.parent(upperArmLenTrs, self.joint1Fk.name)
        cmds.parent(self.joint2Fk.orig, upperArmLenTrs)
        self.__connectFkLimbStretch(self.joint1Fk.name, upperArmLenTrs)

        # create the lowerLimbLength Attr
        lowerArmLenTrs = cmds.createNode("transform", name=f"{self.joint3Fk.name}_len_trs")
        transform.matchTransform(self.joint3Fk.name, lowerArmLenTrs)
        transform.matchRotate(self.joint2Fk.name, lowerArmLenTrs)
        cmds.parent(lowerArmLenTrs, self.joint2Fk.name)
        cmds.parent(self.joint3Fk.orig, lowerArmLenTrs)
        self.__connectFkLimbStretch(self.joint2Fk.name, lowerArmLenTrs)

        # decompose the scale of the ik control
        transform.decomposeScale(self.limbIk.name, self.ikfk.getIkJointList()[-1])

        # connect twist of ikHandle to ik arm
        cmds.addAttr(self.paramsHierarchy, ln="twist", at="float", k=True)
        cmds.connectAttr("{}.{}".format(self.paramsHierarchy, "twist"), "{}.{}".format(self.ikfk.getHandle(), "twist"))

        if self.addTwistJoints:
            self.twistHierarchy = cmds.createNode("transform", n="{}_twist".format(self.name), p=self.rootHierarchy)

            uppTargets, uppSpline = spline.addTwistJoints(
                self.input[1],
                self.input[2],
                name=self.name + "_upp_twist",
                bindParent=self.input[1],
                rigParent=self.twistHierarchy,
            )
            lowTargets, lowSpline = spline.addTwistJoints(
                self.input[2],
                self.input[3],
                name=self.name + "_low_twist",
                bindParent=self.input[2],
                rigParent=self.twistHierarchy,
            )

            # calculate an inverted rotation to negate the upp twist start.
            self.__negateUpperLimbTwist(uppSpline)

            # tag the new joints as bind joints
            for jnt in uppSpline.getJointList() + lowSpline.getJointList():
                meta.tag(jnt, common.BINDTAG)
            meta.untag([self.input[1], self.input[2]], common.BINDTAG)

            aimVector = transform.getVectorFromAxis(transform.getAimAxis(self.input[1], allowNegative=True))
            if self.addBendies:
                transform.connectOffsetParentMatrix(self.input[1], self.bend1.orig, mo=True)
                transform.connectOffsetParentMatrix(self.input[2], self.bend3.orig, mo=True)
                transform.connectOffsetParentMatrix(self.input[3], self.bend5.orig, mo=True)

                # out aim contraints will use the offset groups as an up rotation vector
                cmds.pointConstraint(self.bend1.name, self.bend3.name, self.bend2.orig)
                cmds.aimConstraint(
                    self.bend3.name,
                    self.bend2.orig,
                    aim=aimVector,
                    u=(0, 1, 0),
                    wut="objectrotation",
                    wuo=self.bend1.orig,
                    mo=True,
                )
                cmds.pointConstraint(self.bend3.name, self.bend5.name, self.bend4.orig)
                cmds.aimConstraint(
                    self.bend5.name,
                    self.bend4.orig,
                    aim=aimVector,
                    u=(0, 1, 0),
                    wut="objectrotation",
                    wuo=self.bend3.orig,
                    mo=True,
                )

                # create the twist setup
                transform.connectOffsetParentMatrix(self.bend1.name, uppTargets[0], mo=True)
                transform.connectOffsetParentMatrix(self.bend2.name, uppTargets[1], mo=True)
                transform.connectOffsetParentMatrix(self.bend3.name, uppTargets[2], mo=True)

                transform.connectOffsetParentMatrix(self.bend3.name, lowTargets[0], mo=True)
                transform.connectOffsetParentMatrix(self.bend4.name, lowTargets[1], mo=True)
                transform.connectOffsetParentMatrix(self.bend5.name, lowTargets[2], mo=True)

            # create attributes for the volume factor
            volumePlug = attr.createAttr(self.paramsHierarchy, "volumeFactor", "float", value=1, minValue=0)
            cmds.connectAttr(volumePlug, "{}.{}".format(uppSpline.getGroup(), "volumeFactor"))
            cmds.connectAttr(volumePlug, "{}.{}".format(lowSpline.getGroup(), "volumeFactor"))

            self.__unifyBendiesInterp(uppSpline, lowSpline)

            # if the module is using the twisty bendy controls then we need to create a visibly control
            attr.createAttr(self.paramsHierarchy, "bendies", "bool", value=0, keyable=True, channelBox=True)

            for bendieCtl in self.bendControls:
                control.connectControlVisiblity(self.paramsHierarchy, "bendies", bendieCtl)

        self.__createIkFkMatchSetup()

    def _postRigSetup(self):
        """Connect the blend chain to the bind chain"""
        joint.connectChains(self.ikfk.getBlendJointList(), self.input[1:4])
        ikfk.IkFkBase.connectVisibility(self.paramsHierarchy, "ikfk", ikList=self.ikControls, fkList=self.fkControls)

        if self.addTwistJoints:
            for jnt in [self.input[1], self.input[2]]:
                cmds.setAttr("{}.{}".format(jnt, "drawStyle"), 2)

        # connect the base to the main bind chain
        joint.connectChains(self.limbBase.name, self.input[0])

    def _setupAnimAttrs(self):
        attr.driveAttribute("ikfk", self.paramsHierarchy, self.ikfkControl.name)
        attr.driveAttribute("stretch", self.paramsHierarchy, self.ikfkControl.name)
        attr.driveAttribute("stretchTop", self.paramsHierarchy, self.ikfkControl.name)
        attr.driveAttribute("stretchBot", self.paramsHierarchy, self.ikfkControl.name)
        attr.driveAttribute("softStretch", self.paramsHierarchy, self.ikfkControl.name)
        attr.driveAttribute("pvPin", self.paramsHierarchy, self.ikfkControl.name)
        if self.addTwistJoints and self.addBendies:
            attr.driveAttribute("volumeFactor", self.paramsHierarchy, self.ikfkControl.name)
            attr.driveAttribute("bendies", self.paramsHierarchy, self.ikfkControl.name)
            attr.driveAttribute("uppCounterTwist", self.paramsHierarchy, self.ikfkControl.name)

        # create a visability control for the ikGimble control
        attr.createAttr(
            self.limbIk.name, longName="gimble", attributeType="bool", value=0, keyable=False, channelBox=True
        )
        control.connectControlVisiblity(self.limbIk.name, driverAttr="gimble", controls=self.limbGimbleIk.name)

        attr.createAttr(
            self.joint3Fk.name, longName="gimble", attributeType="bool", value=0, keyable=False, channelBox=True
        )
        control.connectControlVisiblity(self.joint3Fk.name, driverAttr="gimble", controls=self.joint3GimbleFk.name)

    def _connect(self):
        """Create the connection"""

        # if not using proxy attributes then setup our ikfk controller

        if self.useCallbackSwitch:
            transform.connectOffsetParentMatrix(self.input[3], self.ikfkProxySwitch.orig)
            transform.connectOffsetParentMatrix(self.input[0], self.ikfkControl.orig)
            meta.createMessageConnection(
                self.ikfkProxySwitch.name,
                self.ikfkControl.name,
                sourceAttr="selectionOverride",
                destAttr="selectionOverridden",
            )
        else:
            transform.connectOffsetParentMatrix(self.input[3], self.ikfkControl.orig)

        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(self.rigParent, self.limbBase.orig, s=False, sh=False, mo=True)

        # setup the spaces
        spaces.create(self.limbSwing.spaces, self.limbSwing.name, parent=self.spacesHierarchy)
        spaces.create(self.joint1Fk.spaces, self.joint1Fk.name, parent=self.spacesHierarchy)
        spaces.create(self.limbIk.spaces, self.limbIk.name, parent=self.spacesHierarchy, defaultName="world")
        spaces.create(self.limbPv.spaces, self.limbPv.name, parent=self.spacesHierarchy, defaultName="world")

        # if the main control exists connect the world space
        if cmds.objExists("trs_motion"):
            spaces.addSpace(self.limbSwing.spaces, ["trs_motion"], nameList=["world"], constraintType="orient")
            spaces.addSpace(self.joint1Fk.spaces, ["trs_motion"], nameList=["world"], constraintType="orient")

        if self.ikSpaces:
            ikSpaceValues = [self.ikSpaces[k] for k in self.ikSpaces.keys()]
            spaces.addSpace(self.limbIk.spaces, ikSpaceValues, list(self.ikSpaces.keys()), constraintType="parent")

        if self.pvSpaces:
            pvSpaceValues = [self.pvSpaces[k] for k in self.pvSpaces.keys()]
            spaces.addSpace(self.limbPv.spaces, pvSpaceValues, list(self.pvSpaces.keys()), constraintType="parent")

    def _finalize(self):
        """Lock some attributes we dont want to see"""
        attr.lockAndHide(self.rootHierarchy, attr.TRANSFORMS + ["v"])
        attr.lockAndHide(self.controlHierarchy, attr.TRANSFORMS + ["v"])
        attr.lockAndHide(self.spacesHierarchy, attr.TRANSFORMS + ["v"])
        attr.lockAndHide(self.ikfk.getGroup(), attr.TRANSFORMS + ["v"])
        attr.lockAndHide(self.paramsHierarchy, attr.TRANSFORMS + ["v"])

    def _setControlAttributes(self):
        """Set some attributes to values that make more sense for the inital setup."""
        cmds.setAttr("{}.{}".format(self.ikfkControl.name, "softStretch"), 0.2)

    # --------------------------------------------------------------------------------
    # helper functions to shorten functions.
    # --------------------------------------------------------------------------------
    def __createIkFkMatchSetup(self):
        """Setup the ikFKMatching"""
        wristIkOffset = cmds.createNode(
            "transform", name=f"{self.input[3]}_ikMatch", parent=self.ikfk.getFkJointList()[-1]
        )
        fkJointsMatchList = self.ikfk.getFkJointList()[:-1] + [wristIkOffset]
        transform.matchTransform(self.limbIk.name, wristIkOffset)
        attr.lock(wristIkOffset, ["t", "r", "s", "v"])

        # add required data to the ikFkSwitchGroup
        ikfkGroup = self.ikfk.getGroup()
        ikJointsList = self.ikfk.getIkJointList()
        meta.createMessageConnection(ikfkGroup, self.ikfkControl.name, sourceAttr="ikfkControl")
        meta.createMessageConnection(ikfkGroup, fkJointsMatchList, sourceAttr="fkMatchList", destAttr="matchNode")
        meta.createMessageConnection(ikfkGroup, ikJointsList, sourceAttr="ikMatchList", destAttr="matchNode")
        meta.createMessageConnection(ikfkGroup, self.fkControls, sourceAttr="fkControls", destAttr="matchNode")
        meta.createMessageConnection(ikfkGroup, self.ikControls, sourceAttr="ikControls", destAttr="matchNode")

    def __connectFkLimbStretch(self, attrHolder, lenTrs):
        """Connect the FK limb stretch"""
        lenAttr = attr.createAttr(attrHolder, longName="length", attributeType="float", value=1, minValue=0.001)
        aimAxis = transform.getAimAxis(attrHolder, allowNegative=False)

        defaultLength = cmds.getAttr(f"{lenTrs}.t{aimAxis}")

        node.multDoubleLinear(
            input1=defaultLength, input2=lenAttr, output=f"{lenTrs}.t{aimAxis}", name=f"{lenTrs}_lengthScale"
        )

    def __negateUpperLimbTwist(self, uppSpline):
        # calculate an inverted rotation to negate the upp twist start.
        # This gives a more natural twist down the limb
        twistMultMatrix, twistDecompose = node.multMatrix(
            inputs=["{}.worldMatrix".format(self.input[1]), "{}.worldInverseMatrix".format(self.input[0])],
            outputs=[""],
            name="{}_invStartTist".format(uppSpline._startTwist),
        )
        # add in a blendMatrix to allow us to
        cmds.addAttr(
            self.paramsHierarchy,
            longName="uppCounterTwist",
            attributeType="float",
            keyable=True,
            defaultValue=1,
            minValue=0,
            maxValue=1,
        )

        blendMatrix = cmds.createNode("blendMatrix", name="{}_conterTwist".format(uppSpline._startTwist))
        cmds.connectAttr("{}.matrixSum".format(twistMultMatrix), "{}.target[0].targetMatrix".format(blendMatrix))
        cmds.connectAttr("{}.outputMatrix".format(blendMatrix), "{}.inputMatrix".format(twistDecompose), f=True)

        cmds.connectAttr("{}.uppCounterTwist".format(self.paramsHierarchy), "{}.envelope".format(blendMatrix))

        if "-" not in transform.getAimAxis(self.input[1]):
            node.unitConversion(
                "{}.outputRotate".format(twistDecompose),
                output="{}.r".format(uppSpline._startTwist),
                conversionFactor=-1,
                name="{}_invStartTwistRev".format(self.input[1]),
            )
            rotateOrder = cmds.getAttr("{}.rotateOrder".format(self.input[1]))
            negatedRotateOrder = transform.ROTATEORDER_NEGATED[rotateOrder]
            negatedRotateOrderIndex = transform.ROTATEORDER_NEGATED.index(negatedRotateOrder)
            cmds.setAttr("{}.{}".format(uppSpline._startTwist, "rotateOrder"), negatedRotateOrderIndex)
        else:
            cmds.connectAttr("{}.outputRotate".format(twistDecompose), "{}.r".format(uppSpline._startTwist))

    def __unifyBendiesInterp(self, uppSpline, lowSpline):
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
            cmds.setAttr("{}.scale_{}".format(lowSpline._group, lowSpline._ikJointList.index(scaleList[i])), value)
