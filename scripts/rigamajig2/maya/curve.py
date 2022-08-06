""" Curve functions """
from collections import OrderedDict

import maya.cmds as cmds

import rigamajig2.maya.decorators
import rigamajig2.shared.common as common
import rigamajig2.maya.shape as shape
import rigamajig2.maya.mathUtils as mathUtils


def createCurve(points, degree=3, name='curve', transformType="transform", form="Open"):
    """
    Create a curve
    :param points: points used to create the curve
    :type points: list

    :param degree: degree of the curve
    :type degree: int

    :param name: name of the curve
    :type name: str

    :param transformType: transfrom type to create on.
    :type transformType: str

    :param form: The form of the curve. ex. (Open, Closed)
    :type form: str

    :return: name of the curve created
    :rtype: str
    """

    knotList = [0]
    if degree == 1:
        knotList.extend(range(len(points))[1:])
    elif degree == 2:
        knotList.extend(range(len(points) - 1))
        knotList.append(knotList[-1])
    elif degree == 3:
        knotList.append(0)
        knotList.extend(range(len(points) - 2))
        knotList.extend([knotList[-1], knotList[-1]])

    # if the form is closed, we will use a circle to create the control
    if form not in ['Closed', 'Periodic']:
        curve = cmds.curve(name=name, p=points, k=knotList, degree=degree)
    else:
        curve = cmds.circle(name=name, c=(0, 0, 0), nr=(0, 1, 0), sw=360, r=1,
                            d=degree, ut=0, tol=0.01, s=len(points), ch=False)[0]
        for i, position in enumerate(points):
            cmds.setAttr("{}.controlPoints[{}]".format(curve, i), *position)

    # rename all of the shapes that are children of the curve. In this instance, there should
    # only be one.
    for shape in cmds.listRelatives(curve, c=True, type="shape"):
        if transformType == "joint":
            trsTypeName = cmds.createNode("joint", name="{}_jtn".format(name))
            cmds.parent(shape, trsTypeName, r=True, shape=True)
            cmds.delete(curve)
            cmds.rename(trsTypeName, curve)
            cmds.setAttr("{}.drawStyle".format(curve), 2)
        cmds.rename(shape, "{}Shape".format(curve))

    return curve


def createCurveFromTransform(transforms, degree=3, name='curve', transformType='transform'):
    """
    Wrapper to create a curve from given transforms
    :param transforms:

    :param degree: degree of the curve
    :type degree: int

    :param name: name of the curve
    :type name: str

    :param transformType: transfrom type to create on.
    :type transformType: str

    :return: name of the curve created
    :rtype: str
    """
    points = [cmds.xform(transform, q=True, ws=True, t=True) for transform in transforms]
    return createCurve(points, degree, name, transformType)


def getCvs(curve):
    """
    get a list of all Cvs in a curve
    :param curve: curve to get CVs of
    :type curve: str

    :return: list of Cvs. ie ('curve.cv[0]', 'curve.cv[1]'...)
    :rtype: list
    """
    if isinstance(curve, (list, tuple)):
        curve = curve[0]

    cvs = cmds.ls("{}.cv[*]".format(curve))
    return common.flattenList(cvs)


def getCvPositions(curve, world=True):
    """
    Get the positions of all cvs in a curve
    :param curve: curve to get cvs from
    :param world: Get the Cv position in world space. False is local position
    :return: list of Cv positions
    :rtype: list
    """

    if isinstance(curve, (list, tuple)):
        curve = curve[0]

    if shape.getType(curve) != 'nurbsCurve':
        cmds.error("Node must be of type 'nurbsCurve'. {} is of type {}".format(curve, shape.getType(curve)))

    cvPos = list()
    for cv in getCvs(curve):
        if world:
            cvPos.append(cmds.xform(cv, q=True, ws=True, t=True))
        else:
            cvPos.append(cmds.xform(cv, q=True, ws=False, t=True))
    return cvPos


def getArcLen(curve):
    """
    Get the arc length of a curve. This is a simple wrapper
    :param curve: curve to get the length of
    :return: length of the given curve
    """
    return cmds.arclen(curve, ch=False)


def setCvPositions(curve, cvList, world=True):
    """
    Using a list of positions set the positions of each Cv in a curve
    :param curve: curve to get cvs from
    :param cvList: list of positions to set
    :param world: apply the positions in world or local space.
    :return: list of Cv positions
    :rtype: list
    """
    if isinstance(curve, (list, tuple)):
        curve = curve[0]

    if shape.getType(curve) != 'nurbsCurve':
        cmds.error("Node must be of type 'nurbsCurve'. {} is of type {}".format(curve, shape.getType(curve)))

    for i, cv in enumerate(getCvs(curve)):
        if world:
            cmds.xform(cv, ws=True, t=cvList[i])
        else:
            cmds.xform(cv, ws=False, t=cvList[i])


def wipeCurveShape(curve):
    """
    Wipe control curves
    :param curve: wipe all control curves
    """
    if cmds.listRelatives(curve, shapes=True, pa=True):
        for shape in cmds.listRelatives(curve, shapes=True, pa=True):
            cmds.delete(shape)


@rigamajig2.maya.decorators.oneUndo
@rigamajig2.maya.decorators.preserveSelection
def copyShape(source, destinations):
    """
    copy the shapes on the shapes nodes of the source to the desination nodes
    :param source: curve to copy from
    :type source: str
    :param destinations: destination of the copied shape
    :type source: str
    :return:
    """
    if isinstance(source, (list, tuple)):
        source = source[0]

    if not isinstance(destinations, (list, tuple)):
        destinations = [destinations]

    # Collect data about the curve
    data = OrderedDict()
    data['shapes'] = OrderedDict()
    shapeList = cmds.listRelatives(source, c=True, shapes=True, type="nurbsCurve", pa=True)
    if shapeList:
        for shape in shapeList:
            data['shapes'][shape] = OrderedDict()
            data['shapes'][shape]['points'] = list()
            for i, cv in enumerate(cmds.ls("{0}.cv[*]".format(shape), fl=True)):
                data['shapes'][shape]['points'].append(cmds.getAttr("{}.controlPoints[{}]".format(shape, i))[0])

            formNames = cmds.attributeQuery("f", node=shape, le=True)[0].split(":")
            data['shapes'][shape]['form'] = formNames[cmds.getAttr("{}.form".format(shape))]
            data['shapes'][shape]['degree'] = cmds.getAttr("{}.degree".format(shape))

    # Create a new curve from the data
    for destination in destinations:
        for shape in data['shapes'].keys():
            form = 'Open'
            if 'form' in data['shapes'][shape]:
                form = data['shapes'][shape]['form']
            curveTrs = createCurve(points=data['shapes'][shape]['points'],
                                   degree=data['shapes'][shape]['degree'],
                                   name='{}_temp'.format(destination),
                                   transformType='transform',
                                   form=form)

            shapeNode = cmds.listRelatives(curveTrs, c=True, s=True, type='nurbsCurve')[0]
            newShape = cmds.rename(shapeNode, "{}Shape".format(destination))
            cmds.parent(newShape, destination, r=True, s=True)
            cmds.delete(curveTrs)


@rigamajig2.maya.decorators.oneUndo
@rigamajig2.maya.decorators.preserveSelection
def mirror(curves, axis='x', mode='replace'):
    """
    :param curves: curve to mirror
    :type curves: str | list

    :param axis: axis to mirror across
    :type axis: str

    :param mode: Sets the mode options for mirroring. 'match' will match the positions of existing cvs.
                'replace' will replace the existing curve with a new one, or create one if it does not exist. 
    """

    if not isinstance(curves, list):
        curves = [curves]

    if axis.lower() not in ('x', 'y', 'z'):
        raise ValueError("Keyword Argument: 'axis' not of accepted value ('x', 'y', 'z').")

    posVector = ()
    if axis.lower() == 'x':
        posVector = (-1, 1, 1)
    elif axis.lower() == 'y':
        posVector = (1, -1, 1)
    elif axis.lower() == 'z':
        posVector = (1, 1, -1)

    for i, curve in enumerate(curves):
        if cmds.nodeType(curve) == "transform" or cmds.nodeType(curve) == "joint":
            shapeList = cmds.listRelatives(curve, c=True, shapes=True, type="nurbsCurve", ni=1)
        else:
            shapeList = [curveNode]
        destinationCurve = common.getMirrorName(curve)
        if mode == 'replace':

            # store any incomming visibility connections to the FIRST curve.
            tempDestinationShape = cmds.listRelatives(destinationCurve, s=True) or []
            connections = None
            if tempDestinationShape:
                connections = cmds.listConnections("{}.v".format(tempDestinationShape[0]), d=False, s=True, p=True)

            wipeCurveShape(destinationCurve)
            copyShape(curve, destinationCurve)

            # if the curve had incoming connections re-create them. 
            if connections:
                for connection in connections:
                    for shape in cmds.listRelatives(destinationCurve, c=True, shapes=True, type="nurbsCurve", ni=1):
                        cmds.connectAttr(connection, "{}.v".format(shape), f=True)

        for shape in shapeList:
            destinationShape = common.getMirrorName(shape)
            # if the source and destination have different CV counts. we need to make a new curve on the destination.

            cvList = getCvs(shape)
            for cv in cvList:
                destinationCv = cv.replace(curve, destinationCurve)

                if not cmds.objExists(cv):
                    cmds.warning('Cannot find source: {}'.format(cv))
                    return

                if not cmds.objExists(destinationCv):
                    cmds.warning('Cannot find destination: {}'.format(destinationCv))
                    return

                if cv == destinationCv:
                    cmds.warning('Cannot find mirror for: {}'.format(cv))
                    return

                pos = cmds.xform(cv, q=True, ws=True, t=True)
                cmds.xform(destinationCv, ws=True,
                           t=(pos[0] * posVector[0], pos[1] * posVector[1], pos[2] * posVector[2]))
