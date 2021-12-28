"""
Constraint functions
"""

import rigamajig2.shared.common as common
import rigamajig2.maya.node as node
import maya.cmds as cmds


def parentConstraint(source, target):
    pass


def jointConstraint(source, target):
    pass


def orientConstraint(source, target):
    pass


def negate(driver, driven, translate=False, rotate=False, scale=False):
    """
    :param driver:
    :param driven:
    :param translate:
    :param rotate:
    :param scale:
    :return:
    """
    driver = common.getFirstIndex(driver)
    driven = common.getFirstIndex(driven)

    if driven not in cmds.listRelatives(driver, ad=True):
        raise RuntimeError("driven is not a child of the driver")

    if translate:
        node.multiplyDivide('{}.{}'.format(driver, 't'), [-1,-1,-1], output='{}.{}'.format(driven, 't'), name=driven + '_t_neg')

    if rotate:
        node.unitConversion('{}.{}'.format(driver, 'r'), '{}.{}'.format(driven, 'r'), -1, name=driven + '_r_neg')
        # get the opposite rotate order. this is hard coded.
        ro = [5, 3, 4, 1, 2, 0][cmds.getAttr('%s.rotateOrder' % driver)]
        cmds.setAttr("{}.{}".format(driven, 'rotateOrder'), ro)

    if scale:
        node.multiplyDivide([1,1,1], '{}.{}'.format(driver, 's'), operation='div', output='{}.{}'.format(driven, 's'), name=driven + '_s_neg')
