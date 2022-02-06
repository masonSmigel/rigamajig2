"""
neck component
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
import rigamajig2.maya.meta as meta


class Neck(rigamajig2.maya.cmpts.base.Base):
    def __init__(self, name, input=[], size=1, headSpaces=dict(), neckSpaces=dict(), rigParent=str()):
        super(Neck, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['neck_name'] = 'neck'
        self.cmptSettings['head_name'] = 'head'
        self.cmptSettings['headGimble_name'] = 'headGimble'
        self.cmptSettings['headTangent_name'] = 'headTan'
        self.cmptSettings['neckTangent_name'] = 'neckTan'
        self.cmptSettings['skull_name'] = 'skull'
        self.cmptSettings['neckSpaces'] = neckSpaces
        self.cmptSettings['headSpaces'] = headSpaces

    def initalHierachy(self):
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        neck_pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.neck = rig_control.create(self.neck_name, self.side,
                                       hierarchy=['trsBuffer', 'spaces_trs'],
                                       hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                       parent=self.control_hrc, shape='cube', shapeAim='x',
                                       position=neck_pos)
        head_pos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.head = rig_control.create(self.head_name, self.side,
                                       hierarchy=['trsBuffer', 'spaces_trs'],
                                       hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                       parent=self.neck[-1], shape='cube', shapeAim='x',
                                       position=head_pos)
        self.headGimble = rig_control.create(self.headGimble_name, self.side,
                                             hierarchy=['trsBuffer'],
                                             hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                             parent=self.head[-1], shape='cube', shapeAim='x',
                                             position=head_pos)
        skull_pos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.skull = rig_control.create(self.skull_name, self.side,
                                        hierarchy=['trsBuffer'],
                                        hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                        parent=self.headGimble[-1], shape='cube', shapeAim='x',
                                        position=skull_pos)
        self.headTanget = rig_control.create(self.headTangent_name, self.side,
                                             hierarchy=['trsBuffer'],
                                             hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                             parent=self.headGimble[-1], shape='diamond', shapeAim='x',
                                             position=head_pos)
        self.neckTanget = rig_control.create(self.neckTangent_name, self.side,
                                             hierarchy=['trsBuffer'],
                                             hideAttrs=['r', 's', 'v'], size=self.size, color='yellow',
                                             parent=self.neck[-1], shape='diamond', shapeAim='x',
                                             position=neck_pos)

    def rigSetup(self):
        """Add the rig setup"""
        # create the spline ik
        self.ikspline = spline.SplineBase(self.input, name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=4)
        cmds.parent(self.ikspline.getGroup(), self.root_hrc)

        # connect the tangents visability
        rig_attr.addAttr(self.neck[-1], 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.neck[-1]), "{}.v".format(self.neckTanget[0]))
        rig_transform.matchTransform(self.ikspline.getClusters()[1], self.neckTanget[0])

        rig_attr.addAttr(self.head[-1], 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.head[-1]), "{}.v".format(self.headTanget[0]))
        rig_transform.matchTransform(self.ikspline.getClusters()[2], self.headTanget[0])

        cmds.parent(self.ikspline.getClusters()[1], self.neckTanget[-1])
        cmds.parent(self.ikspline.getClusters()[2], self.headTanget[-1])
        cmds.parent(self.ikspline.getClusters()[3], self.headGimble[-1])

        self.skull_trs = hierarchy.create(self.skull[-1], ['{}_trs'.format(self.input[-1])], above=False)[0]
        rig_transform.matchTransform(self.input[-1], self.skull_trs)
        rig_transform.connectOffsetParentMatrix(self.skull_trs, self.input[-1])

        # create the neck piviot offset
        rig_attr.addAttr(self.head[-1], 'pivotHeight', attributeType='float', value=3.5, minValue=0, maxValue=10)
        axis = rig_transform.getAimAxis(self.neck[-1])
        remap = node.remapValue('{}.{}'.format(self.head[-1], 'pivotHeight'),
                                inMin=0, inMax=10, outMin=0,
                                outMax=cmds.arclen(self.ikspline.getCurve(), ch=False),
                                name=self.head[-1] + "height")
        node.multDoubleLinear('{}.{}'.format(remap, 'outValue'), -1,
                              output='{}.{}'.format(self.head[-1], 'rotatePivot' + axis.upper()),
                              name=self.head[-1] + "height")

        # connect the orient constraint to the twist controls
        cmds.orientConstraint(self.neck[-1], self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.headGimble[-1], self.ikspline._endTwist, mo=True)

        rig_transform.connectOffsetParentMatrix(self.neck[-1], self.ikspline.getGroup(), mo=True)
        rig_attr.lock(self.ikspline.getGroup(), rig_attr.TRANSFORMS + ['v'])

    def connect(self):
        """Create the connection"""

        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.neck[0], mo=True)

        spaces.create(self.neck[1], self.neck[-1], parent=self.spaces_hrc)
        spaces.create(self.head[1], self.head[-1], parent=self.spaces_hrc)

        # if the main control exists connect the world space
        if cmds.objExists('trs_motion'):
            spaces.addSpace(self.neck[1], ['trs_motion'], nameList=['world'], constraintType='orient')
            spaces.addSpace(self.head[1], ['trs_motion'], nameList=['world'], constraintType='orient')

        if self.neckSpaces:
            spaces.addSpace(self.head[1], [self.neckSpaces[k] for k in self.neckSpaces.keys()], self.neckSpaces.keys(),
                            'orient')

        if self.headSpaces:
            spaces.addSpace(self.head[1], [self.headSpaces[k] for k in self.headSpaces.keys()], self.headSpaces.keys(),
                            'orient')
