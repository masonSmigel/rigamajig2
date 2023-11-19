"""
COG component
"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import constrain
from rigamajig2.maya import hierarchy
from rigamajig2.maya import joint
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control


class Cog(base.BaseComponent):
    """
    Center of gravity (COG) component.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (243, 115, 58)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: name of the components
        :param list input: list of one joint. typically the hips.
        :param float int size: default size of the controls:
        :param str rigParent:  Connect the component to a rigParent.
        :param bool bindToInput: connect the output position of the COG component to the input.
                            This should be False in most rigs as the hips will be controlled by the spine.
        """
        super(Cog, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)

        self.bindToInput = False
        self.cogControlShape = "cube"
        self.cogName = "cog"

        self.defineParameter(parameter="bindToInput", value=self.bindToInput, dataType="bool")
        self.defineParameter(parameter="cogControlShape", value=self.cogControlShape, dataType="string")
        self.defineParameter(parameter="cogName", value=self.cogName, dataType="string")

    def _initialHierarchy(self):
        """Build the initial hierarchy"""
        super(Cog, self)._initialHierarchy()

        if len(self.input) >= 1:
            pos = transform.getTranslate(self.input[0], worldSpace=True)
        else:
            pos = (0, 0, 0)
        self.cog = control.create(
            name=self.cogName,
            hideAttrs=["s", "v"],
            size=self.size,
            color="yellow",
            parent=self.controlHierarchy,
            shape=self.cogControlShape,
            shapeAim="x",
            position=pos,
        )
        self.cogPivot = control.create(
            name=self.cogName + "Pivot",
            hideAttrs=["s", "v"],
            size=self.size,
            color="yellow",
            parent=self.cog.name,
            shape="sphere",
            shapeAim="x",
            position=pos,
        )
        self.cogGimble = control.create(
            name=self.cogName + "Gimble",
            hideAttrs=["s", "v"],
            size=self.size,
            color="yellow",
            parent=self.cog.name,
            shape=self.cogControlShape,
            shapeAim="x",
            position=pos,
        )
        self.cogGimble.addTrs("neg")

    def _rigSetup(self):
        # create the pivot negate

        negateOffsetName = self.cogGimble.trs + "_trs"
        negativeTrs = hierarchy.create(self.cogGimble.trs, [negateOffsetName], above=True, matchTransform=True)[0]
        constrain.parentConstraint(driver=self.cogPivot.name, driven=negativeTrs)

        constrain.negate(self.cogPivot.name, self.cogGimble.trs, t=True)
        if self.bindToInput and len(self.input) >= 1:
            self.inputTrs = hierarchy.create(self.cogGimble.name, ["{}_trs".format(self.input[0])], above=False)[0]
            transform.matchTransform(self.input[0], self.inputTrs)
            joint.connectChains(self.inputTrs, self.input[0])

    def _setupAnimAttrs(self):
        """setup the animation attributes"""

        # create a visibility control for the ikGimble control
        attr.addSeparator(self.cog.name, "----")

        attr.createAttr(self.cog.name, "movablePivot", attributeType="bool", value=0, keyable=False, channelBox=True)
        control.connectControlVisiblity(self.cog.name, "movablePivot", controls=self.cogPivot.name)

        attr.createAttr(self.cog.name, "gimble", attributeType="bool", value=0, keyable=False, channelBox=True)
        control.connectControlVisiblity(self.cog.name, "gimble", controls=self.cogGimble.name)

    def _connect(self):
        if cmds.objExists(self.rigParent):
            cmds.parentConstraint(self.rigParent, self.cog[0], maintainOffset=True)
