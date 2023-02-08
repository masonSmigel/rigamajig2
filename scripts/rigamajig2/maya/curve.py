""" Curve functions """
from collections import OrderedDict

import maya.cmds as cmds
import maya.api.OpenMaya as om2

import rigamajig2.maya.decorators
import rigamajig2.shared.common as common
import rigamajig2.maya.shape as shape
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.openMayaUtils as openMayaUtils


def createCurve(points, degree=3, name='curve', transformType="transform", form="Open", parent=None):
    """
    Create a curve

    :param list  points: points used to create the curve
    :param int degree: degree of the curve
    :param str name: name of the curve
    :param str transformType: transfrom type to create on.
    :param str form: The form of the curve. ex. (Open, Closed, Periodic)
    :param str parent: Optional- Parent the curve under this node in the hierarchy
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
            trsTypeName = cmds.createNode("joint", name="{}_jnt".format(name))
            cmds.parent(shape, trsTypeName, r=True, shape=True)
            cmds.delete(curve)
            cmds.rename(trsTypeName, curve)
            cmds.setAttr("{}.drawStyle".format(curve), 2)
        cmds.rename(shape, "{}Shape".format(curve))

    if parent:
        cmds.parent(curve, parent)

    return curve


def createCurveFromTransform(transforms, degree=3, name='curve', transformType='transform', form="Open", parent=None, ep=False):
    """
    Wrapper to create a curve from given transforms

    :param list transforms: list of transforms to use to create the curve from.
    :param int degree: degree of the curve
    :param str name: name of the curve
    :param str transformType: transfrom type to create on.
    :param str form: The form of the curve. ex. (Open, Closed, Periodic). If closed an additional point will be added.
    :param str parent: Optional- Parent the curve under this node in the hierarchy
    :param bool ep: use transforms as Edit points instead of Curve points
    :return: name of the curve created
    :rtype: str
    """
    points = [cmds.xform(transform, q=True, ws=True, t=True) for transform in transforms]

    if form == "Closed":
        pass
        # points.append(cmds.xform(transforms[0], q=True, ws=True, t=True))

    if ep:
        return createCurveFromEP(points, degree=degree, name=name, transformType=transformType, form=form, parent=parent)

    return createCurve(points, degree=degree, name=name, transformType=transformType, form=form, parent=parent)


def createCurveFromEP(epList, degree=3, name='curve', transformType='transform', form='Open', parent=None):
    """
    Create an EP curve from a list of

    :param epList: List of edit points
   :param int degree: degree of the curve
    :param str name: name of the curve
    :param str transformType: transfrom type to create on.
    :param str form: The form of the curve. ex. (Open, Closed, Periodic). If closed an additional point will be added.
    :param str parent: Optional- Parent the curve under this node in the hierarchy
    :return:
    """

    # create a linear curve from the EP list
    curve = createCurve(epList, degree=1, name=name, transformType=transformType, form=form, parent=parent)


    # create a new fit spline
    fitCurve = cmds.fitBspline(curve,ch=0,tol=0.01)

    # Delete original curve
    cmds.delete(curve)
    # Rename fit curve
    curve = cmds.rename(fitCurve[0], curve)
    cmds.parent(curve, parent)
    # Return curve
    return curve



def getCvs(curve):
    """
    get a list of all Cvs in a curve

    :param str curve: curve to get CVs of
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

    :param str curve: curve to get cvs from
    :param bool world: Get the Cv position in world space. False is local position
    :return: list of Cv positions
    :rtype:  list
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

    :param str curve: curve to get the length of
    :return: length of the given curve
    :rtype: float
    """
    return cmds.arclen(curve, ch=False)


def getClosestParameter(curve, position, world=True):
    """
    Get the closest parameter on a curve

    :param str curve: curve to get the closest parameter on
    :param list tuple str position: postion to get the closest parameter from.
        If a transform is passed  get the postion from the tranform
    :param bool world: get the point and parameter in world space otherwise do it in local space
    :return: closest parameter on the curve
    """
    if not isinstance(position, (list, tuple)):
        position = cmds.xform(position, q=True, ws=True, t=True)

    dagPath = openMayaUtils.getDagPath(curve)
    dagPath.extendToShape()
    mFnNurbsCurve = om2.MFnNurbsCurve(dagPath)

    # get the proper space
    space = om2.MSpace.kWorld if world else om2.MSpace.kObject

    # get the closest point on the curve from the point
    mPoint = om2.MPoint(position[0], position[1], position[2])
    mPointOnCurve = mFnNurbsCurve.closestPoint(mPoint, space=space)[0]

    parameter = mFnNurbsCurve.getParamAtPoint(mPointOnCurve, tolerance=0.01, space=space)
    return parameter


def getRange(curve):
    """
    Get the range of a given curve

    :param curve: name of the curve to get the range of
    :return: min, max
    :rtype list
    """
    curveShape = cmds.listRelatives(curve, s=True) or []

    minParam, maxParam = cmds.getAttr("{}.minMaxValue".format(curveShape[0]))[0]
    return minParam, maxParam


def attatchToCurve(transform, curve, toClosestParam=True,  parameter=0.0):
    """
    Connect a transform to a given parameter of a curve

    :param transform: name of transform to attatch to a curve
    :param curve: name of the curve to attatch the transform to
    :param toClosestParam: If true attatch to the closest parameter on the curve
    :param parameter: if not toClosestParam then use this parameter
    :return: the new point on curve info node
    :rtype: str
    """

    if not cmds.objExists(transform):
        raise Exception("The transform {} does not exist".format(transform))

    if toClosestParam:
        trsPosition = cmds.xform(transform, q=True, ws=True, t=True)
        parameter  = getClosestParameter(curve, position=trsPosition)

    # create the point on curve info node and connect stuff
    curveShape = cmds.listRelatives(curve, s=True)[0]

    pointOnCurveInfo = cmds.createNode("pointOnCurveInfo", name="{}_pointOnCurveInfo".format(transform))
    cmds.connectAttr("{}.{}".format(curveShape, "worldSpace[0]"), "{}.{}".format(pointOnCurveInfo, "inputCurve"))
    cmds.connectAttr("{}.{}".format(pointOnCurveInfo, "result.position"), "{}.{}".format(transform, "translate"))
    cmds.setAttr("{}.parameter".format(pointOnCurveInfo), parameter)

    return pointOnCurveInfo


def setCvPositions(curve, cvList, world=True):
    """
    Using a list of positions set the positions of each Cv in a curve

    :param str curve: curve to get cvs from
    :param list cvList: list of positions to set
    :param bool world: apply the positions in world or local space.
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

    :param str source: curve to copy from
    :param str destinations: destination of the copied shape
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
    Mirror the curve shape from one node to an existionf transform with a matching name.

    :param str list curves: curve to mirror
    :param str axis: axis to mirror across
    :param str mode: Sets the mode options for mirroring. 'match' will match the positions of existing cvs.
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
