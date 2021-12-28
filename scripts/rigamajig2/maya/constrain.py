"""
Constraint functions
"""

import rigamajig2.shared.common as common
import rigamajig2.maya.node as node
import rigamajig2.maya.hierarchy as hierarchy
import rigamajig2.maya.meta as meta
import maya.cmds as cmds


def parentConstraint(driver, driven):
    """
    Create a matrix based 'parent constraint'
    :param driver: node to drive the parent constraint
    :param driven: node driven by the parent constraint
    :return: mult matrix and decompose matrix used in the constraint
    """
    mm, dcmp = __createSimpleMatrixConstraintNetwork(driver=driver, driven=driven)

    # connect the translate and rotate
    cmds.connectAttr("{}.{}".format(dcmp, 'outputTranslate'), "{}.{}".format(driven, 'translate'), f=True)
    cmds.connectAttr("{}.{}".format(dcmp, 'outputRotate'), "{}.{}".format(driven, 'rotate'), f=True)

    return mm, dcmp


def jointConstraint(driver, driven):
    pass


def pointConstraint(driver, driven):
    """
    Create a matrix based 'point constraint'
    :param driver: node to drive the point constraint
    :param driven: node driven by the point constraint
    :return: mult matrix and decompose matrix used in the constraint
    """
    mm, dcmp = __createSimpleMatrixConstraintNetwork(driver=driver, driven=driven)

    # connect the translate and rotate
    cmds.connectAttr("{}.{}".format(dcmp, 'outputTranslate'), "{}.{}".format(driven, 'translate'), f=True)

    return mm, dcmp


def orientConstraint(driver, driven):
    """
    Create a matrix based 'orient constraint'
    :param driver: node to drive the orient constraint
    :param driven: node driven by the orient constraint
    :return: mult matrix and decompose matrix used in the constraint
    :return:
    """
    mm, dcmp = __createSimpleMatrixConstraintNetwork(driver=driver, driven=driven)

    # connect the translate and rotate
    cmds.connectAttr("{}.{}".format(dcmp, 'outputRotate'), "{}.{}".format(driven, 'rotate'), f=True)

    return mm, dcmp


def scaleConstraint(driver, driven):
    """
    Create a matrix based 'scale constraint'
    :param driver: node to drive the scale constraint
    :param driven: node driven by the scale constraint
    :return: mult matrix and decompose matrix used in the constraint
    """
    mm, dcmp = __createSimpleMatrixConstraintNetwork(driver=driver, driven=driven)
    # connect the translate and rotate
    cmds.connectAttr("{}.{}".format(dcmp, 'outputScale'), "{}.{}".format(driven, 'scale'), f=True)

    return mm, dcmp


def __createSimpleMatrixConstraintNetwork(driver, driven):
    """
    This private function is used to check if a matrix constraint network exists and if not create it
    :param driver:
    :param driven:
    :return:
    """
    driven = common.getFirstIndex(driven)
    if cmds.objExists("{}.{}".format(driven, '{}_constraintMm'.format(driver))):
        mm = meta.getMessageConnection('{}.{}'.format(driven, '{}_constraintMm'.format(driver)))
        dcmp = meta.getMessageConnection('{}.{}'.format(driven, '{}_constraintDcmp'.format(driver)))
    else:
        mm = cmds.createNode('multMatrix', name=driven + '_mm')
        dcmp = cmds.createNode('decomposeMatrix', name=driven + '_dcmp')

        # convert the driver's world matrix into the parent space of the driven
        cmds.connectAttr("{}.{}".format(driver, 'worldMatrix'), "{}.{}".format(mm, 'matrixIn[0]'))
        cmds.connectAttr("{}.{}".format(driven, 'parentInverseMatrix'), "{}.{}".format(mm, 'matrixIn[1]'))

        # connect the new matrix to the decompose matrix
        cmds.connectAttr("{}.{}".format(mm, 'matrixSum'), "{}.{}".format(dcmp, 'inputMatrix'))

        # create message connections to the mult matrix and decompose matrix.
        # this is used if we ever create another constraint to re-use the old nodes
        meta.addMessageConnection(driven, mm, '{}_constraintMm'.format(driver))
        meta.addMessageConnection(driven, dcmp, '{}_constraintDcmp'.format(driver))

    return mm, dcmp


def negate(driver, driven, t=False, r=False, s=False):
    """
    :param driver:
    :param driven:
    :param t: negate the translate
    :param r: negate the rotation
    :param s: negate the scale
    :return:
    """
    driver = common.getFirstIndex(driver)
    drivens = common.toList(driven)

    for driven in drivens:
        if driven not in cmds.listRelatives(driver, ad=True):
            # create a connection to the driver node
            # neg_trs = cmds.createNode('transform', n=driven + '_trs')
            neg_trs = hierarchy.create(driven, [driven + '_trs'], above=True, matchTransform=True)[0]
            parentConstraint(driver=driver, driven=neg_trs)

        if t:
            node.unitConversion('{}.{}'.format(driver, 't'), '{}.{}'.format(driven, 't'), -1, name=driven + '_t_neg')

        if r:
            node.unitConversion('{}.{}'.format(driver, 'r'), '{}.{}'.format(driven, 'r'), -1, name=driven + '_r_neg')
            # get the opposite rotate order. this is hard coded.
            ro = [5, 3, 4, 1, 2, 0][cmds.getAttr('%s.rotateOrder' % driver)]
            cmds.setAttr("{}.{}".format(driven, 'rotateOrder'), ro)

        if s:
            node.multiplyDivide([1,1,1], '{}.{}'.format(driver, 's'), operation='div', output='{}.{}'.format(driven, 's'), name=driven + '_s_neg')
