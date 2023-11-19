"""
Arm component
"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import transform
from rigamajig2.maya.components.limb import limb
from rigamajig2.maya.rig import control


class Arm(limb.Limb):
    """
    Arm component (subclass of the limb.limb)
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: component name. To add a side use a side token
        :param list input: list of 4 joints starting with the clavicle and ending with the wrist.
        :param float int size: default size of the controls.
        :param str rigParent: connect the component to a rigParent.
        :param dict ikSpaces: dictionary of key and space for the ik control. formatted as {"attrName": object}
        :param dict pvSpaces: dictionary of key and space for the pv control. formatted as {"attrName": object}
        :param bool useProxyAttrs: use proxy attributes instead of an ikfk control
        """
        # noinspection PyTypeChecker
        if len(input) != 4:
            raise RuntimeError("Input list must have a length of 4")

        super(Arm, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)

    def _initialHierarchy(self):
        """Build the initial hierarchy"""
        super(Arm, self)._initialHierarchy()

        self.limbAutoAim = control.create(
            name=self.name.split("_")[0] + "_ik_autoWrist",
            side=self.side,
            orig=True,
            trs=True,
            hideAttrs=["v", "s", "t"],
            size=self.size,
            color="blue",
            parent=self.limbGimbleIk.name,
            shape="plus",
            position=transform.getTranslate(self.input[3], worldSpace=True),
        )

    def _rigSetup(self):
        """Add the rig setup"""
        super(Arm, self)._rigSetup()

        cmds.delete(cmds.listRelatives(self.ikfk.getIkJointList()[-1], allParents=True, type="orientConstraint"))
        cmds.orientConstraint(self.limbAutoAim.name, self.ikfk.getIkJointList()[-1], maintainOffset=True)

        # Setup the autoAim stuff. This is basically like the interpolation joint stuff.
        attr.createAttr(self.paramsHierarchy, "autoWrist", "float", value=0, minValue=0, maxValue=1)
        control.connectControlVisiblity(self.paramsHierarchy, "autoWrist", self.limbAutoAim.name)

        multMatrix, pickMatrix = transform.connectOffsetParentMatrix(
            self.ikfk.getIkJointList()[1],
            self.limbAutoAim.trs,
            mo=True,
            t=False,
            r=True,
            s=False,
            sh=False,
        )

        blendMatrixNodeName = "{}_{}_blendMatrix".format(self.ikfk.getIkJointList()[2], self.limbAutoAim.trs)
        blendMatrix = cmds.createNode("blendMatrix", name=blendMatrixNodeName)
        cmds.connectAttr(
            "{}.matrixSum".format(multMatrix),
            "{}.target[0].targetMatrix".format(blendMatrix),
        )
        cmds.connectAttr(
            "{}.outputMatrix".format(blendMatrix),
            "{}.inputMatrix".format(pickMatrix),
            force=True,
        )

        # connect the node to the control
        cmds.connectAttr(
            "{}.{}".format(self.paramsHierarchy, "autoWrist"),
            "{}.envelope".format(blendMatrix),
        )

    def _setupAnimAttrs(self):
        # specific controls not affected by userProxy
        attr.addSeparator(self.limbIk.name, "----")
        attr.driveAttribute("autoWrist", self.paramsHierarchy, self.limbIk.name)
        super(Arm, self)._setupAnimAttrs()

    def _postRigSetup(self):
        """Connect the blend chain to the bind chain"""
        super(Arm, self)._postRigSetup()

    def _connect(self):
        """Create the connection"""
        super(Arm, self)._connect()

    def _finalize(self):
        """Lock some attributes we dont want to see"""
        super(Arm, self)._finalize()
