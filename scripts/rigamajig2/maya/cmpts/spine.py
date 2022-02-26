"""
spine component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
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
        super(Spine, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['hips_name'] = 'hips'
        self.cmptSettings['hipsGimble_name'] = 'hipsGimble'
        self.cmptSettings['hipsPivot_name'] = 'hips_pivot'
        self.cmptSettings['hipsSwing_name'] = 'hip_swing'
        self.cmptSettings['torso_name'] = 'torso'
        self.cmptSettings['chest_name'] = 'chest'
        self.cmptSettings['chestTop_name'] = 'chestTop'
        self.cmptSettings['hipTanget_name'] = 'hipTan'
        self.cmptSettings['chestTanget_name'] = 'chestTan'
        self.cmptSettings['hipSwivel_percent'] = 0.333
        self.cmptSettings['torso_percent'] = 0.15

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        # setup the hip controls
        hip_pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.hips_pivot = rig_control.create(self.hipsPivot_name, self.side,
                                             hierarchy=['trsBuffer'],
                                             hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                             parent=self.control_hrc, shape='sphere', shapeAim='x',
                                             position=hip_pos)
        self.hips = rig_control.create(self.hips_name, self.side,
                                       hierarchy=['trsBuffer', 'neg'],
                                       hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                       parent=self.control_hrc, shape='cube', shapeAim='x',
                                       position=hip_pos)
        self.hipsGimble = rig_control.create(self.hipsGimble_name, self.side,
                                             hierarchy=['trsBuffer'],
                                             hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                             parent=self.hips[-1], shape='cube', shapeAim='x',
                                             position=hip_pos)
        # build the hips swivel control
        hipSwivel_pos = mathUtils.nodePosLerp(self.input[0], self.input[-1], self.hipSwivel_percent)
        self.hip_swing = rig_control.create(self.hipsSwing_name, self.side,
                                            hierarchy=['trsBuffer'],
                                            hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                            parent=self.hipsGimble[-1], shape='cube', shapeAim='x',
                                            position=hipSwivel_pos)
        # build the torso control
        torso_pos = mathUtils.nodePosLerp(self.input[0], self.input[-1], self.torso_percent)
        self.torso = rig_control.create(self.torso_name, self.side,
                                        hierarchy=['trsBuffer'],
                                        hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                        parent=self.hipsGimble[-1], shape='cube', shapeAim='x',
                                        position=torso_pos)

        # build the chest control
        spineEnd_pos = cmds.xform(self.input[-2], q=True, ws=True, t=True)
        self.chest = rig_control.create(self.chest_name, self.side,
                                        hierarchy=['trsBuffer', 'neg'],
                                        hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                        parent=self.torso[-1], shape='cube', shapeAim='x',
                                        position=spineEnd_pos)
        chest_pos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.chestTop = rig_control.create(self.chestTop_name, self.side,
                                           hierarchy=['trsBuffer', 'len'],
                                           hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                           parent=self.chest[-1], shape='cube', shapeAim='x',
                                           position=chest_pos)

        self.hipTanget = rig_control.create(self.hipTanget_name, self.side,
                                            hierarchy=['trsBuffer'],
                                            hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                            parent=self.hip_swing[-1], shape='diamond', shapeAim='x',
                                            position=hip_pos)

        self.chestTanget = rig_control.create(self.chestTanget_name, self.side,
                                              hierarchy=['trsBuffer'],
                                              hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                              parent=self.chest[-1], shape='diamond', shapeAim='x',
                                              position=chest_pos)

    def rigSetup(self):
        """Add the rig setup"""

        # the spline might shift slightly when the ik is created.
        # If built first this could affect the input of joints downstream
        # To comabt this  first we'll use the last joint to anchor the end of the spine to the chest top control
        self.chestTop_trs = hierarchy.create(self.chestTop[-1], ['{}_trs'.format(self.input[0])], above=False)[0]
        rig_transform.matchTransform(self.input[-1], self.chestTop_trs)

        joint.connectChains(self.chestTop_trs, self.input[-1])

        # create the spline ik
        self.ikspline = spline.SplineBase(self.input[1:-1], name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=4)
        cmds.parent(self.ikspline.getGroup(), self.root_hrc)

        # setup the hipSwivel
        self.hips_swing_trs = hierarchy.create(self.hip_swing[-1], ['{}_trs'.format(self.input[0])], above=False)[0]
        rig_transform.matchTransform(self.input[0], self.hips_swing_trs)
        joint.connectChains(self.hips_swing_trs, self.input[0])

        # create the pivot negate
        constrain.negate(self.hips_pivot[-1], self.hips[1], t=True)

        # create  attributes
        rig_attr.addSeparator(self.chest[-1], '----')
        rig_attr.addSeparator(self.hip_swing[-1], '----')
        rig_attr.addAttr(self.chest[-1], 'pivotHeight', attributeType='float', value=3.5, minValue=0, maxValue=10)
        # connect the some attributes
        rig_attr.addAttr(self.chest[-1], 'volumeFactor', attributeType='float', value=1, minValue=0, maxValue=10)
        cmds.connectAttr("{}.volumeFactor".format(self.chest[-1]), "{}.volumeFactor".format(self.ikspline.getGroup()))

        # connect the tangets to the visablity
        rig_attr.addAttr(self.chest[-1], 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.chest[-1]), "{}.v".format(self.chestTanget[0]))
        rig_attr.addAttr(self.hip_swing[-1], 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.hip_swing[-1]), "{}.v".format(self.hipTanget[0]))

        # create the chest piviot offset
        axis = rig_transform.getAimAxis(self.chest[-1])
        remap = rigamajig2.maya.node.remapValue('{}.{}'.format(self.chest[-1], 'pivotHeight'),
                                                inMin=0, inMax=10, outMin=0,
                                                outMax=cmds.arclen(self.ikspline.getCurve(), ch=False),
                                                name=self.chest[-1] + "height")
        rigamajig2.maya.node.multDoubleLinear('{}.{}'.format(remap, 'outValue'), -1,
                                              output='{}.{}'.format(self.chest[-1], 'rotatePivot' + axis.upper()),
                                              name=self.chest[-1] + "height")

        # connect the clusters to the spline
        cmds.parent(self.ikspline.getClusters()[0], self.hips_swing_trs)
        cmds.parent(self.ikspline.getClusters()[3], self.chest[-1])
        rig_transform.matchTransform(self.ikspline.getClusters()[1], self.hipTanget[0])
        cmds.parent(self.ikspline.getClusters()[1], self.hipTanget[-1])
        rig_transform.matchTransform(self.ikspline.getClusters()[2], self.chestTanget[0])
        cmds.parent(self.ikspline.getClusters()[2], self.chestTanget[-1])

        # connect the orient constraint to the twist controls
        cmds.orientConstraint(self.hip_swing[-1], self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.chestTop[-1], self.ikspline._endTwist, mo=True)

        rig_transform.connectOffsetParentMatrix(self.hipsGimble[-1], self.ikspline.getGroup(), mo=True)
        rig_attr.lock(self.ikspline.getGroup(), rig_attr.TRANSFORMS + ['v'])

    def connect(self):
        """Create the connection"""

        if cmds.objExists(self.rigParent):
            cmds.parentConstraint(self.rigParent, self.hips[0], mo=True)
            cmds.parentConstraint(self.rigParent, self.hips_pivot[0], mo=True)
