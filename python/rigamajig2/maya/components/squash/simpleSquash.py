"""
squash component
"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import joint
from rigamajig2.maya import mathUtils
from rigamajig2.maya import node
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.shared import common


class SimpleSquash(base.BaseComponent):
    """
    Squash component.
    This is a simple squash component made of a single joint that will scale
    based on the distance between the two end controls.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (39, 189, 46)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: name of the components
        :param list input:  Single input joint
        :param float int size: default size of the controls:
        :param bool addFKSpace: add a world/local space switch to the base of the fk chain
        :param str rigParent: node to parent to connect the component to in the heirarchy
        """
        super(SimpleSquash, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        # initialize cmpt settings.
        self.defineParameter(parameter="startControlName", value=f"{self.name}Start", dataType="string")
        self.defineParameter(parameter="endControlName", value=f"{self.name}End", dataType="string")

        # noinspection PyTypeChecker
        if len(self.input) != 1:
            raise RuntimeError("Input list must have a length of 1")

    def _createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name="{}_guide".format(self.name))

        pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        rot = cmds.xform(self.input[0], q=True, ws=True, ro=True)

        startPos = mathUtils.addVector(pos, [0, 5, 0])
        endPos = mathUtils.addVector(pos, [0, -5, 0])
        self.startGuide = control.createGuide(
            self.name + "_start", side=self.side, parent=self.guidesHierarchy, position=startPos, rotation=rot
        )
        self.endGuide = control.createGuide(
            self.name + "_end", side=self.side, parent=self.guidesHierarchy, position=endPos, rotation=rot
        )

    def _initialHierarchy(self):
        """Build the initial hirarchy"""
        super(SimpleSquash, self)._initialHierarchy()

        self.squashStart = control.createAtObject(
            self.startControlName,
            self.side,
            hideAttrs=["r", "s", "v"],
            size=self.size,
            color="yellow",
            parent=self.controlHierarchy,
            shape="pyramid",
            shapeAim="x",
            xformObj=self.startGuide,
        )
        self.squashEnd = control.createAtObject(
            self.endControlName,
            self.side,
            hideAttrs=["r", "s", "v"],
            size=self.size,
            color="yellow",
            parent=self.controlHierarchy,
            shape="pyramid",
            shapeAim="x",
            xformObj=self.endGuide,
        )

        self.controlers = [self.squashStart.name, self.squashEnd.name]

    def _rigSetup(self):
        """Add the rig setup"""
        self.ikHierarchy = cmds.createNode("transform", n=self.name + "_ik", parent=self.rootHierarchy)

        startJoint = cmds.createNode("joint", n="{}_start_tgt".format(self.name), p=self.ikHierarchy)
        squashJoint = cmds.createNode("joint", n="{}_squash_jnt".format(self.name), p=startJoint)
        endJoint = cmds.createNode("joint", n="{}_end_tgt".format(self.name), p=startJoint)

        transform.matchTransform(self.startGuide, startJoint)
        transform.matchTransform(self.endGuide, endJoint)

        # add parameters
        volumeFactorAttr = attr.createAttr(
            self.paramsHierarchy, "volumeFactor", "float", value=1, minValue=0, maxValue=10
        )

        # orient the joints
        for jnt in [startJoint, endJoint, squashJoint]:
            transform.matchRotate(self.input[0], jnt)

        joint.toOrientation([startJoint, endJoint, squashJoint])

        # create an ik handle to control the angle
        self.ikHandle, self.effector = cmds.ikHandle(sj=startJoint, ee=endJoint, sol="ikSCsolver")
        cmds.parent(self.ikHandle, self.ikHierarchy)

        # connect the ik handle
        transform.connectOffsetParentMatrix(self.squashEnd.name, self.ikHandle)
        transform.connectOffsetParentMatrix(self.squashStart.name, startJoint)

        # get the distance
        dcmp = node.decomposeMatrix("{}.worldMatrix".format(self.rootHierarchy), name="{}_scale".format(self.name))
        distance = node.distance(self.squashStart.name, self.squashEnd.name, name="{}_stretch".format(self.name))
        distanceFloat = mathUtils.distanceNodes(self.squashStart.name, self.squashEnd.name)

        normalizedDistance = node.multiplyDivide(
            "{}.distance".format(distance),
            "{}.outputScale".format(dcmp),
            operation="div",
            name="{}_normScale".format(self.name),
        )

        # set the translation to be half of the distance
        aimAxis = transform.getAimAxis(startJoint, allowNegative=True)
        posFactor = 0.5
        if "-" in aimAxis:
            posFactor = -0.5

        midTrs = node.multDoubleLinear(
            "{}.outputX".format(normalizedDistance),
            posFactor,
            output="{}.t{}".format(squashJoint, aimAxis[-1]),
            name="{}_midPos".format(self.name),
        )

        # build the stretch and squash
        stretchMult = node.multiplyDivide(
            "{}.outputX".format(normalizedDistance),
            [distanceFloat, 1, 1],
            operation="div",
            name="{}_stretch".format(self.name),
            output="{}.s{}".format(squashJoint, aimAxis[-1]),
        )

        volumeLossPercent = node.multDoubleLinear(-0.666, volumeFactorAttr, name="{}_volume".format(self.name))
        volumePower = node.multiplyDivide(
            "{}.outputX".format(stretchMult),
            "{}.output".format(volumeLossPercent),
            operation="pow",
            name="{}_volume".format(self.name),
        )

        for axis in [x for x in "xyz" if x != aimAxis[-1]]:
            cmds.connectAttr("{}.outputX".format(volumePower), "{}.s{}".format(squashJoint, axis))

        # connect the squash joint to the bind joint
        joint.connectChains(squashJoint, self.input[0])

        # cleanup the rig
        joint.hideJoints([startJoint, endJoint, squashJoint])
        cmds.setAttr("{}.v".format(self.ikHandle), 0)

    def _connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(self.rigParent, self.squashStart.orig, mo=True)
            transform.connectOffsetParentMatrix(self.rigParent, self.squashEnd.orig, mo=True)

    def _setupAnimAttrs(self):
        attr.addSeparator(self.squashEnd.name, "----")
        attr.driveAttribute("volumeFactor", self.paramsHierarchy, self.squashEnd.name)
