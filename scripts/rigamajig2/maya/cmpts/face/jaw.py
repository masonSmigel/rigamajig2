"""
functions to create a jaw rig.
Unlike other components that are built from the base component, this is a system of organized methods.
"""
import maya.cmds as cmds

import rigamajig2.maya.cmpts.face.base as base
import rigamajig2.maya.container
import rigamajig2.shared.common as common

import rigamajig2.maya.rig.control as control
import rigamajig2.maya.hierarchy as hierarchy
import rigamajig2.maya.transform as transform
import rigamajig2.maya.attr as attr
import rigamajig2.maya.joint as joint
import rigamajig2.maya.node as node
import rigamajig2.maya.meta as meta


class Jaw(base.Base):
    def __init__(self, name):
        self.name = name
        self.container = self.name + '_container'

        self.lip_guides = list()
        self.jaw_guides = list()

    def createGuides(self, number):
        """This is based on the tutorial from gnomon. This should be re-writen to use a list of edges"""
        self.guides_hrc = cmds.createNode("transform", name='{}_guide'.format(self.name))
        self.lip_guides_hrc = cmds.createNode("transform", name='{}_lip_guide'.format(self.name),
                                              parent=self.guides_hrc)

        for part in ['upper', 'lower']:
            part_mult = 1 if part == 'upper' else -1
            mid_guide = control.createGuide(name="{}_c_{}".format(self.name, part), type='face',
                                            parent=self.lip_guides_hrc, position=(0, part_mult, 0), size=0.1)
            # set class variables for the upper and lower uides
            if part == 'upper':
                self.upper_guide = mid_guide
            elif part == 'lower':
                self.lower_guide = mid_guide
            self.lip_guides.append(mid_guide)

            for side in [common.LEFT, common.RIGHT]:
                for x in range(number):
                    multipler = x + 1 if side == common.LEFT else -(x + 1)
                    guide_pos = (multipler, part_mult, 0)
                    guide = control.createGuide(name="{}_{}_{}_{}".format(self.name, part, side, x + 1), type='face',
                                                parent=self.lip_guides_hrc, position=guide_pos, size=0.1)
                    self.lip_guides.append(guide)

        # create corner
        self.l_corner_guide = control.createGuide(name="{}_{}_corner".format(self.name, common.LEFT), type='face',
                                                  parent=self.lip_guides_hrc, position=(number + 1, 0, 0), size=0.1)
        self.r_corner_guide = control.createGuide(name="{}_{}_corner".format(self.name, common.RIGHT), type='face',
                                                  parent=self.lip_guides_hrc, position=(-(number + 1), 0, 0), size=0.1)
        self.lip_guides += [self.l_corner_guide, self.r_corner_guide]

        # jaw base
        self.jaw_guides_hrc = cmds.createNode("transform", name='{}_jaw_guide'.format(self.name),
                                              parent=self.guides_hrc)
        jaw_base_guide = control.createGuide(name="{}_jaw_base".format(self.name), type='face',
                                             parent=self.jaw_guides_hrc, position=(0, -1, -number))
        jaw_inver_guide = control.createGuide(name="{}_jaw_inverse".format(self.name), type='face',
                                              parent=self.jaw_guides_hrc, position=(0, 1, -number))
        self.jaw_guides = [jaw_base_guide, jaw_inver_guide]

    def build(self):
        self.initalHierachy()
        self.createMinorJoints()
        self.createBroadJoints()
        self.createBaseJoints()
        self.setupRig()
        self.createSeal('upper')
        self.createSeal('lower')
        self.createJawParams()
        self.createConstraints()
        self.createInitalValues("upper")
        self.createInitalValues("lower")
        self.createOffsetFollow()
        self.createSealParams()
        self.connectSeal('upper')
        self.connectSeal('lower')
        self.createCornerPinning()
        self.setupAnimAttrs()

    def initalHierachy(self):
        super(Jaw, self).initalHierachy()
        self.joints_hrc = cmds.createNode('transform', n=self.name + '_joints', parent=self.root_hrc)
        self.lip_joints_hrc = cmds.createNode('transform', n=self.name + '_lip_joints', parent=self.joints_hrc)
        self.minor_lip_hrc = cmds.createNode('transform', n=self.name + '_minor_lip', parent=self.lip_joints_hrc)
        self.broad_lip_hrc = cmds.createNode('transform', n=self.name + '_broad_lip', parent=self.lip_joints_hrc)
        self.base_joint_hrc = cmds.createNode('transform', n=self.name + '_base_joints', parent=self.joints_hrc)

        self.jaw_control = control.createAtObject(self.name,  hierarchy=['trsBuffer', 'auto_trs'], parent=self.control_hrc, shape='square', xformObj=self.jaw_guides[0])

        self.jawInverse_control = control.createAtObject(self.name + '_inverse', parent=self.control_hrc, shape='square', xformObj=self.jaw_guides[1])

        self.l_corner_control = control.createAtObject(self.name + "_corner_{}".format(common.LEFT), hideAttrs=['sx', 'sy', 'sz', 'v'],
                                                       parent=self.control_hrc, shape='sphere', xformObj=self.l_corner_guide)
        self.r_corner_control = control.createAtObject(self.name + "_corner_{}".format(common.RIGHT),  hideAttrs=['sx', 'sy', 'sz', 'v'],
                                                       parent=self.control_hrc, shape='sphere', xformObj=self.r_corner_guide)

    def createMinorJoints(self):
        """
        create minor joints
        :return:
        """

        self.minor_joints = list()

        for guide in self.lip_guides:
            wm = cmds.xform(guide, q=True, ws=True, m=True)
            joint = cmds.createNode("joint", n="{}_bind".format(guide))
            cmds.setAttr("{}.radius".format(joint), 0.5)
            cmds.xform(joint, ws=True, m=wm)
            self.minor_joints.append(joint)
            meta.tag(joint, 'bind')
            cmds.parent(joint, self.minor_lip_hrc)

        return self.minor_joints

    def createBroadJoints(self):
        """ create major joints around the lips"""
        self.upper_broad = cmds.createNode("joint", name="{}_upper_drvr".format(self.name))
        self.lower_broad = cmds.createNode("joint", name="{}_lower_drvr".format(self.name))
        self.l_corner_broad = cmds.createNode("joint", name="{}_{}_corner_drvr".format(self.name, common.LEFT))
        self.r_corner_broad = cmds.createNode("joint", name="{}_{}_corner_drvr".format(self.name, common.RIGHT))

        cmds.parent([self.upper_broad, self.lower_broad, self.l_corner_broad, self.r_corner_broad], self.broad_lip_hrc)

        # match the broad joints to the guides
        transform.matchTransform(self.upper_guide, self.upper_broad)
        transform.matchTransform(self.lower_guide, self.lower_broad)
        transform.matchTransform(self.l_corner_guide, self.l_corner_broad)
        transform.matchTransform(self.r_corner_guide, self.r_corner_broad)

        self.upper_trsBuffer = hierarchy.create(self.upper_broad, hierarchy=["{}_trsBuffer".format(self.upper_broad)])
        self.lower_trsBuffer = hierarchy.create(self.lower_broad, hierarchy=["{}_trsBuffer".format(self.lower_broad)])
        self.l_corner_trsBuffer = hierarchy.create(self.l_corner_broad,
                                                   hierarchy=["{}_trsBuffer".format(self.l_corner_broad)])
        self.r_corner_trsBuffer = hierarchy.create(self.r_corner_broad,
                                                   hierarchy=["{}_trsBuffer".format(self.r_corner_broad)])

    def createBaseJoints(self):
        """Create the base joints"""
        self.jaw_jnt = cmds.createNode("joint", name="{}_jaw_bind".format(self.name))
        self.jawInverse_jnt = cmds.createNode("joint", name="{}_inverse_bind".format(self.name))

        meta.tag([self.jaw_jnt, self.jawInverse_jnt], 'bind')

        jaw_pos = cmds.xform(self.jaw_guides[0], q=True, ws=True, m=True)
        inverse_pos = cmds.xform(self.jaw_guides[-1], q=True, ws=True, m=True)

        cmds.xform(self.jaw_jnt, ws=True, m=jaw_pos)
        cmds.xform(self.jawInverse_jnt, ws=True, m=inverse_pos)

        cmds.parent([self.jaw_jnt, self.jawInverse_jnt], self.base_joint_hrc)

        self.jaw_hi = hierarchy.create(self.jaw_jnt, hierarchy=['{}_trsBuffer'.format(self.jaw_jnt), '{}_trs'.format(self.jaw_jnt)])
        self.jawInverse_hi = hierarchy.create(self.jawInverse_jnt, hierarchy=['{}_trsBuffer'.format(self.jawInverse_jnt)])

    def setupRig(self):

        joint.connectChains(self.jaw_control[-1], self.jaw_hi[1])
        joint.connectChains(self.jawInverse_control[-1], self.jawInverse_jnt)

        cmds.parentConstraint(self.jaw_jnt, self.lower_trsBuffer, mo=True)
        cmds.parentConstraint(self.jawInverse_jnt, self.upper_trsBuffer, mo=True)

        cmds.parentConstraint(self.upper_trsBuffer, self.lower_trsBuffer, self.l_corner_control[0], mo=True)
        cmds.parentConstraint(self.upper_trsBuffer, self.lower_trsBuffer, self.r_corner_control[0], mo=True)

        joint.connectChains(self.l_corner_control[-1], self.l_corner_broad)
        joint.connectChains(self.r_corner_control[-1], self.r_corner_broad)

    def getLipParts(self):
        upper_token = 'upper'
        lower_token = 'lower'
        corner_token = 'corner'

        lookup = {"c_upper": {}, "c_lower": {},
                  "l_upper": {}, "l_lower": {},
                  "r_upper": {}, "r_lower": {},
                  "l_corner": {}, "r_corner":{}}

        for joint in self.minor_joints:
            joint_side = common.getSide(joint)

            if joint_side == 'c' and upper_token in joint:
                lookup["c_upper"][joint] = [self.upper_broad]
            if joint_side == 'c' and lower_token in joint:
                lookup["c_lower"][joint] = [self.lower_broad]

            if joint_side == 'l' and upper_token in joint:
                lookup["l_upper"][joint] = [self.upper_broad, self.l_corner_broad]
            if joint_side == 'l' and lower_token in joint:
                lookup["l_lower"][joint] = [self.lower_broad, self.l_corner_broad]

            if joint_side == 'r' and upper_token in joint:
                lookup["r_upper"][joint] = [self.upper_broad, self.r_corner_broad]
            if joint_side == 'r' and lower_token in joint:
                lookup["r_lower"][joint] = [self.lower_broad, self.r_corner_broad]

            if joint_side == 'l' and corner_token in joint:
                lookup["l_corner"][joint] = [self.l_corner_broad]
            if joint_side == 'r' and corner_token in joint:
                lookup["r_corner"][joint] = [self.r_corner_broad]

        return lookup

    def getLipPart(self, part):
        """
        retreive an ordered list of parts of the lip rig
        :param part: part to return. Valid values are "upper" or "lower"
        :return:
        """
        lip_lookup = self.getLipParts()

        lipParts = [reversed(sorted(lip_lookup["l_{}".format(part)])),
                    sorted(lip_lookup["c_{}".format(part)]),
                    sorted(lip_lookup["r_{}".format(part)])]

        return [joint for joint in lipParts for joint in joint]

    def createSeal(self, part):
        """
        create the lip seal
        :param part:
        :return:
        """
        seal_name = "{}_seal".format(self.name)
        self.seal_hrc = seal_name if cmds.objExists(seal_name) else cmds.createNode("transform", name=seal_name, parent=self.root_hrc)

        part_group = cmds.createNode("transform", name="{}_{}_seal".format(self.name, part), parent=self.seal_hrc)

        value = len(self.getLipPart(part))

        for index, joint in enumerate(self.getLipPart(part)):
            node = cmds.createNode("transform", n='{}_seal_trs'.format(joint), parent=part_group)
            transform.matchTransform(joint, node)

            # create the constraint
            constraint = cmds.parentConstraint(self.l_corner_broad, self.r_corner_broad, node, mo=True)[0]
            cmds.setAttr("{}.interpType".format(constraint), 2)

            r_corner_value = float(index) / float(value-1)
            l_corner_value = 1-r_corner_value

            l_corner_attr = "{}.{}W0".format(constraint, self.l_corner_broad)
            r_corner_attr = "{}.{}W1".format(constraint, self.r_corner_broad)

            cmds.setAttr(l_corner_attr, l_corner_value)
            cmds.setAttr(r_corner_attr, r_corner_value)

    def createJawParams(self):
        """

        :return:
        """

        self.jaw_params = list()

        c_upper_attr = sorted(self.getLipParts()["c_upper"].keys())[0]
        cmds.addAttr(self.params_hrc, ln=c_upper_attr, min=0, max=1, dv=0)
        cmds.setAttr("{}.{}".format(self.params_hrc, c_upper_attr), lock=True)

        for upper in sorted(self.getLipParts()['l_upper'].keys()):
            cmds.addAttr(self.params_hrc, ln=upper, min=0, max=1, dv=0)

        l_corner_attr = sorted(self.getLipParts()["l_corner"].keys())[0]
        cmds.addAttr(self.params_hrc, ln=l_corner_attr, min=0, max=1, dv=1)
        cmds.setAttr("{}.{}".format(self.params_hrc, l_corner_attr), lock=True)

        for lower in sorted(self.getLipParts()['l_lower'].keys())[::-1]:
            cmds.addAttr(self.params_hrc, ln=lower, min=0, max=1, dv=0)

        c_lower_attr = sorted(self.getLipParts()["c_lower"].keys())[0]
        cmds.addAttr(self.params_hrc, ln=c_lower_attr, min=0, max=1, dv=0)
        cmds.setAttr("{}.{}".format(self.params_hrc, c_lower_attr), lock=True)

    def createConstraints(self):
        """

        :return:
        """
        for value in self.getLipParts().values():
            for lip_joint, broad_joint in value.items():
                seal_trs = '{}_seal_trs'.format(lip_joint)

                if not cmds.objExists(seal_trs):
                    constraint = cmds.parentConstraint(broad_joint, lip_joint, mo=True)[0]
                    cmds.setAttr("{}.interpType".format(constraint), 2)
                    continue

                constraint = cmds.parentConstraint(broad_joint, seal_trs, lip_joint, mo=True)[0]
                cmds.setAttr("{}.interpType".format(constraint), 2)

                constraint = cmds.ls(cmds.listRelatives(lip_joint, c=True), type='parentConstraint')[0]
                if len(broad_joint) == 1:
                    seal_attr = "{}.{}W1".format(constraint, seal_trs)
                    cmds.setAttr(seal_attr, 0)
                    rev = cmds.createNode("reverse", name="{}_rev".format(lip_joint))
                    cmds.connectAttr(seal_attr, "{}.inputX".format(rev))
                    cmds.connectAttr("{}.outputX".format(rev), "{}.{}W0".format(constraint, broad_joint[0]))
                elif len(broad_joint) == 2:
                    # TODO: this will need to be optimized as its basically a huge cycle
                    seal_attr = "{}.{}W2".format(constraint, seal_trs)
                    cmds.setAttr(seal_attr, 0)

                    lip_attr = lip_joint
                    if common.getSide(lip_joint) == 'r':
                        lip_attr = common.getMirrorName(lip_joint)

                    seal_rev = cmds.createNode("reverse", name="{}_seal_rev".format(lip_joint))
                    jaw_attr_rev = cmds.createNode("reverse", name="{}_jaw_rev".format(lip_joint))
                    seal_mult = cmds.createNode("multiplyDivide", name="{}_seal_mult".format(lip_joint))

                    cmds.connectAttr(seal_attr, "{}.inputX".format(seal_rev))
                    cmds.connectAttr("{}.outputX".format(seal_rev), "{}.input2X".format(seal_mult))
                    cmds.connectAttr("{}.outputX".format(seal_rev), "{}.input2Y".format(seal_mult))

                    cmds.connectAttr("{}.{}".format(self.params_hrc, lip_attr), "{}.input1Y".format(seal_mult))
                    cmds.connectAttr("{}.{}".format(self.params_hrc, lip_attr), "{}.inputX".format(jaw_attr_rev))

                    cmds.connectAttr("{}.outputX".format(jaw_attr_rev), "{}.input1X".format(seal_mult))

                    cmds.connectAttr("{}.outputX".format(seal_mult), "{}.{}W0".format(constraint, broad_joint[0]))
                    cmds.connectAttr("{}.outputY".format(seal_mult), "{}.{}W1".format(constraint, broad_joint[1]))

    def createInitalValues(self, part, degree=1.3):
        """

        :param part:
        :param degree:
        :return:
        """

        jaw_attr = [part for part in self.getLipPart(part) if common.getSide(part) == 'l']
        value = len(jaw_attr)

        for index, attr_name in enumerate(jaw_attr[::-1]):
            attr = "{}.{}".format(self.params_hrc, attr_name)

            linear_value = float(index) / float(value-1)

            div_value = linear_value / degree
            final_value = div_value * linear_value

            cmds.setAttr(attr, final_value)

    def createOffsetFollow(self):
        """

        :return:
        """
        # add follow attributes
        cmds.addAttr(self.params_hrc, ln='follow_ty', min=-10, max=10, dv=0)
        cmds.addAttr(self.params_hrc, ln='follow_tz', min=-10, max=10, dv=0)

        uc = node.unitConversion("{}.rx".format(self.jaw_control[-1]), name="{}_auto".format(self.jaw_control[1]))

        mdl_y = node.multDoubleLinear("{}.follow_ty".format(self.params_hrc), -1, name="{}_auto".format(self.jaw_control[1]))

        remap_y = node.remapValue("{}.{}".format(uc, "output"), inMin=0, inMax=1,
                                  outMin=0, outMax="{}.{}".format(mdl_y, "output"), name="{}_auto".format(self.jaw_control[1]))
        remap_z = node.remapValue("{}.{}".format(uc, "output"), inMin=0, inMax=1,
                                  outMin=0, outMax="{}.{}".format(self.params_hrc, "follow_tz"), name="{}_auto".format(self.jaw_control[1]))

        cmds.connectAttr("{}.outValue".format(remap_y), "{}.ty".format(self.jaw_control[1]))
        cmds.connectAttr("{}.outValue".format(remap_z), "{}.tz".format(self.jaw_control[1]))

    def createSealParams(self):
        """
        :return:
        """

        cmds.addAttr(self.params_hrc, at='double', ln='l_seal', min=0, max=10, dv=0)
        cmds.addAttr(self.params_hrc, at='double', ln='r_seal', min=0, max=10, dv=0)

        cmds.addAttr(self.params_hrc, at='double', ln='l_seal_falloff', min=0, max=10, dv=4)
        cmds.addAttr(self.params_hrc, at='double', ln='r_seal_falloff', min=0, max=10, dv=4)

    def connectSeal(self, part):
        """

        :return:
        """

        lip_joints = self.getLipPart(part)

        triggers = {"l": list(), "r": list()}

        value = len(lip_joints)
        seal_driver = cmds.createNode("lightInfo", n="{}_seal_{}_drvr".format(self.name, part))

        for side in 'lr':
            # get falloff
            delay_pma = node.plusMinusAverage1D([10, "{}.{}_seal_falloff".format(self.params_hrc, side)],
                                                operation='sub', name='{}_seal_{}_{}_delay'.format(self.name, side, part))
            lerp = 1.0 / float(value-1)

            delay_div = node.multDoubleLinear(input1="{}.{}".format(delay_pma, 'output1D'), input2=lerp,
                                              name="{}_seal_{}_{}_div".format(self.name, side, part))

            mult_triggers = list()
            sub_triggers = list()
            triggers[side].append(mult_triggers)
            triggers[side].append(sub_triggers)

            for index in range(value):
                indexName = "{}_{:02d}".format(self.name, index)

                delay_mult = node.multDoubleLinear(index, "{}.{}".format(delay_div, 'output'), name="{}_seal_{}_{}".format(indexName, side, part))
                mult_triggers.append(delay_mult)

                sub_delay = node.plusMinusAverage1D(["{}.{}".format(delay_mult, "output"),
                                                     "{}.{}_seal_falloff".format(self.params_hrc, side)],
                                                    operation='sum', name="{}_seal_{}_{}".format(indexName, side, part))
                sub_triggers.append(sub_delay)

        for l_index in range(value):
            r_index = value-l_index -1
            indexName = "{}_seal_{}_{}".format(self.name, part, l_index)

            l_mult_trigger, l_sub_trigger = triggers['l'][0][l_index], triggers['l'][1][l_index]
            r_mult_trigger, r_sub_trigger = triggers['r'][0][r_index], triggers['r'][1][r_index]

            # left network
            l_remap = node.remapValue("{}.{}_seal".format(self.params_hrc, 'l'),
                                      inMin="{}.{}".format(l_mult_trigger, "output"),
                                      inMax="{}.{}".format(l_sub_trigger, "output1D"),
                                      outMax=1, interp='smooth', name="{}_seal_{}_{}".format(indexName, 'l', part))
            # right network
            r_sub = node.plusMinusAverage1D([1, "{}.{}".format(l_remap, "outValue")], operation='sub', name="{}_offset_seal_r_{}_sub".format(indexName, part))

            r_remap = node.remapValue("{}.{}_seal".format(self.params_hrc, 'r'),
                                      inMin="{}.{}".format(r_mult_trigger, "output"),
                                      inMax="{}.{}".format(r_sub_trigger, "output1D"),
                                      outMax="{}.{}".format(r_sub, "output1D"),
                                      interp='smooth', name="{}_seal_{}_{}".format(indexName, 'r', part))

            # final addition of both sides
            sum = node.plusMinusAverage1D(["{}.{}".format(l_remap, "outValue"), "{}.{}".format(r_remap, "outValue")],
                                          name="{}_sum".format(indexName))

            clamp = node.remapValue("{}.output1D".format(sum),name="{}_clamp".format(indexName))

            cmds.addAttr(seal_driver, at="double", ln=indexName, min=0, max=1, dv=0)
            cmds.connectAttr("{}.{}".format(clamp, 'outValue'),"{}.{}".format(seal_driver, indexName))

            # get the constraint
            constraint = cmds.ls(cmds.listRelatives(lip_joints[l_index], c=True), type='parentConstraint')[0]
            seal_attr = cmds.listAttr(constraint, ud=True)[-1]

            cmds.connectAttr("{}.{}".format(seal_driver, indexName), "{}.{}".format(constraint, seal_attr))

    def createCornerPinning(self):
        """

        :return:
        """

        for side in 'lr':
            cmds.addAttr(self.params_hrc, at='double', ln='{}_corner_pin'.format(side), min=-1, max=1, dv=0)

            remap = node.remapValue("{}.{}_corner_pin".format(self.params_hrc, side), inMin=-1, inMax=1, outMin=0, outMax=1,
                                    name="{}_{}_cornerPin".format(self.name, side))
            rev = node.reverse("{}.{}".format(remap, 'outValue'), name="{}_{}_cornerPin".format(self.name, side))

            trsbuffer = self.l_corner_control[0] if side == 'l' else self.r_corner_control[0]
            constraint = cmds.ls(cmds.listRelatives(trsbuffer, c=True), type='parentConstraint')[0]
            constraint_tgts = cmds.listAttr(constraint, ud=True)
            cmds.connectAttr("{}.{}".format(rev, 'outputX'), "{}.{}".format(constraint, constraint_tgts[1]))
            cmds.connectAttr("{}.{}".format(remap, 'outValue'), "{}.{}".format(constraint, constraint_tgts[0]))

    def setupAnimAttrs(self):

        for side in 'lr':
            control = self.l_corner_control[-1] if side == 'l' else self.r_corner_control[-1]
            attr.addSeparator(control, '---')
            cmds.addAttr(control, ln='corner_pin', at='double', min=-1, max=1, dv=0, k=True)
            cmds.connectAttr("{}.corner_pin".format(control), "{}.{}_corner_pin".format(self.params_hrc, side))

            cmds.addAttr(control, ln='seal', at='double', min=0, max=10, dv=0, k=True)
            cmds.connectAttr("{}.seal".format(control), "{}.{}_seal".format(self.params_hrc, side))

            cmds.addAttr(control, ln='seal_falloff', at='double', min=0, max=10, dv=4, k=True)
            cmds.connectAttr("{}.seal_falloff".format(control), "{}.{}_seal_falloff".format(self.params_hrc, side))








