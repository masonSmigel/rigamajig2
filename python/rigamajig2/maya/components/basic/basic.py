"""
basic component
"""
import maya.cmds as cmds

from rigamajig2.maya import joint
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import spaces
from rigamajig2.shared import common


class Basic(base.BaseComponent):
    """
    Single control component
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (204, 194, 109)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param name: Component name. To add a side use a side token
        :param input: Single input joint
        :param size:  Default size of the controls.
        :param spacesGrp: add a spaces group
        :param trsGrp: add a trs group
        :param sdkGrp: add a sdk group
        :param addBpm: add an associated bind pre matrix joint to the components skin joint.
        :param rigParent:  Connect the component to a rigParent.
        :param controlShape: Control shape to apply. Default: "cube"
        :param worldOrient: Orient the control to the world. Default: False
        :param spaceType: Control the type of space switch added. Value values are "orient" or "parent"
        """
        super(Basic, self).__init__(
            name, input, size=size, rigParent=rigParent, componentTag=componentTag
        )
        self.side = common.getSide(self.name)

        self.controlName = [x.split("_")[0] for x in self.input][0]
        self.controlShape = "sphere"
        self.worldOrient = False
        self.addSpaces = False
        self.spaceType = "orient"
        self.addTrs = False
        self.addSdk = False
        self.addBpm = False

        self.defineParameter(
            parameter="controlName", value=self.controlName, dataType="string"
        )
        self.defineParameter(
            parameter="controlShape", value=self.controlShape, dataType="string"
        )
        self.defineParameter(
            parameter="worldOrient", value=self.worldOrient, dataType="bool"
        )
        self.defineParameter(
            parameter="addSpaces", value=self.addSpaces, dataType="bool"
        )
        self.defineParameter(
            parameter="spaceType", value=self.spaceType, dataType="string"
        )
        self.defineParameter(parameter="addTrs", value=self.addTrs, dataType="bool")
        self.defineParameter(parameter="addSdk", value=self.addSdk, dataType="bool")
        self.defineParameter(parameter="addBpm", value=self.addBpm, dataType="bool")

    def _initialHierarchy(self):
        super(Basic, self)._initialHierarchy()

        self.control = control.create(
            self.controlName,
            self.side,
            spaces=self.addSpaces,
            trs=self.addTrs,
            sdk=self.addSdk,
            color="blue",
            parent=self.controlHierarchy,
            shape=self.controlShape,
        )

        transform.matchTranslate(self.input[0], self.control.orig)
        if not self.worldOrient:
            transform.matchRotate(self.input[0], self.control.orig)

    def _rigSetup(self):
        if self.worldOrient:
            if self.side:
                name = "{}_{}_trs".format(self.controlName, self.side)
            else:
                name = "{}_trs".format(self.controlName)

            offset = cmds.createNode("transform", name=name)
            transform.matchTransform(self.input[0], offset)
            cmds.parent(offset, self.control.name)
            joint.connectChains(offset, self.input[0])
        else:
            joint.connectChains(self.control.name, self.input[0])

        if self.addBpm:
            # if needed we will add a bind pre matrix joint.
            self.bpmHierarchy = cmds.createNode(
                "transform",
                name="{}_bpm_hrc".format(self.name),
                parent=self.rootHierarchy,
            )

            bpmJointName = [x.rsplit("_", 1)[0] + "_bpm" for x in self.input]
            self.bpmJointList = joint.duplicateChain(
                self.input, parent=self.bpmHierarchy, names=bpmJointName
            )

            joint.hideJoints(self.bpmJointList)

    def _connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(
                self.rigParent, self.control.orig, mo=True
            )

        if self.addSpaces:
            spaces.create(
                self.control.spaces, self.control.name, parent=self.spacesHierarchy
            )
            spaces.addSpace(
                self.control.spaces,
                ["trs_motion"],
                nameList=["world"],
                constraintType=self.spaceType,
            )

        if self.addBpm:
            transform.connectOffsetParentMatrix(
                self.rigParent, self.bpmJointList[0], mo=True
            )
