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
    def __init__(self, name, input=[], size=1, rigParent=str()):
        super(Neck, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['neck_name'] = 'neck'
        self.cmptSettings['head_name'] = 'head'
        self.cmptSettings['headGimble_name'] = 'headGimble'
        self.cmptSettings['skull_name'] = 'headGimble'
        self.cmptSettings['head_percent'] = 0.7

    def initalHierachy(self):
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        neck_pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.neck = rig_control.create(self.neck_name, self.side,
                                       hierarchy=['trsBuffer'],
                                       hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                       parent=self.control_hrc, shape='cube', shapeAim='x',
                                       position=neck_pos)
        head_pos = mathUtils.nodePosLerp(self.input[0], self.input[-1], self.head_percent)
        self.head = rig_control.create(self.head_name, self.side,
                                       hierarchy=['trsBuffer'],
                                       hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                       parent=self.neck[-1], shape='cube', shapeAim='x',
                                       position=head_pos)
        self.neckGimble = rig_control.create(self.skull_name, self.side,
                                             hierarchy=['trsBuffer'],
                                             hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                             parent=self.head[-1], shape='cube', shapeAim='x',
                                             position=head_pos)
        skull_pos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.skull = rig_control.create(self.skull_name, self.side,
                                        hierarchy=['trsBuffer'],
                                        hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                        parent=self.neckGimble[-1], shape='cube', shapeAim='x',
                                        position=skull_pos)

    def rigSetup(self):
        """Add the rig setup"""
        # create the spline ik
        self.ikspline = spline.SplineBase(self.input, name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=4)
        cmds.parent(self.ikspline.getGroup(), self.root_hrc)

