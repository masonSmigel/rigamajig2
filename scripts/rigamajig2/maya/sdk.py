"""
Functions for working with SDKs
"""
import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.attr as attr

SDKNODETYPES = ['animCurveUU', 'animCurveUA', 'animCurveUL', 'animCurveUT']


def getSdkNode(driver, driven, type=None):
    """
    Get all SDK nodes between the driver and
    :param driver: sdk driver node
    :param driven: sdk driven node
    :param type: Optional - specifiy a type of animCurve to return.
    :return:
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
    :param sdk:
    :return:
    """
    if not cmds.ls(sdk, type=SDKNODETYPES):
        cmds.error('{} is not an SDK node'.format(sdk))
        return
    connList = cmds.listConnections(sdk, s=True, d=False, p=True, scn=True)
    if connList:
        return common.getFirstIndex(connList)
    else:
        return None


def getSdkDriven(sdk):
    if not cmds.ls(sdk, type=SDKNODETYPES):
        cmds.error('{} is not an SDK node'.format(sdk))
        return
    connList = cmds.listConnections(sdk, s=False, d=True, p=True, scn=True)

    if cmds.nodeType(connList[0]) == 'blendWeighted':
        connList = cmds.listConnections(connList[0].split('.', 1)[0], s=False, d=True, p=True, scn=True)

    if connList:
        return connList[0]
    else:
        return None


# TODO:
def createSdk(driver, driven, values, preInfinity=False, postInfinity=False, tangent='linear'):
    """
    Create an SDK connection
    :param driver: driver plug
    :type driver: str
    :param driven: driven plug
    :type driven: str
    :param values: list of values as tuples. in the format of: (driver, driven)
    :type values: list | tuple
    :param preInfinity: If true set the tanget to PreInfitity to linear
    :type preInfinity: bool
    :param postInfinity:If true set the tanget to postInfinity to linear
    :type postInfinity: bool
    :param tangent: type of tangent for the curve. Valid values are: "spline", "linear" "fast", "slow", "flat", "step", "clamped". Default is "linear"
    :type tangent: str
    :return: the name of the SDK node created
    :rtype: str
    """

    preTanget = 'spline' if preInfinity else tangent
    postTanget = 'spline' if postInfinity else tangent

    for i, point in enumerate(values):
        itt = preTanget if i == 0 else tangent
        ott = postTanget if i == (len(values) - 1) else tangent
        cmds.setDrivenKeyframe(driven, cd=driver, dv=float(point[0]), v=float(point[1]), itt=itt, ott=ott, ib=True)

    # Get the sdk node
    sdkNode = common.getFirstIndex(getSdkNode(driver, driven))
    predictedName = "{}_{}_sdk".format(driver.replace('.', '_'), driven.replace('.', '_'))
    if not cmds.objExists(predictedName):
        sdkNode = cmds.rename(sdkNode, predictedName)

    # set the pre and post infinity nodes
    cmds.setAttr("{}.preInfinity".format(sdkNode), preInfinity)
    cmds.setAttr("{}.postInfinity".format(sdkNode), postInfinity)

    # cut the key to save a bit of memory
    cmds.cutKey(sdkNode, f=(1000001, 1000001), clear=True)

    # look for a blendWeighted, and try to rename it
    for node in cmds.listConnections(sdkNode, d=True, scn=True):
        if cmds.nodeType(node) == 'blendWeighted':
            cmds.rename(node, "{}_{}_blendweighted".format(driver.split('.')[0], driven.replace('.', '_')))

    return sdkNode


# TODO:
def setSdk(sdk, keyList):
    pass
