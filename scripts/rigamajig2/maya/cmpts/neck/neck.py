"""
neck component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.live as live
import rigamajig2.maya.rig.spline as spline
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.constrain as constrain
import rigamajig2.maya.node as node
import rigamajig2.shared.common as common
import rigamajig2.maya.hierarchy as hierarchy
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.joint as rig_joint
import rigamajig2.maya.meta as meta


class Neck(rigamajig2.maya.cmpts.base.Base):
    def __init__(self, name, input=[], size=1, headSpaces=dict(), neckSpaces=dict(), rigParent=str()):
        """
        Neck component.
        The neck has a head and neck control to create natural movement in the head

        :param name: name of the component
        :type name: str
        :param input: list of input joints. Starting with the base of the neck and ending with the head.
        :type input: list
        :param size: default size of the controls.
        :type size: float
        :param headSpaces: dictionary of key and space for the head control. formated as {"attrName": object}
        :type headSpaces: dict
        :param neckSpaces: dictionary of key and space for the neck control. formated as {"attrName": object}
        :param rigParent: connect the component to a rigParent.
        :type rigParent: str
        """

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

    def createBuildGuides(self):
        """Create the build guides"""
        HEAD_PERCENT = 0.7

        self.guides_hrc = cmds.createNode("transform", name='{}_guide'.format(self.name))

        neck_pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.neck_guide = rig_control.createGuide(self.name + "_neck", side=self.side, parent=self.guides_hrc,
                                                  position=neck_pos)
        rig_attr.lockAndHide(self.neck_guide, rig_attr.TRANSLATE + ['v'])

        self.head_guide = rig_control.createGuide(self.name + "_head", side=self.side, parent=self.guides_hrc)
        live.slideBetweenTransforms(self.head_guide, start=self.input[0], end=self.input[-1], defaultValue=HEAD_PERCENT)
        rig_attr.lock(self.head_guide, rig_attr.TRANSLATE + ['v'])

        skull_pos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.skull_guide = rig_control.createGuide(self.name + "_skull", side=self.side, parent=self.guides_hrc,
                                                   position=skull_pos)
        rig_attr.lockAndHide(self.skull_guide, rig_attr.TRANSLATE + ['v'])

    def initalHierachy(self):
        super(Neck, self).initalHierachy()

        self.neck = rig_control.createAtObject(
            self.neck_name, self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.control_hrc,
            shape='cube',
            shapeAim='x',
            xformObj=self.neck_guide)

        self.head = rig_control.createAtObject(
            self.head_name, self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.neck.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.head_guide)

        self.headGimble = rig_control.createAtObject(
            self.headGimble_name,
            self.side,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.head.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.head_guide)

        self.skull = rig_control.createAtObject(
            self.skull_name,
            self.side,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.headGimble.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.skull_guide)

        self.headTanget = rig_control.createAtObject(
            self.headTangent_name, self.side,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='yellow',
            parent=self.headGimble.name,
            shape='diamond',
            shapeAim='x',
            xformObj=self.skull_guide)

        self.neckTanget = rig_control.createAtObject(
            self.neckTangent_name,
            self.side,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='yellow',
            parent=self.neck.name,
            shape='diamond',
            shapeAim='x',
            xformObj=self.neck_guide)

    def rigSetup(self):
        """Add the rig setup"""
        # create the spline ik
        self.ikspline = spline.SplineBase(self.input, name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=4, params=self.params_hrc)
        cmds.parent(self.ikspline.getGroup(), self.root_hrc)

        # connect the volume factor and tangents visability attributes
        rig_attr.createAttr(self.head.name, 'volumeFactor', attributeType='float', value=1, minValue=0, maxValue=10)
        cmds.connectAttr("{}.volumeFactor".format(self.head.name), "{}.volumeFactor".format(self.params_hrc))

        rig_attr.createAttr(self.neck.name, 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.neck.name), "{}.v".format(self.neckTanget.orig))
        rig_transform.matchTransform(self.ikspline.getClusters()[1], self.neckTanget.orig)

        rig_attr.createAttr(self.head.name, 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.head.name), "{}.v".format(self.headTanget.orig))
        rig_transform.matchTransform(self.ikspline.getClusters()[2], self.headTanget.orig)

        # parent clusters to tangent controls
        cmds.parent(self.ikspline.getClusters()[1], self.neckTanget.name)
        cmds.parent(self.ikspline.getClusters()[2], self.headTanget.name)
        cmds.parent(self.ikspline.getClusters()[3], self.headGimble.name)

        # connect the skull to the head joint
        self.skull_trs = hierarchy.create(self.skull.name, ['{}_trs'.format(self.input[-1])], above=False)[0]
        rig_transform.matchTransform(self.input[-1], self.skull_trs)
        cmds.delete(cmds.ls(cmds.listConnections("{}.tx".format(self.input[-1])),
                            type='parentConstraint'))  # delete exising parent constraint
        rig_joint.connectChains(self.skull_trs, self.input[-1])

        # connect the orient constraint to the twist controls
        cmds.orientConstraint(self.neck.name, self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.headGimble.name, self.ikspline._endTwist, mo=True)

        rig_transform.connectOffsetParentMatrix(self.neck.name, self.ikspline.getGroup(), mo=True)

    def connect(self):
        """Create the connection"""

        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.neck.orig, mo=True)

        spaces.create(self.neck.spaces, self.neck.name, parent=self.spaces_hrc)
        spaces.create(self.head.spaces, self.head.name, parent=self.spaces_hrc)

        # if the main control exists connect the world space
        if cmds.objExists('trs_motion'):
            spaces.addSpace(self.neck.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')
            spaces.addSpace(self.head.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')

        if self.neckSpaces:
            spaces.addSpace(self.head.spaces, [self.neckSpaces[k] for k in self.neckSpaces.keys()],
                            self.neckSpaces.keys(),
                            'orient')

        if self.headSpaces:
            spaces.addSpace(self.head.spaces, [self.headSpaces[k] for k in self.headSpaces.keys()],
                            self.headSpaces.keys(),
                            'orient')

    def finalize(self):
        rig_attr.lock(self.ikspline.getGroup(), rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.params_hrc, rig_attr.TRANSFORMS + ['v'])

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=4):
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        GUIDE_POSITIONS = {"neck": (0, 4, 0),
                           "head": (0, 2, 0)}

        joints = list()

        parent = None
        for i in range(numJoints):
            neckName = naming.getUniqueName("neck_0")
            neck = cmds.createNode("joint", name=neckName)

            position = GUIDE_POSITIONS['neck']
            if parent:
                cmds.parent(neck, parent)
            if i > 0:
                cmds.xform(neck, objectSpace=True, t=position)
            else:
                cmds.xform(neck, objectSpace=True, t=(0, 0, 0))
            joints.append(neck)

            parent = neck

        headName = naming.getUniqueName("head")
        head = cmds.createNode("joint", name=headName)

        cmds.parent(head, parent)
        cmds.xform(head, objectSpace=True, t=GUIDE_POSITIONS['head'])
        joints.append(head)

        joint.orientJoints(joints, aimAxis='x', upAxis='y')
        cmds.setAttr("{}.jox".format(joints[0]), -90)
        return joints
