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


class Spine(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, rigParent=str()):
        """
        Spine component.
        The spine containts the hipSwivel, torso and chest controls.
        Based on an IKSpline to create a smooth movement.

        :param name: name of the component
        :type name: str
        :param input: list of input joints. Starting with the base of the neck and ending with the head.
        :type input: list
        :param size: default size of the controls.
        :type size: float
        :param rigParent: connect the component to a rigParent.
        :type rigParent: str
        """

        super(Spine, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['hipsSwing_name'] = 'hip_swing'
        self.cmptSettings['torso_name'] = 'torso'
        self.cmptSettings['chest_name'] = 'chest'
        self.cmptSettings['chestTop_name'] = 'chestTop'
        self.cmptSettings['hipTanget_name'] = 'hipTan'
        self.cmptSettings['chestTanget_name'] = 'chestTan'
        # self.cmptSettings['hipSwivel_percent'] = 0.333
        # self.cmptSettings['torso_percent'] = 0.15

    def createBuildGuides(self):
        """Create the build guides"""
        HIPS_PERCENT = 0.33
        TORSO_PERCENT = 0.15

        self.guides_hrc = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self.hipsSwivel_guide = rig_control.createGuide(self.name + "_hipSwivel",
                                                        side=self.side,
                                                        parent=self.guides_hrc)
        live.slideBetweenTransforms(self.hipsSwivel_guide, self.input[1], self.input[-2], defaultValue=HIPS_PERCENT)

        self.torso_guide = rig_control.createGuide(self.name + "_torso", side=self.side, parent=self.guides_hrc)

        # setup the slider for the guide
        live.slideBetweenTransforms(self.torso_guide, self.input[1], self.input[-2], defaultValue=TORSO_PERCENT)

        self.chest_guide = rig_control.createGuide(self.name + "_chest",
                                                   side=self.side,
                                                   parent=self.guides_hrc,
                                                   position=cmds.xform(self.input[-2], q=True, ws=True, t=True))

        self.chestTop_guide = rig_control.createGuide(self.name + "_chestTop",
                                                      side=self.side,
                                                      parent=self.guides_hrc,
                                                      position=cmds.xform(self.input[-1], q=True, ws=True, t=True))

        for guide in [self.hipsSwivel_guide, self.torso_guide, self.chest_guide]:
            rig_attr.lock(guide, rig_attr.TRANSLATE)

        rig_attr.lockAndHide(self.chestTop_guide, rig_attr.TRANSLATE + ['v'])

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Spine, self).initalHierachy()

        # build the hips swivel control
        hip_pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.hip_swing = rig_control.createAtObject(self.hipsSwing_name, self.side,
                                                    hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                                    parent=self.control_hrc, shape='cube', shapeAim='x',
                                                    xformObj=self.hipsSwivel_guide)
        # build the torso control
        self.torso = rig_control.createAtObject(self.torso_name, self.side,
                                                hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                                parent=self.control_hrc, shape='cube', shapeAim='x',
                                                xformObj=self.torso_guide)

        # build the chest control
        self.chest = rig_control.createAtObject(self.chest_name, self.side,
                                                hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                                parent=self.torso.name, shape='cube', shapeAim='x',
                                                xformObj=self.chest_guide)
        self.chest.addTrs("neg")

        chest_pos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.chestTop = rig_control.createAtObject(self.chestTop_name, self.side,
                                                   hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                                   parent=self.chest.name, shape='cube', shapeAim='x',
                                                   xformObj=self.chestTop_guide)
        self.chest.addTrs("len")

        self.hipTanget = rig_control.create(self.hipTanget_name, self.side,
                                            hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                            parent=self.hip_swing.name, shape='diamond', shapeAim='x',
                                            position=hip_pos)

        self.chestTanget = rig_control.create(self.chestTanget_name, self.side,
                                              hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                              parent=self.chest.name, shape='diamond', shapeAim='x',
                                              position=chest_pos)

    def rigSetup(self):
        """Add the rig setup"""

        # the spline might shift slightly when the ik is created.
        # If built first this could affect the input of joints downstream
        # To comabt this  first we'll use the last joint to anchor the end of the spine to the chest top control
        self.chestTop_trs = hierarchy.create(self.chestTop.name, ['{}_trs'.format(self.input[0])], above=False)[0]
        rig_transform.matchTransform(self.input[-1], self.chestTop_trs)

        joint.connectChains(self.chestTop_trs, self.input[-1])

        # create the spline ik
        self.ikspline = spline.SplineBase(self.input[1:-1], name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=4, params=self.params_hrc)
        cmds.parent(self.ikspline.getGroup(), self.root_hrc)

        # setup the hipSwivel
        self.hips_swing_trs = hierarchy.create(self.hip_swing.name, ['{}_trs'.format(self.input[0])], above=False)[0]
        rig_transform.matchTransform(self.input[0], self.hips_swing_trs)
        joint.connectChains(self.hips_swing_trs, self.input[0])

        # create  attributes
        rig_attr.addSeparator(self.chest.name, '----')
        rig_attr.addSeparator(self.hip_swing.name, '----')
        rig_attr.createAttr(self.chest.name, 'pivotHeight', attributeType='float', value=3.5, minValue=0, maxValue=10)
        # connect the some attributes
        rig_attr.createAttr(self.chest.name, 'volumeFactor', attributeType='float', value=1, minValue=0, maxValue=10)
        cmds.connectAttr("{}.volumeFactor".format(self.chest.name), "{}.volumeFactor".format(self.params_hrc))

        # connect the tangets to the visablity
        rig_attr.createAttr(self.chest.name, 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.chest.name), "{}.v".format(self.chestTanget.orig))
        rig_attr.createAttr(self.hip_swing.name, 'tangentVis', attributeType='bool', value=1, channelBox=True,
                            keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.hip_swing.name), "{}.v".format(self.hipTanget.orig))

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
        cmds.parent(self.ikspline.getClusters()[0], self.hips_swing_trs)
        cmds.parent(self.ikspline.getClusters()[3], self.chest.name)
        rig_transform.matchTransform(self.ikspline.getClusters()[1], self.hipTanget.orig)
        cmds.parent(self.ikspline.getClusters()[1], self.hipTanget.name)
        rig_transform.matchTransform(self.ikspline.getClusters()[2], self.chestTanget.orig)
        cmds.parent(self.ikspline.getClusters()[2], self.chestTanget.name)

        # connect the orient constraint to the twist controls
        cmds.orientConstraint(self.hip_swing.name, self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.chestTop.name, self.ikspline._endTwist, mo=True)

    def connect(self):
        """Create the connection"""

        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.hip_swing.orig, mo=True)
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.torso.orig, mo=True)
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.ikspline.getGroup(), mo=True)

    def finalize(self):
        rig_attr.lock(self.ikspline.getGroup(), rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.params_hrc, rig_attr.TRANSFORMS + ['v'])

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=5):
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        GUIDE_POSITIONS = {"hips": (0, 0, 0),
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

            position = GUIDE_POSITIONS['spine']
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
        cmds.xform(chest, objectSpace=True, t=GUIDE_POSITIONS['chest'])
        joints.append(chest)

        joint.orientJoints(joints, aimAxis='x', upAxis='y')
        cmds.setAttr("{}.jox".format(hip), -90)
        return joints