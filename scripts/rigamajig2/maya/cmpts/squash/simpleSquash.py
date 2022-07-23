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
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input=[], size=1, useProxyAttrs=True, rigParent=str()):
        """
        Squash component.
        This is a simple squash component made of a single joint.

        Important note: the guides will control the placement of this components input!

        :param name: name of the components
        :type name: str
        :param input:  Single input joint
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param addFKSpace: add a world/local space switch to the base of the fk chain
        :type addFKSpace: bool
        :param rigParent: node to parent to connect the component to in the heirarchy
        :type rigParent: str
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
        self.guides_hrc = cmds.createNode("transform", name='{}_guide'.format(self.name))

        pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        rot = cmds.xform(self.input[0], q=True, ws=True, ro=True)
        self.start_guide = rig_control.createGuide(self.name + "_start", side=self.side, parent=self.guides_hrc,
                                                   position=pos, rotation=rot)
        self.end_guide = rig_control.createGuide(self.name + "_end", side=self.side, parent=self.guides_hrc,
                                                 position=pos, rotation=rot)

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(SimpleSquash, self).initalHierachy()

        self.squash_start = rig_control.createAtObject(self.startControlName, self.side,
                                                       hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                                       parent=self.control_hrc, shape='pyramid', shapeAim='x',
                                                       xformObj=self.start_guide)
        self.squash_end = rig_control.createAtObject(self.endControlName, self.side,
                                                     hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                                     parent=self.control_hrc, shape='pyramid', shapeAim='x',
                                                     xformObj=self.end_guide)

        self.controlers = [self.squash_start.name, self.squash_end.name]

    def rigSetup(self):
        """Add the rig setup"""
        self.ik_hrc = cmds.createNode('transform', n=self.name + '_ik', parent=self.root_hrc)

        start_jnt = cmds.createNode("joint", n="{}_start_tgt".format(self.name), p=self.ik_hrc)
        squash_jnt = cmds.createNode("joint", n="{}_squash_jnt".format(self.name), p=start_jnt)
        end_jnt = cmds.createNode("joint", n="{}_end_tgt".format(self.name), p=start_jnt)

        rig_transform.matchTransform(self.start_guide, start_jnt)
        rig_transform.matchTransform(self.end_guide, end_jnt)

        # add parameters
        volumeFactorAttr = rig_attr.createAttr(self.params_hrc, "volumeFactor", "float", value=1, minValue=0, maxValue=10)

        # orient the joints
        for jnt in [start_jnt, end_jnt, squash_jnt]:
            rig_transform.matchRotate(self.input[0], jnt)

        joint.toOrientation([start_jnt, end_jnt, squash_jnt])

        # create an ik handle to control the angle
        self.ikHandle, self.effector = cmds.ikHandle(sj=start_jnt, ee=end_jnt, sol='ikSCsolver')
        cmds.parent(self.ikHandle, self.ik_hrc)

        # connect the ik handle
        rig_transform.connectOffsetParentMatrix(self.squash_end.name, self.ikHandle)
        rig_transform.connectOffsetParentMatrix(self.squash_start.name, start_jnt)

        # get the distance
        dcmp = node.decomposeMatrix("{}.worldMatrix".format(self.root_hrc), name='{}_scale'.format(self.name))
        distance = node.distance(self.squash_start.name, self.squash_end.name, name='{}_stretch'.format(self.name))
        dist_float = mathUtils.distanceNodes(self.squash_start.name, self.squash_end.name)

        normalized_distance = node.multiplyDivide("{}.distance".format(distance), "{}.outputScale".format(dcmp),
                                                  operation='div', name="{}_normScale".format(self.name))

        # set the translation to be half of the distance
        aim_axis = rig_transform.getAimAxis(start_jnt, allowNegative=True)
        pos_factor = 0.5
        if "-" in aim_axis:
            pos_factor = -0.5

        mid_trs = node.multDoubleLinear("{}.outputX".format(normalized_distance), pos_factor,
                                        output="{}.t{}".format(squash_jnt, aim_axis[-1]),
                                        name="{}_midPos".format(self.name))

        # build the stretch and squash
        stretch_mult = node.multiplyDivide("{}.outputX".format(normalized_distance), [dist_float, 1, 1],
                                           operation='div',
                                           name="{}_stretch".format(self.name),
                                           output="{}.s{}".format(squash_jnt, aim_axis[-1]))

        volumeLoss_mdl = node.multDoubleLinear(-0.666, volumeFactorAttr, name="{}_volume".format(self.name))
        volume_power = node.multiplyDivide("{}.outputX".format(stretch_mult), "{}.output".format(volumeLoss_mdl),
                                           operation="pow", name="{}_volume".format(self.name))

        for axis in [x for x in 'xyz' if x != aim_axis[-1]]:
            cmds.connectAttr("{}.outputX".format(volume_power), "{}.s{}".format(squash_jnt, axis))

        # connect the squash joint to the bind joint
        joint.connectChains(squash_jnt, self.input[0])

        # cleanup the rig
        joint.hideJoints([start_jnt, end_jnt, squash_jnt])
        cmds.setAttr("{}.v".format(self.ikHandle), 0)

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.squash_start.orig, mo=True)
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.squash_end.orig, mo=True)

    def setupAnimAttrs(self):
        if self.useProxyAttrs:
            for control in self.controlers:
                rig_attr.addSeparator(control, '----')
            rig_attr.createProxy('{}.{}'.format(self.params_hrc, 'volumeFactor'), self.controlers)
        else:
            rig_attr.addSeparator(self.squash_end.name, '----')
            rig_attr.driveAttribute('volumeFactor', self.params_hrc, self.squash_end.name)

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=4):
        import rigamajig2.maya.naming as naming

        name = name or 'squash'
        jnt = cmds.createNode("joint", name=name)

        return [jnt]