"""
squash component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.joint as joint
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.node as node
import rigamajig2.maya.mathUtils as mathUtils


class SimpleSquash(rigamajig2.maya.cmpts.base.Base):
    """
    Squash component.
    This is a simple squash component made of a single joint that will scale
    based on the distance between the two end controls.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    UI_COLOR = (39, 189, 46)

    def __init__(self, name, input, size=1, useProxyAttrs=True, rigParent=str()):
        """
        :param str name: name of the components
        :param list input:  Single input joint
        :param float int size: default size of the controls:
        :param bool addFKSpace: add a world/local space switch to the base of the fk chain
        :param str rigParent: node to parent to connect the component to in the heirarchy
        """
        super(SimpleSquash, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['component_side'] = self.side
        # initalize cmpt settings.
        self.cmptSettings['useProxyAttrs'] = useProxyAttrs
        self.cmptSettings['startControlName'] = "{}Start".format(self.name)
        self.cmptSettings['endControlName'] = "{}End".format(self.name)

        # noinspection PyTypeChecker
        if len(self.input) != 1:
            raise RuntimeError('Input list must have a length of 1')

    def createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        rot = cmds.xform(self.input[0], q=True, ws=True, ro=True)

        startPos = mathUtils.addVector(pos, [0, 5, 0])
        endPos = mathUtils.addVector(pos, [0, -5, 0])
        self.startGuide = rig_control.createGuide(self.name + "_start",
                                                  side=self.side,
                                                  parent=self.guidesHierarchy,
                                                  position=startPos,
                                                  rotation=rot
                                                  )
        self.endGuide = rig_control.createGuide(self.name + "_end",
                                                side=self.side,
                                                parent=self.guidesHierarchy,
                                                position=endPos,
                                                rotation=rot
                                                )

    def initialHierarchy(self):
        """Build the initial hirarchy"""
        super(SimpleSquash, self).initialHierarchy()

        self.squashStart = rig_control.createAtObject(self.startControlName, self.side,
                                                      hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                                      parent=self.controlHierarchy, shape='pyramid', shapeAim='x',
                                                      xformObj=self.startGuide)
        self.squashEnd = rig_control.createAtObject(self.endControlName, self.side,
                                                    hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                                    parent=self.controlHierarchy, shape='pyramid', shapeAim='x',
                                                    xformObj=self.endGuide)

        self.controlers = [self.squashStart.name, self.squashEnd.name]

    def rigSetup(self):
        """Add the rig setup"""
        self.ikHierarchy = cmds.createNode('transform', n=self.name + '_ik', parent=self.rootHierarchy)

        startJoint = cmds.createNode("joint", n="{}_start_tgt".format(self.name), p=self.ikHierarchy)
        squashJoint = cmds.createNode("joint", n="{}_squash_jnt".format(self.name), p=startJoint)
        endJoint = cmds.createNode("joint", n="{}_end_tgt".format(self.name), p=startJoint)

        rig_transform.matchTransform(self.startGuide, startJoint)
        rig_transform.matchTransform(self.endGuide, endJoint)

        # add parameters
        volumeFactorAttr = rig_attr.createAttr(self.paramsHierarchy, "volumeFactor", "float", value=1, minValue=0,
                                               maxValue=10)

        # orient the joints
        for jnt in [startJoint, endJoint, squashJoint]:
            rig_transform.matchRotate(self.input[0], jnt)

        joint.toOrientation([startJoint, endJoint, squashJoint])

        # create an ik handle to control the angle
        self.ikHandle, self.effector = cmds.ikHandle(sj=startJoint, ee=endJoint, sol='ikSCsolver')
        cmds.parent(self.ikHandle, self.ikHierarchy)

        # connect the ik handle
        rig_transform.connectOffsetParentMatrix(self.squashEnd.name, self.ikHandle)
        rig_transform.connectOffsetParentMatrix(self.squashStart.name, startJoint)

        # get the distance
        dcmp = node.decomposeMatrix("{}.worldMatrix".format(self.rootHierarchy), name='{}_scale'.format(self.name))
        distance = node.distance(self.squashStart.name, self.squashEnd.name, name='{}_stretch'.format(self.name))
        distanceFloat = mathUtils.distanceNodes(self.squashStart.name, self.squashEnd.name)

        normalizedDistance = node.multiplyDivide("{}.distance".format(distance), "{}.outputScale".format(dcmp),
                                                 operation='div', name="{}_normScale".format(self.name))

        # set the translation to be half of the distance
        aimAxis = rig_transform.getAimAxis(startJoint, allowNegative=True)
        posFactor = 0.5
        if "-" in aimAxis:
            posFactor = -0.5

        midTrs = node.multDoubleLinear("{}.outputX".format(normalizedDistance), posFactor,
                                       output="{}.t{}".format(squashJoint, aimAxis[-1]),
                                       name="{}_midPos".format(self.name))

        # build the stretch and squash
        stretchMult = node.multiplyDivide("{}.outputX".format(normalizedDistance), [distanceFloat, 1, 1],
                                          operation='div',
                                          name="{}_stretch".format(self.name),
                                          output="{}.s{}".format(squashJoint, aimAxis[-1]))

        volumeLossPercent = node.multDoubleLinear(-0.666, volumeFactorAttr, name="{}_volume".format(self.name))
        volumePower = node.multiplyDivide("{}.outputX".format(stretchMult), "{}.output".format(volumeLossPercent),
                                          operation="pow", name="{}_volume".format(self.name))

        for axis in [x for x in 'xyz' if x != aimAxis[-1]]:
            cmds.connectAttr("{}.outputX".format(volumePower), "{}.s{}".format(squashJoint, axis))

        # connect the squash joint to the bind joint
        joint.connectChains(squashJoint, self.input[0])

        # cleanup the rig
        joint.hideJoints([startJoint, endJoint, squashJoint])
        cmds.setAttr("{}.v".format(self.ikHandle), 0)

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.squashStart.orig, mo=True)
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.squashEnd.orig, mo=True)

    def setupAnimAttrs(self):
        if self.useProxyAttrs:
            for control in self.controlers:
                rig_attr.addSeparator(control, '----')
            rig_attr.createProxy('{}.{}'.format(self.paramsHierarchy, 'volumeFactor'), self.controlers)
        else:
            rig_attr.addSeparator(self.squashEnd.name, '----')
            rig_attr.driveAttribute('volumeFactor', self.paramsHierarchy, self.squashEnd.name)

