"""
main component
"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import meta
from rigamajig2.maya import node
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control

RIG_HRC_NAME = "rig"
BIND_HRC_NAME = "bind"
MOD_HRC_NAME = "model"


class Main(base.BaseComponent):
    """
    Component for the main hierarchy.
    This includes the base heirarchy of the main, model, rig and bind groups as well the global controls.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (48, 150, 225)

    def __init__(self, name, input=None, size=1, rigParent=None, componentTag=None):
        """
        :param name: name of the component
        :param input: inputs to the component. This is ignored in the component but is required for base component.
        :param rigParent:
        """
        super(Main, self).__init__(
            name=name,
            input=input,
            size=size,
            rigParent=rigParent,
            componentTag=componentTag,
        )

    def _initialHierarchy(self):
        """Build the initial hirarchy"""
        self.rootHierarchy = cmds.createNode("transform", name=self.name)
        self.rigHierarchy = cmds.createNode(
            "transform", name=RIG_HRC_NAME, parent=self.rootHierarchy
        )
        self.bindHierarchy = cmds.createNode(
            "transform", name=BIND_HRC_NAME, parent=self.rootHierarchy
        )
        self.modelHierarchy = cmds.createNode(
            "transform", name=MOD_HRC_NAME, parent=self.rootHierarchy
        )

        # Build our controls
        self.trsGlobal = control.create(
            "trs_global",
            orig=False,
            size=self.size * 1.2,
            color="yellow",
            parent=self.rootHierarchy,
        )
        self.trsShot = control.create(
            "trs_shot",
            orig=False,
            size=self.size * 1.1,
            color="lightgreenyellow",
            parent=self.trsGlobal.name,
        )
        self.trsMotion = control.create(
            "trs_motion",
            orig=False,
            size=self.size,
            color="yellowgreen",
            parent=self.trsShot.name,
        )
        # add the trs to the top of our outliner
        cmds.reorder(self.trsGlobal.name, front=True)

    def _rigSetup(self):
        """Add the self.rig setup"""
        # Setup the main scaling
        node.multMatrix(
            [
                self.trsMotion.name + ".matrix",
                self.trsShot.name + ".matrix",
                self.trsGlobal.name + ".matrix",
            ],
            outputs=[self.rigHierarchy, self.bindHierarchy],
            translate=True,
            rotate=True,
            scale=True,
            name="main",
        )

        # turn off inherit transform so we dont get double transformations
        cmds.setAttr("{}.{}".format(self.modelHierarchy, "inheritsTransform"), 0)

        # Add the attribute for model override.
        overrideModelAttr = attr.createEnum(
            self.trsShot.name,
            longName="modDisplay",
            enum=["normal", "template", "reference"],
            value=0,
            keyable=False,
            channelBox=True,
        )

        cmds.setAttr(self.modelHierarchy + ".overrideEnabled", 1)
        cmds.connectAttr(
            overrideModelAttr, self.modelHierarchy + ".overrideDisplayType"
        )

        # create some attributes for the geo and rig visablity
        modVisAttr = attr.createAttr(
            self.rootHierarchy,
            longName="model",
            attributeType="bool",
            value=True,
            keyable=True,
            channelBox=True,
        )

        rigVisAttr = attr.createAttr(
            self.rootHierarchy,
            longName="rig",
            attributeType="bool",
            value=True,
            keyable=True,
            channelBox=True,
        )

        bindVisAttr = attr.createAttr(
            self.rootHierarchy,
            longName="bind",
            attributeType="bool",
            value=True,
            keyable=True,
            channelBox=True,
        )

        cmds.connectAttr(modVisAttr, "{}.v".format(self.modelHierarchy))
        cmds.connectAttr(rigVisAttr, "{}.v".format(self.rigHierarchy))
        cmds.connectAttr(bindVisAttr, "{}.v".format(self.bindHierarchy))

    def _finalize(self):
        attr.lockAndHide(self.rootHierarchy, attr.TRANSFORMS + ["v"])
        attr.lock(self.rigHierarchy, attr.TRANSFORMS)
        attr.lock(self.bindHierarchy, attr.TRANSFORMS)
        attr.lock(self.modelHierarchy, attr.TRANSFORMS)

        self.addMetadataToMain()

    def deleteSetup(self):
        """Delete the component setup"""
        if cmds.objExists(BIND_HRC_NAME):
            skeletonChildren = cmds.listRelatives(BIND_HRC_NAME, children=True)
            if skeletonChildren:
                cmds.parent(skeletonChildren, world=True)

        if cmds.objExists(RIG_HRC_NAME):
            rigChildren = cmds.listRelatives(RIG_HRC_NAME, children=True)
            if rigChildren:
                cmds.parent(rigChildren, world=True)

        if cmds.objExists(MOD_HRC_NAME):
            modelChildred = cmds.listRelatives(MOD_HRC_NAME, children=True)
            if modelChildred:
                cmds.parent(modelChildred, world=True)

        super(Main, self).deleteSetup()

    def addMetadataToMain(self):
        """
        Add some Meta data to the main group. This data includes:
        - The version of rigamajig used
        - The user who created the rig
        - The data and time at which the rig was created
        """
        import rigamajig2
        import getpass
        from time import gmtime, strftime

        meta.tag(self.rootHierarchy, "__rig_root__")

        attr.createAttr(
            self.rootHierarchy,
            "__rigamajigVersion__",
            "string",
            value=rigamajig2.version,
            keyable=False,
            locked=True,
        )
        attr.createAttr(
            self.rootHierarchy,
            "__creationUser__",
            "string",
            value=getpass.getuser(),
            keyable=False,
            locked=True,
        )
        attr.createAttr(
            self.rootHierarchy,
            "__creationDate__",
            "string",
            value=strftime("%Y-%m-%d %H:%M:%S", gmtime()),
            keyable=False,
            locked=True,
        )
