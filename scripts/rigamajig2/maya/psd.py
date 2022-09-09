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
import logging

logger = logging.getLogger(__name__)


def getAssociateJoint(node):
    """
    returns the joint associated with the pose reader node
    :param node: node to get pose reader from.
    :return:
    """
    # first check what node we got. it should be the joint.
    if not cmds.objExists("{}.poseReaderRoot".format(node)):
        raise RuntimeError("'{}' does not have a pose reader assiciated with it.".format(node))
    if meta.hasTag(node, "poseReader"):
        node = meta.getMessageConnection("{}.poseReaderRoot".format(node))
        node = common.getFirstIndex(node)

    return node


def deletePsdReader(joints):
    """
    Delete the pose reader associated with a given joint
    :param joints: joints to delete the pose readers on
    :return:
    """
    joints = common.toList(joints)

    for jnt in joints:
        jnt = getAssociateJoint(jnt)

        if not cmds.objExists("{}.{}".format(jnt, "poseReaderRoot")):
            continue
        readerHierarchy = meta.getMessageConnection("{}.{}".format(jnt, "poseReaderRoot"))
        if readerHierarchy:
            cmds.delete(readerHierarchy)

        # delete the attrs if they exist
        for attr in ["poseReaderRoot", "poseReaderOut", "swingPsdReaderNurbs"]:
            if cmds.objExists("{}.{}".format(jnt, attr)):
                cmds.deleteAttr("{}.{}".format(jnt, attr))


def initalizePsds():
    """This will initalize the pose reader parent group"""
    if not cmds.objExists("pose_readers"):
        root = cmds.createNode("transform", n="pose_readers")
        if cmds.objExists("rig"):
            cmds.parent(root, "rig")


def getAllPoseReaders():
    """
    Get all pose readers in the scene
    :return: a list of pose readers
    """
    return meta.getTagged('poseReader')


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

    if cmds.objExists("{}.{}".format(joint, "poseReaderRoot")):
        logger.warning("Joint {} already has a pose reader".format(joint))
        return

    # Create a group for the pose reader hierarchy
    hrc = "{}_poseReader_hrc".format(joint)
    if not cmds.objExists(hrc):
        hrc = cmds.createNode("transform", n="{}_poseReader_hrc".format(joint))
    # setup the hirarchy node.
    rig_transform.matchTransform(joint, hrc)
    attr.lock(hrc, attr.TRANSFORMS + ['v'])
    meta.createMessageConnection(joint, hrc, sourceAttr="poseReaderRoot")
    meta.tag(hrc, "poseReader")

    # create and setup the output parameter node.
    # This is stored on a separate node to reduce any cycle clusters in parallel eval.
    output = cmds.createNode("transform", n="{}_poseReader_out".format(joint))
    attr.lockAndHide(output, attr.TRANSFORMS + ['v'])
    cmds.parent(output, hrc)
    meta.createMessageConnection(joint, output, sourceAttr="poseReaderOut")

    # add attributes to the joint so we have an access point for later
    aimAxis = rig_transform.getAimAxis(aimJoint, allowNegative=False)
    if twist:
        if not cmds.objExists("{}.twist_{}".format(output, aimAxis)):
            cmds.addAttr(output, longName='twist_{}'.format(aimAxis), k=True)
        twistPlug = "{}.{}".format(output, 'twist_{}'.format(aimAxis))
        createTwistPsdReader(joint, aimAxis=aimAxis, outputAttr=twistPlug)
        attr.lock(output, "twist_{}".format(aimAxis))

    if swing:
        if not cmds.objExists("{}.{}".format(joint, "swingPsdReaderNurbs")):
            outputPlugsList = list()
            # build the attributes and add them to a list!
            for axis in [a for a in 'xyz' if a != aimAxis]:
                if not cmds.objExists("{}.swing_{}".format(output, axis)):
                    cmds.addAttr(output, longName='swing_{}'.format(axis), k=True)
                outputPlugsList.append("{}.{}".format(output, 'swing_{}'.format(axis)))

            createSwingPsdReader(joint, aimAxis=aimAxis, parent=hrc, outputAttrs=outputPlugsList)

            for plug in outputPlugsList:
                attrName = plug.split(".")[-1]
                attr.lock(output, attrName)

        else:
            cmds.warning("Pose reader already exists on the joint '{}'".format(joint))

    if parent and cmds.objExists(parent):
        hierarchyParent = cmds.listRelatives(hrc, p=True) or ['']
        if hierarchyParent[0] != parent:
            cmds.parent(hrc, parent)

    # to create the swing and twist combos do those here
    if twist and swing:
        attr.addSeparator(output, "combos")
        twistInput = cmds.listConnections(twistPlug, s=True, d=False, p=True)
        for swingPlug in outputPlugsList:
            swingInput = cmds.listConnections(swingPlug, s=True, d=False, p=True)
            swingAttrName = swingPlug.split(".")[-1]
            twistAttrName = twistPlug.split(".")[-1]
            cmds.addAttr(output, longName="{}_{}_combo".format(swingAttrName, twistAttrName), k=True)
            comboOutputAttr = "{}_{}_combo".format(swingAttrName, twistAttrName)
            comboOutputPlug = "{}.{}".format(output, comboOutputAttr)

            mdlName = "{}_{}_{}_combo".format(joint, swingAttrName, twistAttrName)
            node.multDoubleLinear(swingInput[0], twistInput[0], comboOutputPlug, name=mdlName)
            attr.lock(output, comboOutputAttr)

    logger.info("Created pose reader on joint '{}'".format(joint, twist, swing))


def createTwistPsdReader(joint, aimAxis='x', outputAttr=None):
    """create a twist pose reader"""

    parentList = cmds.listRelatives(joint, parent=True, path=True)
    parentTrs = parentList[0] if parentList else None

    multMatrix = cmds.createNode("multMatrix", name="{}_local_mm".format(joint))
    worldMatrix = "{}.worldMatrix[0]".format(joint)
    cmds.connectAttr(worldMatrix, "{}.matrixIn[0]".format(multMatrix))

    if parentTrs:
        parentInverseAttr = "{}.worldInverseMatrix[0]".format(parentTrs)
        cmds.connectAttr(parentInverseAttr, "{}.matrixIn[1]".format(multMatrix))

        # inverse the parent matrix
        parentInverseMatrix = om2.MMatrix(cmds.getAttr(parentInverseAttr))
        matrix = om2.MMatrix(cmds.getAttr(worldMatrix))
        invLocalRest = (matrix * parentInverseMatrix).inverse()
        cmds.setAttr("{}.matrixIn[2]".format(multMatrix), list(invLocalRest), type='matrix')

    rotation = cmds.createNode("decomposeMatrix", name='{}_rotation_{}'.format(joint, "dcmp"))

    cmds.connectAttr("{}.matrixSum".format(multMatrix), "{}.inputMatrix".format(rotation))
    twist = cmds.createNode('quatNormalize', name='{}_twist_{}'.format(joint, 'quatNormalize'))
    cmds.connectAttr("{}.outputQuatW".format(rotation), "{}.inputQuatW".format(twist))

    cmds.connectAttr("{}.outputQuat{}".format(rotation, aimAxis.upper()),
                     "{}.inputQuat{}".format(twist, aimAxis.upper()))
    twistEuler = cmds.createNode("quatToEuler", name="{}_twistEuler_quatToEuler".format(joint))
    cmds.setAttr("{}.inputRotateOrder".format(twistEuler), cmds.getAttr("{}.rotateOrder".format(joint)))
    cmds.connectAttr("{}.outputQuat".format(twist), "{}.inputQuat".format(twistEuler))

    remap = cmds.createNode("remapValue", name="{}_normalizeValue_remap".format(joint))
    cmds.connectAttr("{}.outputRotate{}".format(twistEuler, aimAxis.upper()), "{}.inputValue".format(remap))
    cmds.setAttr("{}.inputMin".format(remap), -180)
    cmds.setAttr("{}.inputMax".format(remap), 180)
    cmds.setAttr("{}.outputMin".format(remap), -2)
    cmds.setAttr("{}.outputMax".format(remap), 2)

    # # connect outputs
    if cmds.objExists(outputAttr):
        cmds.connectAttr("{}.outValue".format(remap), outputAttr)


# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
def createSwingPsdReader(joint, aimJoint=None, aimAxis='x', parent=None, outputAttrs=None):
    """ create a swing pose reader """

    outputAttrs = outputAttrs or list()
    if not aimJoint:
        aimJoint = joint

    aimAxisVector = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(aimJoint))

    # create the pose reader nurbs.
    poseReader = cmds.sphere(s=2, nsp=2, axis=aimAxisVector, n=joint + "_poseReader", ch=False)[0]
    cmds.rebuildSurface(poseReader, ch=0, rpo=1, end=1, kr=0, kcp=1, su=2, sv=2)
    poseReaderShape = cmds.ls(cmds.listRelatives(poseReader, c=True), type='nurbsSurface')[0]
    rig_transform.matchTransform(joint, poseReader)
    cmds.parent(poseReader, parent)

    # create a point to reference. This is alittle Hacky.
    # We build a transform to offset in the proper space
    # then create a offset matrix relationship and hijack the output and delete the created node.
    readerPoint = cmds.createNode("transform", n="{}_posePoint".format(joint))
    rig_transform.matchTransform(joint, readerPoint)
    cmds.move(aimAxisVector[0], aimAxisVector[1], aimAxisVector[2], readerPoint, r=True, os=True)
    multMatrix, decompMatrix = rig_transform.connectOffsetParentMatrix(joint, readerPoint, mo=True)

    # Create the closest point node network
    vprod = cmds.createNode("vectorProduct", n="{}_vprod".format(joint))
    closest = cmds.createNode("closestPointOnSurface", n="{}_closestPointOnSurface".format(joint))

    cmds.connectAttr("{}.matrixSum".format(multMatrix), "{}.matrix".format(vprod))
    cmds.setAttr("{}.operation".format(vprod), 4)
    cmds.connectAttr("{}.output".format(vprod), "{}.inPosition".format(closest))
    cmds.connectAttr("{}.worldSpace".format(poseReaderShape), "{}.inputSurface".format(closest))

    # after we use the reader point delete the node
    cmds.delete(readerPoint)

    suffixList = ["z_neg", 'y_neg', 'z_pos', 'y_pos']
    zoneNumber = 4

    # create four sets of texture maps
    zoneOutputList = list()
    for i in range(zoneNumber):
        uRamp = cmds.createNode('ramp', n='{}_uRamp_{}'.format(joint, suffixList[i]))
        vRamp = cmds.createNode('ramp', n='{}_vRamp_{}'.format(joint, suffixList[i]))

        # connect the attributes
        cmds.connectAttr("{}.{}".format(closest, "parameterU"), "{}.{}".format(uRamp, "uCoord"))
        cmds.connectAttr("{}.{}".format(closest, "parameterV"), "{}.{}".format(vRamp, "vCoord"))

        # setup the U ramp
        cmds.setAttr("{}.type".format(uRamp), 1)
        cmds.setAttr("{}.colorEntryList[1].color".format(uRamp), 1, 1, 1, type="double3")
        cmds.setAttr("{}.colorEntryList[0].color".format(uRamp), 0, 0, 0, type="double3")
        cmds.setAttr("{}.colorEntryList[0].position".format(uRamp), 1)

        # setup the V ramp
        cmds.setAttr("{}.type".format(vRamp), 0)
        for zone in range(0, zoneNumber + 1):
            if zone == i:
                cmds.setAttr("{}.colorEntryList[{}].color".format(vRamp, zone), 1, 1, 1, type="double3")
            else:
                cmds.setAttr("{}.colorEntryList[{}].color".format(vRamp, zone), 0, 0, 0, type="double3")

            # if it is the first zone make the last zone white too
            if i == 0: cmds.setAttr("{}.colorEntryList[{}].color".format(vRamp, zoneNumber), 1, 1, 1, type="double3")
            cmds.setAttr("{}.colorEntryList[{}].position".format(vRamp, zone), float(zone) * 1 / float(zoneNumber))

        mdl = cmds.createNode("multDoubleLinear", n='{}_{}_mdl'.format(joint, suffixList[i]))
        cmds.connectAttr("{}.{}".format(uRamp, "outColorR"), "{}.{}".format(mdl, "input1"))
        cmds.connectAttr("{}.{}".format(vRamp, "outColorR"), "{}.{}".format(mdl, "input2"))

        # create a multiplier
        rev = cmds.createNode("multDoubleLinear", n='{}_{}_reverse_mdl'.format(joint, suffixList[i]))
        cmds.connectAttr("{}.{}".format(mdl, "output"), "{}.{}".format(rev, "input1"))

        # TODO: check if the axis semi-aligns with the world axises.
        if 'neg' in suffixList[i]:
            cmds.setAttr("{}.{}".format(rev, "input2"), -2)
        else:
            cmds.setAttr("{}.{}".format(rev, "input2"), 2)
        zoneOutputList.append(rev)

    # create a conditional
    for i, axis in enumerate([a for a in 'xyz' if a != aimAxis]):
        zones = zoneOutputList[i::2]
        negativeZone = zones[0]
        positiveZone = zones[-1]

        # setup the condition node
        cond = cmds.createNode("condition", n="{}_{}_cond".format(joint, axis))
        cmds.connectAttr("{}.{}".format(positiveZone, 'output'), "{}.{}".format(cond, "firstTerm"))
        cmds.setAttr("{}.{}".format(cond, "operation"), 2)
        cmds.connectAttr("{}.{}".format(negativeZone, 'output'), "{}.{}".format(cond, "colorIfFalseR"))
        cmds.connectAttr("{}.{}".format(positiveZone, 'output'), "{}.{}".format(cond, "colorIfTrueR"))
        cmds.connectAttr("{}.{}".format(cond, "outColorR"), outputAttrs[i], f=True)

        rig_transform.matchTranslate(joint, poseReader)

    # connect the setup to the parent joint
    transformMultMatrix, transformPick = rig_transform.connectOffsetParentMatrix(joint, poseReader, r=False)
    jointParents = cmds.ls(cmds.listRelatives(joint, p=True), type='joint')
    if jointParents:
        parentJoint = jointParents[0]
        rotateMultMatrix, rotatePick = rig_transform.connectOffsetParentMatrix(parentJoint, poseReader, mo=True,
                                                                               t=False, r=True, s=False, sh=False)
        multMatrix = cmds.createNode("multMatrix", n='{}_mergeMat'.format(joint))
        cmds.connectAttr("{}.{}".format(transformPick, "outputMatrix"), "{}.{}".format(multMatrix, 'matrixIn[1]'))
        cmds.connectAttr("{}.{}".format(rotatePick, "outputMatrix"), "{}.{}".format(multMatrix, 'matrixIn[0]'))
        cmds.connectAttr("{}.{}".format(multMatrix, 'matrixSum'), "{}.{}".format(poseReader, 'offsetParentMatrix'),
                         f=True)

    # cleanup the setup
    attr.lockAndHide(poseReader, attr.TRANSFORMS)
    cmds.setAttr("{}.{}".format(poseReader, "v"), 0)
    meta.createMessageConnection(joint, poseReader, sourceAttr="swingPsdReaderNurbs")

    return poseReader
