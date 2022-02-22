"""
This Module contains
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2

import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.node as node
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.attr as attr


def showPsdReaders():
    """ Show all Psd Readers in the scene"""
    readers = meta.getTagged("poseReader")
    for reader in readers:
        cmds.setAttr("{}.{}".format(reader, "v"), 1)


def hidePsdReaders():
    """ Hide all Psd readers in the scene"""
    readers = meta.getTagged("poseReader")
    for reader in readers:
        cmds.setAttr("{}.{}".format(reader, "v"), 0)


def deletePsdReader(joints):
    """
    Delete the pose reader associated with a given joint
    :param joints: joints to delete the pose readers on
    :return:
    """
    joints = common.toList(joints)

    for jnt in joints:
        if not cmds.objExists("{}.{}".format(jnt, "PsdHrc")):
            continue
        reader_hrc = meta.getMessageConnection("{}.{}".format(jnt, "PsdHrc"))
        if reader_hrc:
            cmds.delete(reader_hrc)

        # delete the attrs if they exist
        for attr in ["PsdHrc", "PsdOutput", "SwingPsdReader"]:
            if cmds.objExists("{}.{}".format(jnt, attr)):
                cmds.deleteAttr("{}.{}".format(jnt, attr))


def initalizePsds():
    """This will initalize the pose reader parent group"""
    if not cmds.objExists("pose_readers"):
        root = cmds.createNode("transform", n="pose_readers")
        if cmds.objExists("rig"):
            cmds.parent(root, "rig")


def createPsdReader(joint, twist=False, swing=True, parent=False):
    """
    Create a Pose space reader on the given joint
    :param joint: joint to create the pose reader on
    :param twist: Add the twist attribute to the pose reader
    :param swing: Add swing attributes to the pose reader
    :param parent: Parent in the rig for the pose reader
    :return:
    """
    # initalize an envornment for our Psds to go to
    initalizePsds()

    joint = common.getFirstIndex(joint)
    aimJoint = joint
    if not cmds.listRelatives(joint, type="joint"):
        aimJoint = cmds.listRelatives(joint, type="joint", p=True)
    if not aimJoint:
        raise RuntimeError("Could not determine axis from joint {}".format(joint))
    if not parent:
        parent = 'pose_readers'

    # Create a group for the pose reader hierarchy
    hrc = "{}_poseReader_hrc".format(joint)
    if not cmds.objExists(hrc):
        hrc = cmds.createNode("transform", n="{}_poseReader_hrc".format(joint))
    # setup the hirarchy node.
    rig_transform.matchTransform(joint, hrc)
    attr.lock(hrc, attr.TRANSFORMS + ['v'])
    meta.addMessageConnection(joint, hrc, sourceAttr="PsdHrc")

    # create and setup the output parameter node.
    # This is stored on a separate node to reduce any cycle clusters in parallel eval.
    output = cmds.createNode("transform", n="{}_poseReader_out".format(joint))
    attr.lockAndHide(output, attr.TRANSFORMS + ['v'])
    cmds.parent(output, hrc)
    meta.addMessageConnection(joint, output, sourceAttr="PsdOutput")

    # TODO: add twist reader
    # add attributes to the joint so we have an access point for later
    aimAxis = rig_transform.getAimAxis(aimJoint, allowNegative=False)
    if twist:
        if not cmds.objExists("{}.twist_{}".format(output, aimAxis)):
            cmds.addAttr(output, longName='twist_{}'.format(aimAxis), k=True)
        twistAttr = "{}.{}".format(output, 'twist_{}'.format(aimAxis))
        __createTwistPsdReader(joint, aimAxis=aimAxis, outputAttr=twistAttr)

    if swing:
        if not cmds.objExists("{}.{}".format(joint, "SwingPsdReader")):
            outputAttrsList = list()
            # build the attributes and add them to a list!
            for axis in [a for a in 'xyz' if a != aimAxis]:
                if not cmds.objExists("{}.swing_{}".format(output, axis)):
                    cmds.addAttr(output, longName='swing_{}'.format(axis), k=True)
                outputAttrsList.append("{}.{}".format(output, 'swing_{}'.format(axis)))
                __createSwingPsdReader(joint, aimAxis=aimAxis, parent=hrc, outputAttrs=outputAttrsList)
        else:
            cmds.warning("Pose reader already exists on the joint '{}'".format(joint))

    if parent and cmds.objExists(parent):
        hrc_parent = cmds.listRelatives(hrc, p=True) or ['']
        if hrc_parent[0] != parent:
            cmds.parent(hrc, parent)


def __createTwistPsdReader(joint, aimAxis='x', outputAttr=None):
    """create a twist pose reader"""

    parentList = cmds.listRelatives(joint, parent=True, path=True)
    parent_trs = parentList[0] if parentList else None

    mm = cmds.createNode("multMatrix", name="{}_local_mm".format(joint))
    worldMatrix = "{}.worldMatrix[0]".format(joint)
    cmds.connectAttr(worldMatrix, "{}.matrixIn[0]".format(mm))

    if parent_trs:
        parentInverse = "{}.worldInverseMatrix[0]".format(parent_trs)
        cmds.connectAttr(parentInverse, "{}.matrixIn[1]".format(mm))

        # inverse the parent matrix
        pinv = om2.MMatrix(cmds.getAttr(parentInverse))
        m = om2.MMatrix(cmds.getAttr(worldMatrix))
        invLocalRest = (m * pinv).inverse()
        cmds.setAttr("{}.matrixIn[2]".format(mm), list(invLocalRest), type='matrix')

    rotation = cmds.createNode("decomposeMatrix", name='{}_rotation_{}'.format(joint, "dcmp"))

    cmds.connectAttr("{}.matrixSum".format(mm), "{}.inputMatrix".format(rotation))
    twist = cmds.createNode('quatNormalize', name='{}_twist_{}'.format(joint, 'quatNormalize'))
    cmds.connectAttr("{}.outputQuatW".format(rotation), "{}.inputQuatW".format(twist))

    cmds.connectAttr("{}.outputQuat{}".format(rotation, aimAxis.upper()), "{}.inputQuat{}".format(twist, aimAxis.upper()))
    twistEuler = cmds.createNode("quatToEuler", name="{}_twistEuler_quatToEuler".format(joint))
    cmds.setAttr("{}.inputRotateOrder".format(twistEuler), cmds.getAttr("{}.rotateOrder".format(joint)))
    cmds.connectAttr("{}.outputQuat".format(twist),"{}.inputQuat".format(twistEuler))

    remap = cmds.createNode("remapValue", name="{}_normalizeValue_remap".format(joint))
    cmds.connectAttr("{}.outputRotate{}".format(twistEuler, aimAxis.upper()), "{}.inputValue".format(remap))
    cmds.setAttr("{}.inputMin".format(remap), -180)
    cmds.setAttr("{}.inputMax".format(remap),  180)
    cmds.setAttr("{}.outputMin".format(remap), -2)
    cmds.setAttr("{}.outputMax".format(remap),  2)

    # # connect outputs
    if cmds.objExists(outputAttr):
        cmds.connectAttr("{}.outValue".format(remap), outputAttr)


def __createSwingPsdReader(joint, aimJoint=None, aimAxis='x', parent=None, outputAttrs=list()):
    """ create a swing pose reader """
    if not aimJoint:
        aimJoint = joint

    aimAxisVector = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(aimJoint))

    # create the pose reader nurbs.
    pose_reader = cmds.sphere(s=2, nsp=2, axis=aimAxisVector, n=joint + "_poseReader", ch=False)[0]
    cmds.rebuildSurface(pose_reader, ch=0, rpo=1, end=1, kr=0, kcp=1, su=2, sv=2)
    pose_reader_shape = cmds.ls(cmds.listRelatives(pose_reader, c=True), type='nurbsSurface')[0]
    rig_transform.matchTransform(joint, pose_reader)
    cmds.parent(pose_reader, parent)

    # create a point to reference. This is alittle Hacky.
    # We build a transform to offset in the proper space
    # then create a offset matrix relationship and hijack the output and delete the created node.
    reader_pt = cmds.createNode("transform", n="{}_posePoint".format(joint))
    rig_transform.matchTransform(joint, reader_pt)
    cmds.move(aimAxisVector[0], aimAxisVector[1], aimAxisVector[2], reader_pt, r=True, os=True)
    mm, dcmp = rig_transform.connectOffsetParentMatrix(joint, reader_pt, mo=True)

    # Create the closest point node network
    vprod = cmds.createNode("vectorProduct", n="{}_vprod".format(joint))
    closest = cmds.createNode("closestPointOnSurface", n="{}_closestPointOnSurface".format(joint))

    cmds.connectAttr("{}.matrixSum".format(mm), "{}.matrix".format(vprod))
    cmds.setAttr("{}.operation".format(vprod), 4)
    cmds.connectAttr("{}.output".format(vprod), "{}.inPosition".format(closest))
    cmds.connectAttr("{}.worldSpace".format(pose_reader_shape), "{}.inputSurface".format(closest))

    # after we use the reader point delete the node
    cmds.delete(reader_pt)

    suffix_list = ["z_neg", 'y_neg', 'z_pos', 'y_pos']
    zone_num = 4

    # create four sets of texture maps
    zone_output_list = list()
    for i in range(zone_num):
        u_ramp = cmds.createNode('ramp', n='{}_uRamp_{}'.format(joint, suffix_list[i]))
        v_ramp = cmds.createNode('ramp', n='{}_vRamp_{}'.format(joint, suffix_list[i]))

        # connect the attributes
        cmds.connectAttr("{}.{}".format(closest, "parameterU"), "{}.{}".format(u_ramp, "uCoord"))
        cmds.connectAttr("{}.{}".format(closest, "parameterV"), "{}.{}".format(v_ramp, "vCoord"))

        # setup the U ramp
        cmds.setAttr("{}.type".format(u_ramp), 1)
        cmds.setAttr("{}.colorEntryList[1].color".format(u_ramp), 1, 1, 1, type="double3")
        cmds.setAttr("{}.colorEntryList[0].color".format(u_ramp), 0, 0, 0, type="double3")
        cmds.setAttr("{}.colorEntryList[0].position".format(u_ramp), 1)

        # setup the V ramp
        cmds.setAttr("{}.type".format(v_ramp), 0)
        for zone in range(0, zone_num + 1):
            if zone == i:
                cmds.setAttr("{}.colorEntryList[{}].color".format(v_ramp, zone), 1, 1, 1, type="double3")
            else:
                cmds.setAttr("{}.colorEntryList[{}].color".format(v_ramp, zone), 0, 0, 0, type="double3")

            # if it is the first zone make the last zone white too
            if i == 0: cmds.setAttr("{}.colorEntryList[{}].color".format(v_ramp, zone_num), 1, 1, 1, type="double3")
            cmds.setAttr("{}.colorEntryList[{}].position".format(v_ramp, zone), float(zone) * 1 / float(zone_num))

        mdl = cmds.createNode("multDoubleLinear", n='{}_{}_mdl'.format(joint, suffix_list[i]))
        cmds.connectAttr("{}.{}".format(u_ramp, "outColorR"), "{}.{}".format(mdl, "input1"))
        cmds.connectAttr("{}.{}".format(v_ramp, "outColorR"), "{}.{}".format(mdl, "input2"))

        # create a multiplier
        rev = cmds.createNode("multDoubleLinear", n='{}_{}_reverse_mdl'.format(joint, suffix_list[i]))
        cmds.connectAttr("{}.{}".format(mdl, "output"), "{}.{}".format(rev, "input1"))

        if 'neg' in suffix_list[i]:
            cmds.setAttr("{}.{}".format(rev, "input2"), -2)
        else:
            cmds.setAttr("{}.{}".format(rev, "input2"), 2)
        zone_output_list.append(rev)

    # create a conditional
    for i, axis in enumerate([a for a in 'xyz' if a != aimAxis]):
        zones = zone_output_list[i::2]
        neg_zone = zones[0]
        pos_zone = zones[-1]

        # setup the condition node
        cond = cmds.createNode("condition", n="{}_{}_cond".format(joint, axis))
        cmds.connectAttr("{}.{}".format(pos_zone, 'output'), "{}.{}".format(cond, "firstTerm"))
        cmds.setAttr("{}.{}".format(cond, "operation"), 2)
        cmds.connectAttr("{}.{}".format(neg_zone, 'output'), "{}.{}".format(cond, "colorIfFalseR"))
        cmds.connectAttr("{}.{}".format(pos_zone, 'output'), "{}.{}".format(cond, "colorIfTrueR"))
        cmds.connectAttr("{}.{}".format(cond, "outColorR"), outputAttrs[i])

        rig_transform.matchTranslate(joint, pose_reader)

    # connect the setup to the parent joint
    t_mm, t_pick = rig_transform.connectOffsetParentMatrix(joint, pose_reader, r=False)
    joint_parents = cmds.ls(cmds.listRelatives(joint, p=True), type='joint')
    if joint_parents:
        parent_joint = joint_parents[0]
        r_mm, r_pick = rig_transform.connectOffsetParentMatrix(parent_joint, pose_reader,
                                                               mo=True, t=False, r=True, s=False, sh=False)
        merge_m = cmds.createNode("multMatrix", n='{}_mergeMat'.format(joint))
        cmds.connectAttr("{}.{}".format(t_pick, "outputMatrix"), "{}.{}".format(merge_m, 'matrixIn[1]'))
        cmds.connectAttr("{}.{}".format(r_pick, "outputMatrix"), "{}.{}".format(merge_m, 'matrixIn[0]'))
        cmds.connectAttr("{}.{}".format(merge_m, 'matrixSum'), "{}.{}".format(pose_reader, 'offsetParentMatrix'),
                         f=True)

    # cleanup the setup
    meta.tag(pose_reader, "poseReader")
    attr.lockAndHide(pose_reader, attr.TRANSFORMS)
    cmds.setAttr("{}.{}".format(pose_reader, "v"), 0)
    meta.addMessageConnection(joint, pose_reader, sourceAttr="SwingPsdReader")

    return pose_reader
