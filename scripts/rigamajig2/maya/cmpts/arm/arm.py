"""
Arm component
"""
# MAYA
import maya.cmds as cmds

import rigamajig2.maya.attr as rig_attr
# RIGAMAJIG
import rigamajig2.maya.cmpts.limb.limb
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.transform as rig_transform


class Arm(rigamajig2.maya.cmpts.limb.limb.Limb):
    """
    Arm component (subclass of the limb.limb)
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
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
            raise RuntimeError('Input list must have a length of 4')

        super(Arm, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)

        self.defineParameter(parameter='limb_autoWristName', value=self.name.split("_")[0] + "_autoWrist",
                             dataType="string")

    def _initialHierarchy(self):
        """Build the initial hierarchy"""
        super(Arm, self)._initialHierarchy()

        self.limbAutoAim = rig_control.create(
            self.limb_autoWristName,
            self.side,
            orig=True,
            trs=True,
            hideAttrs=['v', 's', 't'],
            size=self.size,
            color='blue',
            parent=self.limbGimbleIk.name,
            shape='plus',
            position=cmds.xform(self.input[3], q=True, ws=True, t=True)
        )

    def _rigSetup(self):
        """Add the rig setup"""
        super(Arm, self)._rigSetup()

        cmds.delete(cmds.listRelatives(self.ikfk.getIkJointList()[-1], ad=True, type='orientConstraint'))
        cmds.orientConstraint(self.limbAutoAim.name, self.ikfk.getIkJointList()[-1], mo=True)

        # Setup the autoAim stuff. This is basically like the interpolation joint stuff.
        rig_attr.createAttr(self.paramsHierarchy, "autoWrist", "float", value=0, minValue=0, maxValue=1)
        rig_control.connectControlVisiblity(self.paramsHierarchy, "autoWrist", self.limbAutoAim.name)

        multMatrix, pickMatrix = rig_transform.connectOffsetParentMatrix(self.ikfk.getIkJointList()[1],
                                                                         self.limbAutoAim.trs,
                                                                         mo=True,
                                                                         t=False,
                                                                         r=True,
                                                                         s=False,
                                                                         sh=False)

        blendMatrixNodeName = "{}_{}_blendMatrix".format(self.ikfk.getIkJointList()[2], self.limbAutoAim.trs)
        blendMatrix = cmds.createNode("blendMatrix", n=blendMatrixNodeName)
        cmds.connectAttr("{}.matrixSum".format(multMatrix), "{}.target[0].targetMatrix".format(blendMatrix))
        cmds.connectAttr("{}.outputMatrix".format(blendMatrix), "{}.inputMatrix".format(pickMatrix), f=True)

        # connect the node to the control
        cmds.connectAttr("{}.{}".format(self.paramsHierarchy, "autoWrist"), "{}.envelope".format(blendMatrix))

    def _setupAnimAttrs(self):
        # specific controls not affected by userProxy
        rig_attr.addSeparator(self.limbIk.name, '----')
        rig_attr.driveAttribute('autoWrist', self.paramsHierarchy, self.limbIk.name)
        super(Arm, self)._setupAnimAttrs()

    def _postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        super(Arm, self)._postRigSetup()

    def _connect(self):
        """Create the connection"""
        super(Arm, self)._connect()

    def _finalize(self):
        """ Lock some attributes we dont want to see"""
        super(Arm, self)._finalize()
