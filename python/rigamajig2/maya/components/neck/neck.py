"""
neck component
"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import hierarchy
from rigamajig2.maya import joint
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import live
from rigamajig2.maya.rig import spaces
from rigamajig2.maya.rig import spline
from rigamajig2.shared import common

HEAD_PERCENT = 0.7


# pylint:disable = too-many-instance-attributes
class Neck(base.BaseComponent):
    """
    Neck component
    The neck has a head and neck controls.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (47, 177, 161)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: name of the component
        :param list input: list of input joints. Starting with the base of the neck and ending with the head.
        :param float int size: default size of the controls.
        :param dict headSpaces: dictionary of key and space for the head control. formated as {"attrName": object}
        :param dict neckSpaces: dictionary of key and space for the neck control. formated as {"attrName": object}
        :param str rigParent: connect the component to a rigParent.
        """

        super(Neck, self).__init__(
            name, input=input, size=size, rigParent=rigParent, componentTag=componentTag
        )
        self.side = common.getSide(self.name)

        self.neckSpaces = {}
        self.headSpaces = {}

        self.neckName = "neck"
        self.headName = "head"

        self.defineParameter(parameter="neckName", value="neck", dataType="string")
        self.defineParameter(parameter="headName", value="head", dataType="string")
        self.defineParameter(parameter="skullName", value="skull", dataType="string")
        self.defineParameter(
            parameter="neckSpaces", value=self.neckSpaces, dataType="dict"
        )
        self.defineParameter(
            parameter="headSpaces", value=self.headSpaces, dataType="dict"
        )

    def _createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode(
            "transform", name="{}_guide".format(self.name)
        )

        neckPos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.neckGuide = control.createGuide(
            self.name + "_neck",
            side=self.side,
            parent=self.guidesHierarchy,
            position=neckPos,
        )
        attr.lockAndHide(self.neckGuide, attr.TRANSLATE + ["v"])

        self.headGuide = control.createGuide(
            self.name + "_head", side=self.side, parent=self.guidesHierarchy
        )
        live.slideBetweenTransforms(
            self.headGuide,
            start=self.input[0],
            end=self.input[-1],
            defaultValue=HEAD_PERCENT,
        )
        attr.lock(self.headGuide, attr.TRANSLATE + ["v"])

        skullPos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.skullGuide = control.createGuide(
            self.name + "_skull",
            side=self.side,
            parent=self.guidesHierarchy,
            position=skullPos,
        )
        attr.lockAndHide(self.skullGuide, attr.TRANSLATE + ["v"])

    def _initialHierarchy(self):
        super(Neck, self)._initialHierarchy()

        self.neck = control.createAtObject(
            name=self.neckName,
            side=self.side,
            spaces=True,
            hideAttrs=["s", "v"],
            size=self.size,
            color="yellow",
            parent=self.controlHierarchy,
            shape="cube",
            shapeAim="x",
            xformObj=self.neckGuide,
        )

        self.head = control.createAtObject(
            name=self.headName,
            side=self.side,
            spaces=True,
            hideAttrs=["v"],
            size=self.size,
            color="yellow",
            parent=self.neck.name,
            shape="cube",
            shapeAim="x",
            xformObj=self.headGuide,
        )

        self.headGimble = control.createAtObject(
            self.headName + "Gimble",
            self.side,
            hideAttrs=["s", "v"],
            size=self.size,
            color="yellow",
            parent=self.head.name,
            shape="cube",
            shapeAim="x",
            xformObj=self.headGuide,
        )

        self.skull = control.createAtObject(
            self.skullName,
            self.side,
            hideAttrs=["v"],
            size=self.size,
            color="yellow",
            parent=self.headGimble.name,
            shape="cube",
            shapeAim="x",
            xformObj=self.skullGuide,
        )

        self.headTanget = control.createAtObject(
            name=self.headName + "Tan",
            side=self.side,
            hideAttrs=["r", "s", "v"],
            size=self.size,
            color="yellow",
            parent=self.headGimble.name,
            shape="diamond",
            shapeAim="x",
            xformObj=self.skullGuide,
        )

        self.neckTanget = control.createAtObject(
            name=self.neckName + "Tan",
            side=self.side,
            hideAttrs=["r", "s", "v"],
            size=self.size,
            color="yellow",
            parent=self.neck.name,
            shape="diamond",
            shapeAim="x",
            xformObj=self.neckGuide,
        )

    def _rigSetup(self):
        """Add the rig setup"""
        # create the spline ik
        self.ikspline = spline.SplineBase(self.input, name=self.name)
        self.ikspline.setGroup(self.name + "_ik")
        self.ikspline.create(clusters=4, params=self.paramsHierarchy)
        cmds.parent(self.ikspline.getGroup(), self.rootHierarchy)

        # connect the volume factor and tangents visability attributes
        attr.addSeparator(self.head.name, "----")
        attr.createAttr(
            self.head.name,
            "volumeFactor",
            attributeType="float",
            value=1,
            minValue=0,
            maxValue=10,
        )
        cmds.connectAttr(
            "{}.volumeFactor".format(self.head.name),
            "{}.volumeFactor".format(self.paramsHierarchy),
        )

        attr.createAttr(
            self.neck.name,
            "tangentVis",
            attributeType="bool",
            value=1,
            channelBox=True,
            keyable=False,
        )
        cmds.connectAttr(
            "{}.tangentVis".format(self.neck.name), "{}.v".format(self.neckTanget.orig)
        )
        transform.matchTransform(self.ikspline.getClusters()[1], self.neckTanget.orig)

        attr.createAttr(
            self.head.name,
            "tangentVis",
            attributeType="bool",
            value=1,
            channelBox=True,
            keyable=False,
        )
        cmds.connectAttr(
            "{}.tangentVis".format(self.head.name), "{}.v".format(self.headTanget.orig)
        )
        transform.matchTransform(self.ikspline.getClusters()[2], self.headTanget.orig)

        # parent clusters to tangent controls
        cmds.parent(self.ikspline.getClusters()[1], self.neckTanget.name)
        cmds.parent(self.ikspline.getClusters()[2], self.headTanget.name)
        cmds.parent(self.ikspline.getClusters()[3], self.headGimble.name)

        # connect the skull to the head joint
        self.skullTrs = hierarchy.create(
            self.skull.name, ["{}_trs".format(self.input[-1])], above=False
        )[0]
        transform.matchTransform(self.input[-1], self.skullTrs)
        # delete exising parent constraint
        cmds.delete(
            cmds.ls(
                cmds.listConnections("{}.tx".format(self.input[-1])),
                type="parentConstraint",
            )
        )
        joint.connectChains(self.skullTrs, self.input[-1])

        # connect the orient constraint to the twist controls
        cmds.orientConstraint(self.neck.name, self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.headGimble.name, self.ikspline._endTwist, mo=True)

        transform.connectOffsetParentMatrix(
            self.neck.name, self.ikspline.getGroup(), mo=True
        )

    def _setupAnimAttrs(self):
        # create a visability control for the ikGimble control
        attr.createAttr(
            self.head.name,
            "gimble",
            attributeType="bool",
            value=0,
            keyable=False,
            channelBox=True,
        )
        control.connectControlVisiblity(
            self.head.name, "gimble", controls=self.headGimble.name
        )

    def _connect(self):
        """Create the connection"""

        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(self.rigParent, self.neck.orig, mo=True)

        spaces.create(self.neck.spaces, self.neck.name, parent=self.spacesHierarchy)
        spaces.create(self.head.spaces, self.head.name, parent=self.spacesHierarchy)

        # if the main control exists connect the world space
        if cmds.objExists("trs_motion"):
            spaces.addSpace(
                self.neck.spaces,
                ["trs_motion"],
                nameList=["world"],
                constraintType="orient",
            )
            spaces.addSpace(
                self.head.spaces,
                ["trs_motion"],
                nameList=["world"],
                constraintType="orient",
            )

        if self.neckSpaces:
            spaces.addSpace(
                self.head.spaces,
                [self.neckSpaces[k] for k in self.neckSpaces.keys()],
                self.neckSpaces.keys(),
                "orient",
            )

        if self.headSpaces:
            spaces.addSpace(
                self.head.spaces,
                [self.headSpaces[k] for k in self.headSpaces.keys()],
                self.headSpaces.keys(),
                "orient",
            )

    def _finalize(self):
        attr.lock(self.ikspline.getGroup(), attr.TRANSFORMS + ["v"])
        attr.lockAndHide(self.paramsHierarchy, attr.TRANSFORMS + ["v"])
