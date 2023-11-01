"""
Functions for working with SDKs
"""
import logging

import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

import rigamajig2.maya.attr as attr
import rigamajig2.maya.openMayaUtils as omu
import rigamajig2.shared.common as common

logger = logging.getLogger(__name__)

SDKNODETYPES = ['animCurveUU', 'animCurveUA', 'animCurveUL', 'animCurveUT']
DEFAULT_SDK_TYPE = 'animCurveUU'

TANGENT_TYPE_DICT = {"linear": oma.MFnAnimCurve.kTangentLinear,
                     "auto": oma.MFnAnimCurve.kTangentAuto,
                     "fast": oma.MFnAnimCurve.kTangentFast,
                     "slow": oma.MFnAnimCurve.kTangentSlow,
                     "step": oma.MFnAnimCurve.kTangentStep,
                     "clamp": oma.MFnAnimCurve.kTangentClamped}


def getSdkNode(driver, driven, type=None):
    """
    Get all SDK nodes between the driver and driven node.
    This is useful especially for things like rotations where the conncection may be fed through
    a UnitConversion node before going to the driven node.

    :param str driver: sdk driver node
    :param str driven: sdk driven node
    :param type: Optional - specifiy a type of animCurve to return.
    :return: list of sdk nodes between a driver and driven.
    """
    if type is None:
        type = SDKNODETYPES
    else:
        type = common.toList(type)

    driver = common.getFirstIndex(driver)
    driven = common.getFirstIndex(driven)
    sdkSet = set()
    for obj in [driver, driven]:
        if not cmds.objExists(obj):
            raise RuntimeError("{} does not exist".format(obj))
        connList = cmds.ls(cmds.listConnections(obj, scn=True), type=type)
        for each in connList:
            connList.extend(cmds.ls(cmds.listConnections(each, scn=True), type=type))
            sdkSet.update(set(connList))
    return list(sdkSet)


def getSdkDriver(sdk):
    """
    get the driver of an sdk node

    :param str sdk: name of an SDK node
    :return: driver of an SDK node
    :rtype: str
    """
    if not cmds.ls(sdk, type=SDKNODETYPES):
        logger.error('{} is not an SDK node'.format(sdk))
        return
    connList = cmds.listConnections(sdk, s=True, d=False, p=True, scn=True)
    if connList:
        return common.getFirstIndex(connList)
    else:
        return None


def getSdkDriven(sdk):
    """
    Get the nodes driven by a set driven key (anim curve) node

    :param sdk: Set driven key animation curve node. must be a valid rigamaig sdk curve type.
    :return: nodes driven by the sdk
    :rtype: str
    """
    if not cmds.ls(sdk, type=SDKNODETYPES):
        logger.error('{} is not an SDK node'.format(sdk))
        return
    connList = cmds.listConnections(sdk, s=False, d=True, p=True, scn=True)

    if cmds.nodeType(connList[0]) == 'blendWeighted':
        connList = cmds.listConnections(connList[0].split('.', 1)[0], s=False, d=True, p=True, scn=True)

    if connList:
        return connList[0]
    else:
        return None


# TODO:
def createSdk(driverPlug, drivenPlug, values, preInfinity=False, postInfinity=False, tangent='linear'):
    """
    Create an SDK connection

    :param str driverPlug: driver plug
    :param str drivenPlug: driven plug
    :param list tupple values: list of values as tuples. in the format of: [(driver, driven), ...]
    :param bool preInfinity: If true set the tanget to PreInfitity to linear
    :param bool postInfinity:If true set the tanget to postInfinity to linear
    :param str tangent: type of tangent for the curve.
                        Valid values are: "spline", "linear" "fast", "slow", "flat", "step", "clamped".
    :return: the name of the SDK node created
    :rtype: str
    """
    driverNode, driverAttr = driverPlug.split(".")
    drivenNode, drivenAttr = drivenPlug.split(".")

    animCurveName = '{}_{}_{}_{}_animCurve'.format(driverNode, driverAttr, drivenNode, drivenAttr)
    animCurveNode = cmds.createNode(DEFAULT_SDK_TYPE, n=animCurveName)

    mObject = omu.getMObject(animCurveNode)
    mfnAnimCurve = oma.MFnAnimCurve(mObject)

    # connect the driver into the animCurveNode
    cmds.connectAttr(driverPlug, "{}.input".format(animCurveNode))

    # set the pre infinity behavior
    if preInfinity:
        mfnAnimCurve.setPreInfinityType(oma.MFnAnimCurve.kCycleRelative)
    else:
        mfnAnimCurve.setPreInfinityType(TANGENT_TYPE_DICT[tangent])

    # set the post infitiy behavior
    if postInfinity:
        mfnAnimCurve.setPostInfinityType(oma.MFnAnimCurve.kCycleRelative)
    else:
        mfnAnimCurve.setPostInfinityType(TANGENT_TYPE_DICT[tangent])

    for i, point in enumerate(values):
        inn = point[0]
        out = point[-1]
        mfnAnimCurve.addKey(inn, out)
        # set the in and out tangets based on the input
        mfnAnimCurve.setInTangentType(i, TANGENT_TYPE_DICT[tangent])
        mfnAnimCurve.setOutTangentType(i, TANGENT_TYPE_DICT[tangent])

    connected = cmds.listConnections(drivenPlug, source=True, destination=False, skipConversionNodes=True)
    if connected:
        nodeType = cmds.nodeType(connected[0])

        # if the input is a set driven key then created a blendweighted node to add the values together
        if nodeType in SDKNODETYPES:
            blendWeightedNode = createBlendWeightedNode(drivenPlug)
            nextInput = attr.getNextAvailableElement("{}.input".format(blendWeightedNode))
            cmds.connectAttr("{}.output".format(animCurveNode), nextInput)

        # if a blend weighted node is connected then connect the animCurve into the next available input
        elif nodeType == 'blendWeighted':
            blendWeightedNode = connected[0]
            nextInput = attr.getNextAvailableElement("{}.input".format(blendWeightedNode))
            cmds.connectAttr("{}.output".format(animCurveNode), nextInput)

        # if the connected plug is not a animCurve or a blendWeighted node then throw an error.
        else:
            raise Exception("{} is already connected to {}".format(drivenPlug, connected[0]))

    # if nothing is connected we can connect directly to the driver plug
    else:
        cmds.connectAttr("{}.output".format(animCurveNode), drivenPlug, f=True)

    # return the anim curve created
    return animCurveNode


def createBlendWeightedNode(drivenPlug):
    """
    create a blend weighted node on the driven plug

    :param drivenPlug: plug to add the blend weighted node to
    :return: blend weighted node created
    :rtype: str
    """
    drivenNode, drivenAttr = drivenPlug.split(".")
    # get the connected node. dont skip the conversion nodes in the case of connection to a rotation.
    # also get a unit conversion node. later we will check if the first node is a unit conversion and if it is delete it.
    connected = cmds.listConnections(drivenPlug, source=True, destination=False, plugs=True, skipConversionNodes=True)
    unitConvert = cmds.listConnections(drivenPlug, source=True, destination=False, plugs=True, skipConversionNodes=False)

    blendWeightedNode = cmds.createNode("blendWeighted", n="{}_{}_blendWeighted".format(drivenNode, drivenAttr))

    # if the drivenPlug has an incoming connection connect it to the blendWeightedNode
    if connected:
        nextPlug = attr.getNextAvailableElement("{}.input".format(blendWeightedNode))
        # a node can only have one given input so we can get the first index of the connected list
        cmds.connectAttr(connected[0], nextPlug, f=True)

    if cmds.nodeType(unitConvert[0]) == 'unitConversion':
        cmds.delete(unitConvert)

    # connect the blendWeighted to the drivenPlug
    cmds.connectAttr("{}.output".format(blendWeightedNode), drivenPlug, f=True)

    return blendWeightedNode
