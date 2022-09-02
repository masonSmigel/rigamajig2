"""
spine component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.live as live
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.spline as spline
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.constrain as constrain
import rigamajig2.maya.node as node
import rigamajig2.shared.common as common
import rigamajig2.maya.hierarchy as hierarchy
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.joint as joint
import rigamajig2.maya.meta as meta

HIPS_PERCENT = 0.33
SPINE_PERCENT = 0.5
TORSO_PERCENT = 0.15


class Spine(rigamajig2.maya.cmpts.base.Base):
    """
    Spine component.
    The spine containts the hipSwivel, torso and chest controls.
    Based on an IKSpline to create a smooth movement in the spine
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str(), addSpineMid=False, chestSpaces=None):
        """
        :param str name: name of the component
        :param list input: list of input joints. Starting with the base of the neck and ending with the head.
        :param float int size: default size of the controls.
        :param str rigParent: connect the component to a rigParent.
        """

        if chestSpaces is None:
            chestSpaces = dict()

        super(Spine, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['addSpineMid'] = addSpineMid
        self.cmptSettings['hipsSwing_name'] = 'hip_swing'
        self.cmptSettings['torso_name'] = 'torso'
        self.cmptSettings['spineMid_name'] = 'spineMid'
        self.cmptSettings['chest_name'] = 'chest'
        self.cmptSettings['chestTop_name'] = 'chestTop'
        self.cmptSettings['hipTanget_name'] = 'hipTan'
        self.cmptSettings['chestTanget_name'] = 'chestTan'

        self.cmptSettings['chestSpaces'] = chestSpaces

    def createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self.hipsSwivelGuide = rig_control.createGuide(
            self.name + "_hipSwivel",
            side=self.side,
            parent=self.guidesHierarchy)
        live.slideBetweenTransforms(self.hipsSwivelGuide, self.input[1], self.input[-2], defaultValue=HIPS_PERCENT)

        self.torsoGuide = rig_control.createGuide(
            self.name + "_torso",
            side=self.side,
            parent=self.guidesHierarchy)

        # setup the slider for the guide
        live.slideBetweenTransforms(self.torsoGuide, self.input[1], self.input[-2], defaultValue=TORSO_PERCENT)

        self.chestGuide = rig_control.createGuide(
            self.name + "_chest",
            side=self.side,
            parent=self.guidesHierarchy,
            position=cmds.xform(self.input[-2], q=True, ws=True, t=True))

        self.chestTopGuide = rig_control.createGuide(
            self.name + "_chestTop",
            side=self.side,
            parent=self.guidesHierarchy,
            position=cmds.xform(self.input[-1], q=True, ws=True, t=True))

        if self.addSpineMid:
            self.spineMidGuide = rig_control.createGuide(
                self.name + "_spineMid",
                side=self.side,
                parent=self.guidesHierarchy,
                position=cmds.xform(self.input[-2], q=True, ws=True, t=True)
                )

            live.slideBetweenTransforms(self.spineMidGuide, self.input[1], self.input[-2], defaultValue=SPINE_PERCENT)

        for guide in [self.hipsSwivelGuide, self.torsoGuide, self.chestGuide]:
            rig_attr.lock(guide, rig_attr.TRANSLATE)

        rig_attr.lockAndHide(self.chestTopGuide, rig_attr.TRANSLATE + ['v'])

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Spine, self).initalHierachy()

        # build the hips swivel control
        hipPos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.hipSwing = rig_control.createAtObject(
            name=self.hipsSwing_name,
            side=self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.controlHierarchy,
            shape='cube',
            shapeAim='x',
            xformObj=self.hipsSwivelGuide
            )

        # build the torso control
        self.torso = rig_control.createAtObject(
            name=self.torso_name,
            side=self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.controlHierarchy,
            shape='cube',
            shapeAim='x',
            xformObj=self.torsoGuide
            )

        # if we want to add a spineMid then add it between the chest and torso
        if self.addSpineMid:
            self.spineMid = rig_control.createAtObject(
                name=self.spineMid_name,
                side=self.side,
                hideAttrs=['s', 'v'],
                size=self.size,
                color='yellow',
                parent=self.torso.name,
                shape='cube',
                shapeAim='x',
                xformObj=self.spineMidGuide
                )

        # build the chest control
        self.chest = rig_control.createAtObject(
            name=self.chest_name,
            side=self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.spineMid.name if self.addSpineMid else self.torso.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.chestGuide
            )
        self.chest.addTrs("neg")

        chestPos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.chestTop = rig_control.createAtObject(
            name=self.chestTop_name,
            side=self.side,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.chest.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.chestTopGuide
            )
        self.chest.addTrs("len")

        self.hipTanget = rig_control.create(
            name=self.hipTanget_name,
            side=self.side,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='yellow',
            parent=self.hipSwing.name,
            shape='diamond',
            shapeAim='x',
            position=hipPos
            )

        self.chestTanget = rig_control.create(
            name=self.chestTanget_name,
            side=self.side,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='yellow',
            parent=self.chest.name,
            shape='diamond',
            shapeAim='x',
            position=chestPos
            )

    def rigSetup(self):
        """Add the rig setup"""

        # the spline might shift slightly when the ik is created.
        # If built first this could affect the input of joints downstream
        # To comabt this  first we'll use the last joint to anchor the end of the spine to the chest top control
        self.chestTopTrs = hierarchy.create(self.chestTop.name, ['{}_trs'.format(self.input[0])], above=False)[0]
        rig_transform.matchTransform(self.input[-1], self.chestTopTrs)

        joint.connectChains(self.chestTopTrs, self.input[-1])

        # create the spline ik
        self.ikspline = spline.SplineBase(self.input[1:-1], name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=4, params=self.paramsHierarchy)
        cmds.parent(self.ikspline.getGroup(), self.rootHierarchy)

        # setup the hipSwivel
        self.hipSwingTrs = hierarchy.create(self.hipSwing.name, ['{}_trs'.format(self.input[0])], above=False)[0]
        rig_transform.matchTransform(self.input[0], self.hipSwingTrs)
        joint.connectChains(self.hipSwingTrs, self.input[0])

        # create  attributes
        rig_attr.addSeparator(self.chest.name, '----')
        rig_attr.addSeparator(self.hipSwing.name, '----')
        rig_attr.createAttr(self.chest.name, 'pivotHeight', attributeType='float', value=3.5, minValue=0, maxValue=10)
        # connect the some attributes
        rig_attr.createAttr(self.chest.name, 'volumeFactor', attributeType='float', value=1, minValue=0, maxValue=10)
        cmds.connectAttr("{}.volumeFactor".format(self.chest.name), "{}.volumeFactor".format(self.paramsHierarchy))

        # connect the tangets to the visablity
        rig_attr.createAttr(self.chest.name, 'tangentVis', attributeType='bool', value=1, channelBox=True,
                            keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.chest.name), "{}.v".format(self.chestTanget.orig))
        rig_attr.createAttr(self.hipSwing.name, 'tangentVis', attributeType='bool', value=1, channelBox=True,
                            keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.hipSwing.name), "{}.v".format(self.hipTanget.orig))

        # create the chest piviot offset
        axis = rig_transform.getAimAxis(self.chest.name)
        remap = rigamajig2.maya.node.remapValue('{}.{}'.format(self.chest.name, 'pivotHeight'),
                                                inMin=0, inMax=10, outMin=0,
                                                outMax=cmds.arclen(self.ikspline.getCurve(), ch=False),
                                                name=self.chest.name + "height")
        rigamajig2.maya.node.multDoubleLinear('{}.{}'.format(remap, 'outValue'), -1,
                                              output='{}.{}'.format(self.chest.name, 'rotatePivot' + axis.upper()),
                                              name=self.chest.name + "height")

        # connect the clusters to the spline
        cmds.parent(self.ikspline.getClusters()[0], self.hipSwingTrs)
        cmds.parent(self.ikspline.getClusters()[3], self.chest.name)
        rig_transform.matchTransform(self.ikspline.getClusters()[1], self.hipTanget.orig)
        cmds.parent(self.ikspline.getClusters()[1], self.hipTanget.name)
        rig_transform.matchTransform(self.ikspline.getClusters()[2], self.chestTanget.orig)
        cmds.parent(self.ikspline.getClusters()[2], self.chestTanget.name)

        # connect the orient constraint to the twist controls
        cmds.orientConstraint(self.hipSwing.name, self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.chestTop.name, self.ikspline._endTwist, mo=True)

    def connect(self):
        """Create the connection"""

        # add world space switches
        if cmds.objExists('trs_motion'):
            # setup the spaces
            spaces.create(self.hipSwing.spaces, self.hipSwing.name, parent=self.spacesHierarchy, defaultName='local')
            spaces.create(self.torso.spaces, self.torso.name, parent=self.spacesHierarchy, defaultName='local')
            spaces.create(self.chest.spaces, self.chest.name, parent=self.spacesHierarchy, defaultName='local')

            spaces.addSpace(self.hipSwing.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')
            spaces.addSpace(self.torso.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')
            spaces.addSpace(self.chest.spaces, ['trs_motion'], nameList=['world'], constraintType='parent')

        if self.chestSpaces:
            ikspaceValues = [self.chestSpaces[k] for k in self.chestSpaces.keys()]
            spaces.addSpace(self.chest.spaces, ikspaceValues, self.chestSpaces.keys(), 'parent')

        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.hipSwing.orig, mo=True)
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.torso.orig, mo=True)
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.ikspline.getGroup(), mo=True)

    def finalize(self):
        rig_attr.lock(self.ikspline.getGroup(), rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.paramsHierarchy, rig_attr.TRANSFORMS + ['v'])

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=5):
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        guidePositions = {"hips": (0, 0, 0),
                          "spine": (0, 6, 0),
                          "chest": (0, 3, 0)}

        joints = list()
        hipName = naming.getUniqueName("hips")
        hip = cmds.createNode("joint", name=hipName)

        cmds.setAttr("{}.radius".format(hip), 2)
        joints.append(hip)

        parent = hip
        for i in range(numJoints):
            spineName = naming.getUniqueName("spine_0")
            spine = cmds.createNode("joint", name=spineName)

            position = guidePositions['spine']
            if parent:
                cmds.parent(spine, parent)
            if i > 0:
                cmds.xform(spine, objectSpace=True, t=position)
            else:
                cmds.xform(spine, objectSpace=True, t=(0, 1, 0))
            joints.append(spine)

            parent = spine

        chestName = naming.getUniqueName("chest")
        chest = cmds.createNode("joint", name=chestName)

        cmds.parent(chest, parent)
        cmds.xform(chest, objectSpace=True, t=guidePositions['chest'])
        joints.append(chest)

        joint.orientJoints(joints, aimAxis='x', upAxis='y')
        cmds.setAttr("{}.jox".format(hip), -90)
        return joints
