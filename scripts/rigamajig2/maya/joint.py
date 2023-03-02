"""
functions for Joints
"""
import maya.cmds as cmds
import maya.api.OpenMaya as om2

from rigamajig2.shared import common
from rigamajig2.maya import mathUtils
from rigamajig2.maya import naming
from rigamajig2.maya import attr
from rigamajig2.maya import transform
from rigamajig2.maya import decorators
from rigamajig2.maya import meta


def isJoint(joint):
    """
    Check if the joint is a valud joint

    :param str list joint: name of the joint to check
    :return: True if Valid. False is invalid.
    :rtype: bool
    """
    joint = common.getFirstIndex(joint)
    if not cmds.objExists(joint) or not cmds.nodeType(joint) == 'joint': return False
    return True


def isEndJoint(joint):
    """
    Check if a joint is an end joint

    :param str list joint: name of a joint
    :return: True if the joint is an end joint
    :rtype: bool
    """
    joint = common.getFirstIndex(joint)
    if not isJoint(joint):
        return False
    decendents = cmds.ls(cmds.listRelatives(joint, ad=True) or [], type='joint')
    if not decendents: return True
    return False


def isClean(joint):
    """
    Check if a list of joints have clean orientation.
    We assume joints are clean when there are no transform values exept a single translate channel

    :param str list joint: name of a joint to check if the transforms are clean
    :return: True if the tranforms are clean
    :rtype: bool
    """
    joint = common.getFirstIndex(joint)
    dirtyChannels = list()
    for attr in ["{}{}".format(x, y) for x in 'tr' for y in 'xyz']:
        if abs(cmds.getAttr("{}.{}".format(joint, attr))) > .001:
            dirtyChannels.append(attr)

    if len(dirtyChannels) == 1:
        return True
    return False


def addJointOrientToChannelBox(joints):
    """
    Add the joint orient information to the channel box.
    This can be super handy to make sure its easy to check and edit the joint orientations

    :param str list joints: name of the joint to add the joint
    """
    joints = common.toList(joints)
    for jnt in joints:
        if not cmds.objExists(jnt):
            raise Exception("{} does not exist in the scene".format(jnt))
        for attr in ['jointOrientX', 'jointOrientY', 'jointOrientZ']:
            cmds.setAttr(jnt + '.' + attr, cb=True, k=True)
            cmds.setAttr(jnt + '.' + attr, k=True)


def length(joint):
    """
    Get the length of a joint

    :param str joint: joint to get the length of
    :return: length of the joint
    :rtype: float
    """
    if not isJoint(joint):
        cmds.error('{} is not a joint'.format(joint))
        return
    if isEndJoint(joint):
        cmds.warning("{} is an end joint and has no length".format(joint))

    decendents = cmds.ls(cmds.listRelatives(joint, c=True) or [], type='joint')
    if decendents:
        childJoint = decendents[0]
        startPos = cmds.xform(joint, q=True, ws=True, t=True)
        endPos = cmds.xform(childJoint, q=True, ws=True, t=True)
        return mathUtils.distance(startPos, endPos)


def setRadius(joints, radius=1):
    """
    Set the radius for a list of joints
    :param list joints: list of joint to set the radius of
    :param float radius: radius to set on a list of joints
    """
    joints = common.toList(joints)
    for j in joints:
        if isJoint(j):
            cmds.setAttr("{}.radius".format(j), radius)


def duplicateChain(jointList, parent=None, names=None):
    """
    Duplicate the joint chain without clashing names.
    Optionally you can pass in a list of names to rename the new joints

    :param list jointList: joints to duplicate
    :param str parent: Optional- reparent the new hirarchy under this
    :param list names: Optional - add a prefix to th created joints
    :return: list of joints created
    :rtype: list
    """
    newJointList = list()
    if not names:
        names = [x + '_dup' for x in jointList]
    for joint, name in zip(jointList, names):
        if not cmds.objExists(joint):
            continue
        newJoint = cmds.createNode('joint', name=name)
        newJointList.append(newJoint)
        if parent:
            cmds.parent(newJoint, parent)
        cmds.delete(cmds.parentConstraint(joint, newJoint))
        toOrientation(newJoint)
        parent = newJoint

    return newJointList


@decorators.oneUndo
def insertJoints(startJoint, endJoint, amount=1, name=None):
    """
    Insert more joints between a start and end joint

    :param str list startJoint: joint to start from
    :param str list endJoint: joint to end inbetweens at
    :param int amount: amount of joints to insert
    :param str name: name of new joints
    :return: list if new joints inserted between the start and end joints
    :rtype: list
    """
    jointList = list()
    multiplier = float(1.0 / (amount + 1.0))
    if not name: name = startJoint

    childJoints = cmds.listRelatives(startJoint, c=True) or []
    if endJoint not in childJoints:
        cmds.error("{} is not a child of {}".format(endJoint, startJoint))
        return

    startPos = cmds.xform(startJoint, q=True, ws=True, t=True)
    endPos = cmds.xform(endJoint, q=True, ws=True, t=True)

    for i in range(amount):
        joint = cmds.createNode('joint', n=naming.getUniqueName(name))
        jointList.append(joint)
        pos = mathUtils.vectorLerp(startPos, endPos, multiplier * (i + 1))
        cmds.xform(joint, ws=True, t=pos)
        cmds.delete(cmds.orientConstraint(startJoint, joint, mo=False))
        parentRadius = cmds.getAttr("{}.radius".format(startJoint))
        cmds.setAttr("{}.radius".format(joint), parentRadius)

    reverseList = [startJoint] + jointList + [endJoint]
    reverseList.reverse()
    for i in range(len(reverseList)):
        if i != (len(reverseList) - 1):
            cmds.parent(reverseList[i], reverseList[i + 1])

    addJointOrientToChannelBox(jointList)
    return jointList


def getInbetweenJoints(start, end):
    """
    Return a list of joints between the start and end joints

    :param str start: start joint
    :param str end: end joint
    :return: list of joints from start to end including inbetween joints
    :rtype: list
    """
    btwnJoints = list()
    children = cmds.listRelatives(start, ad=True, type='joint')
    parents = cmds.ls(end, long=True)[0].split("|")[1:-1]
    for jnt in parents:
        if jnt in children:
            btwnJoints.append(str(jnt))
    return [start] + btwnJoints + [end]


@decorators.oneUndo
@decorators.preserveSelection
def toOrientation(joints):
    """
    Remove all values from our rotation channels and add them to the Joint orient

    :param list joints: list of joints to convert to joint orientation
    """
    if not isinstance(joints, (list, tuple)):
        joints = [joints]

    for jnt in joints:
        if not cmds.objExists(jnt):
            continue
        rotateOrder = cmds.xform(jnt, q=True, roo=True)
        cmds.xform(jnt, roo="xyz")
        orient = cmds.xform(jnt, q=True, ws=True, rotation=True)
        cmds.setAttr("{0}.jo".format(jnt), 0, 0, 0)
        cmds.xform(jnt, ws=True, rotation=orient)
        ori = cmds.getAttr(jnt + '.r')[0]
        cmds.setAttr("{0}.jo".format(jnt), *ori)
        for attr in ['rx', 'ry', 'rz']:
            if cmds.getAttr("{}.{}".format(jnt, attr), lock=True):
                cmds.setAttr("{}.{}".format(jnt, attr), lock=False)
            cmds.setAttr("{0}.{1}".format(jnt, attr), 0)
        cmds.xform(jnt, p=True, roo=rotateOrder)
        children = cmds.listRelatives(jnt, c=True, type="joint") or []
        if children:
            cmds.parent(children[0], w=True)
            cmds.setAttr("{0}.rotateAxis".format(jnt), 0, 0, 0)
            cmds.parent(children[0], jnt)
        else:
            cmds.setAttr("{0}.rotateAxis".format(jnt), 0, 0, 0)


@decorators.oneUndo
@decorators.preserveSelection
def toRotation(joints):
    """
    Remove all values from our joint orient channels and add them to the rotation

    :param joints: list of joints to convert to rotation
    """
    if not isinstance(joints, (list, tuple)):
        joints = [joints]
    for jnt in joints:
        if not cmds.objExists(jnt):
            continue
        for attr in ['rx', 'ry', 'rz']:
            if cmds.getAttr(jnt + '.' + attr, lock=True):
                cmds.setAttr(jnt + '.' + attr, lock=False)
        orientation = cmds.xform(jnt, q=True, ws=True, rotation=True)
        cmds.setAttr("{0}.jo".format(jnt), 0, 0, 0)
        cmds.xform(jnt, ws=True, rotation=orientation)


@decorators.oneUndo
@decorators.preserveSelection
def mirror(joints, axis='x', mode='rotate', zeroRotation=True):
    """
    Mirrors of one joint to its mirror across a given axis.
    The node "shouler_l_trs" mirror its position to "shouler_r_trs"

    :param str list joints: joints to mirror
    :param str axis: axis to mirror across. ['x', 'y', 'z']
    :param str mode: mirror mode. 'rotate' mirrors the rotation behaviour where 'translate' mirrors translation behavior as well.
                'translate' more is used more often in the face, 'rotate' in the body.
    :param bool zeroRotation: Zero out rotation after mirroring
    """

    if not isinstance(joints, list):
        joints = [joints]

    # Validate cmds which to mirror axis,
    if axis.lower() not in ('x', 'y', 'z'):
        raise ValueError("Keyword Argument: 'axis' not of accepted value ('x', 'y', 'z').")

    trsVector = ()
    rotVector = ()
    if axis.lower() == 'x':
        trsVector = (-1, 1, 1)
        rotVector = (0, 180, 180)
    elif axis.lower() == 'y':
        trsVector = (1, -1, 1)
        rotVector = (180, 0, 180)
    elif axis.lower() == 'z':
        trsVector = (1, 1, -1)
        rotVector = (180, 180, 0)

    mirroredJointList = list()

    for i, jnt in enumerate(joints):

        destination = common.getMirrorName(jnt)

        if cmds.objExists(jnt) and cmds.objExists(destination) and jnt != destination:

            # parent children
            jointGroup = cmds.createNode('transform')
            children = cmds.listRelatives(destination, type='transform')
            if children:
                cmds.parent(list(set(children)), jointGroup)

            # get position and rotation
            trs = cmds.xform(jnt, q=True, rp=True, ws=True)
            matrix = cmds.xform(jnt, q=True, matrix=True, ws=True)

            # set rotation orientation
            cmds.xform(destination, ws=1, matrix=matrix)
            cmds.xform(destination, ws=True, t=(trs[0] * trsVector[0], trs[1] * trsVector[1], trs[2] * trsVector[2]))
            cmds.xform(destination, ws=True, r=True, ro=rotVector)

            # Mirror mode translate
            if mode == 'translate':
                try:
                    cmds.makeIdentity(destination, apply=1, r=1)
                    cmds.setAttr(destination + '.rz', 180)
                    cmds.makeIdentity(destination, apply=1, r=1)
                except:
                    raise RuntimeError('Could not zeroRotation out {}'.format(destination))

            # set prefered angle
            if cmds.objExists('{}.{}'.format(jnt, 'preferredAngle')):
                preferredAngle = cmds.getAttr('{}.{}'.format(jnt, 'preferredAngle'))[0]
                if cmds.objExists('{}.{}'.format(destination, 'preferredAngle')):
                    cmds.setAttr('{}.{}'.format(destination, 'preferredAngle'),
                                 preferredAngle[0], preferredAngle[1], preferredAngle[2])

            # re-parent children to destination
            if children:
                cmds.parent(children, destination)
            cmds.delete(jointGroup)
            mirroredJointList.append(destination)
        else:
            raise RuntimeError("Node not found: {}".format(destination))

    if zeroRotation:
        toOrientation(mirroredJointList)


@decorators.preserveSelection
def orientJoints(joints, aimAxis='x', upAxis='y', worldUpVector=(0, 1, 0), autoUpVector=False):
    """
    Orient joints using an aim constraint. If using autoUpVector select the only joints you want to orient together.

    ie. if you select the shoulder, elbow and wrist the up vector will keep all three oriented together. however if you
    select the calvical, shoulder, elbow and wrist then the chain will blend between two up vectors for each set of joints.

    :param list joints: joints to orient
    :param str aimAxis: aim axis of the joints. Default 'x'
    :param str upAxis: up axis of the joint. Default 'y'
    :param list tuple worldUpVector: world up vector of the aim Constraint
    :param bool autoUpVector: Auto guess the up vector using the vector pependicular to the joints.
    """
    joints = common.toList(joints)

    aimVector = transform.getVectorFromAxis(aimAxis)
    upVector = transform.getVectorFromAxis(upAxis)

    prevUp = (0, 0, 0)
    for i, joint in enumerate(joints):
        parents = cmds.listRelatives(joint, p=True)
        parent = parents[0] if parents else None
        # if the parent is not in the joint list dont use it as a parent.
        if parent not in joints:
            parent = None

        allChildren = cmds.listRelatives(joint, c=True) if cmds.listRelatives(joint, c=True) else list()
        children = [child for child in allChildren if cmds.nodeType(child) == "joint"]
        if len(children) > 0:
            # get the aim target
            aimTarget = None
            for child in children:
                aimTarget = child
                cmds.parent(child, world=True)

            if aimTarget:
                if autoUpVector or worldUpVector == (0, 0, 0):
                    # Now we need to get three joints to caluclate the cross product
                    jointPos = cmds.xform(joint, q=True, ws=True, rp=True)
                    parentPos = cmds.xform(parent, q=True, ws=True, rp=True) if parent else jointPos

                    # If were not using the parent, or if the parent is in the same position as the currentJoint ...
                    if not parent or mathUtils.pointsEqual(jointPos, parentPos):
                        # ... Then get the first child joint of the aim target.
                        aimChildren = cmds.listRelatives(aimTarget, c=True) if cmds.listRelatives(aimTarget,
                                                                                                  c=True) else list()
                        aimChild = None
                        for child in aimChildren:
                            if cmds.nodeType(child) == 'joint':
                                aimChild = child
                                break
                        worldUpVector = getCrossUpVector(joint, aimTarget, aimChild)

                    # otherwise use the parent and the aimTarget to calculate the up direction.
                    else:
                        worldUpVector = getCrossUpVector(parent, joint, aimTarget)

                # create and delete an aim constraint to orient the joint.
                const = cmds.aimConstraint(aimTarget, joint, aimVector=aimVector, upVector=upVector,
                                           worldUpType="vector", worldUpVector=worldUpVector, mo=False, w=1)
                cmds.delete(const)

            # check the old direction to see if we had a large value change.
            currentUp = mathUtils.normalize(worldUpVector)
            dot = mathUtils.dotProduct(currentUp, prevUp)
            prevUp = worldUpVector

            if i > 0 and dot < 0.0:
                # rotate the joint around the aim axis 180 degrees if we flipped.
                cmds.xform(joint, ra=[aimVector[0] * 180, aimVector[1] * 180, aimVector[2] * 180])
                prevUp = mathUtils.scalarMult(prevUp, -1)

            # Apply rotation values to joint orientation
            toOrientation(joint)

            # reparent children to current joint
            for child in children:
                if cmds.nodeType(child) == 'joint':
                    cmds.parent(child, joint)

        # if the joint has no children, set the orientation to match the parent joint.
        # Apply all rotations then zero them out.
        else:
            toOrientation(joint)
            cmds.setAttr('{}.jointOrient'.format(joint), 0, 0, 0)

        # if the joint is the last joint in the list and we want to autoUpVector the joints then set the orientation to 0
        if joint == joints[-1] and autoUpVector:
            toOrientation(joint)
            children = cmds.listRelatives(joint, c=True) or []
            for child in children:
                cmds.parent(child, world=True)
            cmds.setAttr('{}.jointOrient'.format(joint), 0, 0, 0)
            for child in children:
                cmds.parent(child, joint)


def getCrossUpVector(trs0, trs1, trs2):
    """
    Get a vector perpendicular to the plane drawn between three points

    :param str trs0: first transform
    :param str trs1: second transform
    :param str trs2: third transform
    :return: up vector
    :rtype: list tuple
    """
    A = om2.MPoint(cmds.xform(trs0, q=True, ws=True, t=True))
    B = om2.MPoint(cmds.xform(trs1, q=True, ws=True, t=True))
    C = om2.MPoint(cmds.xform(trs2, q=True, ws=True, t=True))

    # AB represent a distance between point A and B
    # pylint: disable = invalid-name
    AB = om2.MVector(A - B)

    # AC represent a distance between point A and C
    # pylint: disable = invalid-name
    AC = om2.MVector(A - C)

    crossProd = AB ^ AC

    crossProd.normalize()
    crossProd = mathUtils.scalarMult(crossProd, -1)
    return crossProd


def connectChains(source, destination, connectScale=True):
    """
    Connect two skeletons.

    This will connect all elements of the source list to the matching item in the destination list

    :param list source: list of source joints to connect to the matching item in the destination list
    :param list destination: list of destination joints to connect to the matching item in the source list
    :param bool connectScale: Connect the scale to the destination joints. This may not be disireable for some facial
                                components.
    """
    source = common.toList(source)
    destination = common.toList(destination)
    if not len(source) == len(destination):
        raise RuntimeError('List mismatch. Source and destination must have equal lengths')

    for driver, driven in zip(source, destination):
        attr.unlock(driven, attr.TRANSFORMS + ['v'])
        cmds.parentConstraint(driver, driven, mo=False)

        if connectScale:
            parent = 'bind' if cmds.objExists("bind") else None

            mult = cmds.createNode('multMatrix', name="{}_local_{}".format(driven, "mm"))
            worldMatrix = "{}.worldMatrix[0]".format(driver)
            cmds.connectAttr(worldMatrix, "{}.matrixIn[0]".format(mult))
            if parent:
                parentInverse = "{}.worldInverseMatrix[0]".format(parent)
                cmds.connectAttr(parentInverse, "{}.matrixIn[1]".format(mult))

            dcmp = cmds.createNode('decomposeMatrix', n=driver + '_mm_' + "dcmp")
            cmds.connectAttr(mult + '.matrixSum', dcmp + '.inputMatrix')

            cmds.connectAttr(dcmp + '.outputScale', driven + ".scale", f=True)
            cmds.connectAttr(dcmp + '.outputShear', driven + ".shear", f=True)

        attr.lock(driven, attr.TRANSFORMS + ['v'])


def hideJoints(joints):
    """
    Hide joints from the viewport by setting the draw style to None.
    This way you dont have to deal with the visability channel.

    :param list joints: list of joints to hide
    """

    joints = common.toList(joints)

    for joint in joints:
        if isJoint(joint):
            cmds.setAttr("{}.drawStyle".format(joint), 2)


def createInterpJoint(joint, parentJoint=None, value=0.5, t=False, r=True, s=False, sh=False, bind=True):
    """
    Add an interpolation rotation joint on the given joint. We will
    also add an attribute to the joint to blend between the joint and
    parent.

    0 will follow 100% the joint, 1 will follow the parent joint.

    If a parentJoint is provided it will be added as the parent.
    Otherwise it will get the parent of the joint.

    :param str joint: joint to add the interpolation joint on
    :param str parentJoint: parentjoint to blend the rotation between
    :param int float value: default interpolation value
    :param bool t: Apply translation transformations
    :param bool r: Apply rotation transformations
    :param bool s: Apply scale transformations
    :param bool sh: Apply shear transformations
    :param bool bind: Tag the created joint as a bind joint
    :return: name of the interpolation joint
    :rtype: str
    """

    if parentJoint is None:
        parentJoint = cmds.listRelatives(joint, parent=True, type='joint')
        parentJoint = parentJoint[0] if parentJoint else None

    if not parentJoint:
        raise Exception("Please provide a valid parent joint or set a hierarchy parent. ")

    interpJointName = naming.getUniqueName('{}_interp'.format(joint))

    interpJoint = cmds.createNode('joint', name=interpJointName)

    # set the radius to be slightly larger.
    # This is just to help us see alittle better
    cmds.setAttr("{}.radius".format(interpJoint), 1.25)

    # match the interp joint to the parent postion and set the joint as the parent
    transform.matchTransform(joint, interpJoint)
    toOrientation(interpJoint)
    cmds.parent(interpJoint, joint)

    # create an attribute to control the blending
    blendAttr = attr.createAttr(interpJoint, 'interpBlend', 'float', value=value, minValue=0, maxValue=1.0)

    # blend the rotation between the two joints
    multMatrix, pickMatrix = transform.connectOffsetParentMatrix(parentJoint, interpJoint, mo=True, t=t, r=r, s=s,
                                                                 sh=sh)
    blendMatrix = cmds.createNode("blendMatrix", n="{}_{}_blendMatrix".format(parentJoint, joint))
    cmds.connectAttr("{}.matrixSum".format(multMatrix), "{}.target[0].targetMatrix".format(blendMatrix))
    cmds.connectAttr(blendAttr, "{}.envelope".format(blendMatrix))

    # connect the blendMatrix to the pick matrix (and therefore the interp joint)
    cmds.connectAttr("{}.outputMatrix".format(blendMatrix), "{}.inputMatrix".format(pickMatrix), f=True)

    if bind:
        meta.tag(interpJoint, "bind")
    return interpJoint
