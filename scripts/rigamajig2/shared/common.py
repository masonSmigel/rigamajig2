"""
This module contains functions common to all modules and constants
"""
from collections import OrderedDict
import re

DEBUG = False

# Side constants
LEFT = 'l'
RIGHT = 'r'
CENTER = 'c'

SIDES = {'left': LEFT, 'right': RIGHT, 'center': CENTER}

# Location constants
FRONT = 'fr'
BACK = 'bk'
MIDDLE = 'md'
TOP = 'tp'
BOTTOM = 'bt'

LOCATIONS = {'front': FRONT, 'back': BACK, 'middle': MIDDLE, 'top': TOP, 'bottom': BOTTOM}

# Class Constants
IK = 'ik'
FK = 'fk'
SKINCLUSTER = 'sc'
PSD = 'psd'
CLUSTER = 'cls'
BLEND = 'blend'
LATTICE = 'lat'
SURFACE = 'srf'
CURVE = 'crv'
NURBS = 'nurbs'
ROOT = 'root'
GUIDES = 'guide'
POLYGON = 'mesh'
LOCATOR = 'loc'
DRIVER = 'drv'
PARENTCONSTRAINT = "parentConstraint"
POINTCONSTRAINT = "pointConstraint"
ORIENTCONSTRAINT = "orientConstraint"
POINTONCURVEINFO = "pointOnCurveInfo"
AIMCONSTRAINT = "aimConstraint"
PAIRBLEND = "pairBlend"
BLENDCOLOR = 'blend'
BLENDTWOATTR = 'bta'
REVERSE = "rev"
FOLLICLE = "fol"
CONDITION = 'cond'
CHOICE = 'choice'
MULTIPLYDIVIDE = "multDiv"
ADDDOUBLELINEAR = "adl"
MULTDOUBLELINEAR = "mdl"
PLUSMINUSAVERAGE = "pma"
CURVEINFO = "curveInfo"
DISTANCEBETWEEN = "dist"
VECTORPRODUCT = "vpn"
DECOMPOSEMATRIX = 'dcmp'
COMPOSEMATRIX = 'cmp'
MULTMATRIX = 'mm'
CLAMP = 'clamp'
REMAP = 'rmv'
QUATTOEULER = 'quatToEuler'
EULERTOQUAT = 'eulerToQuat'

# Type Constants
COMPONENT = 'cmpnt'
OFFSET = 'trsOffset'
TRANSFORM = 'trs'
TARGET = 'tgt'
BUFFER = 'buffer'
HIARCHY = 'hrc'
SDK = 'sdk'
NEGATE = 'neg'
UTILITY = "util"
CONTROL = 'ctl'
JOINT = 'jnt'
GEOMETRY = 'geo'
DEFORMER = 'def'
SHAPE = 'shape'

# Pipeline Constants
MODEL = 'mod'
RIG = 'rig'
ANIMATION = 'anim'
SIMULATION = 'sim'

# Naming Template
DELIMINATOR = '_'
NAMETEMPLATE = '{BASE}' + DELIMINATOR + '{SIDE}' + DELIMINATOR + '{LOCATION}{WARBLE}{INDEX}' + DELIMINATOR + '{EXTENSION}'
PADDING = 2
MAXITTERATIONS = 2000
NAMETEMPLATETOKENS = ["BASE",
                      "SIDE",
                      "LOCATION",
                      "WARBLE",
                      "INDEX",
                      "EXTENSION",
                      ]

L_TOKENS = ['left_', '_left', 'Left_', '_Left', 'lf_', '_lf', 'Lt_', '_Lt', 'lft_', '_lft', 'Lft_', '_Lft', 'Lf_',
            '_Lf', '_l', 'L_', '_L', '_L_', '_l_']
R_TOKENS = ['right_', '_right', 'Right_', '_Right', 'rt_', '_rt', 'Rt_', '_Rt', 'rgt_', '_rgt', 'Rgt_', '_Rgt', 'Rg_',
            '_Rg', '_r', 'R_', '_R', '_R_', '_r_']


def toList(values):
    """
    Converts values into a list
    :param values: values to convert into a list
    :return: list of values
    """
    if not isinstance(values, (list, tuple)):
        values = [values]
    return values


def getFirstIndex(var):
    """
    Return the first index of a list
    :param var: list to get index from
    :type var: list | tuple
    :return: first index of a list or tuple
    """
    if isinstance(var, (list, tuple)):
        if not len(var):
            return var
        return var[0]
    else:
        return var


def convertDictKeys(dictionary):
    """
    Converts Dictionary keys from unicodes to strings

    :param dictionary: the ditionary you want to convert the keys on
    :type dictionary: dict

    :return: The dictionary with its keys converted
    :rtype: dict
    """

    # If its not a dictionary return it.
    if not isinstance(dictionary, dict):
        return dictionary

    # If its a dictionary look through the keys/values and convert them
    return OrderedDict((str(k), convertDictKeys(v)) for k, v in dictionary.items())


def convertUnicodeList(unicodeList):
    """
    Convert unicodes in a list into string values
    :param unicodeList: the ditionary you want to convert the values on
    :return:
    """
    if not isinstance(unicodeList, (list, tuple)):
        return unicodeList

    return [str(v) if isinstance(v, unicode) else v for v in unicodeList]


def flattenList(selList):
    flat_list = []
    for each in selList:
        if not ":" in each:
            flat_list.append(each)
            continue

        begin, end = re.findall(r'\[(.*?)\]', each)[0].split(":")
        base_part = each.split("[")[0]

        for number in range(int(begin), int(end) + 1):
            flat_list.append("{}[{}]".format(base_part, number))

    return flat_list


def getMirrorName(name, left=None, right=None):
    """
    Get the appropriate name for a control on the opposide side of the rig.
    If a left and right side token are provided it will look for those first.
    otherwise it will look through a list of possible tokens.
    :param name: name of the node to get the mirror of
    :type name:
    :param left: string to denote nodes on the left side of the rig
    :type left: str
    :param right: string to denote nodes on the right side of the rig
    :type right: str
    :return: name of the node on the opposite side of. If none exists return None
    :rtype: str
    """
    if left and right:
        if left in name:
            return name.replace(left, right)
        elif right in name:
            return name.replace(right, left)

    else:
        for i in range(len(L_TOKENS)):
            if L_TOKENS[i] in name:
                return name.replace(L_TOKENS[i], R_TOKENS[i])
            elif R_TOKENS[i] in name:
                return name.replace(R_TOKENS[i], L_TOKENS[i])


def getSide(name):
    """
    Get the side of the node
    :param name: name to check the side of
    :type name: str
    :return: the side of the node. A single letter to denote the side (this can be set in the rigamjig2.shared.common module)
             Default values are left - 'l' and  right -'r'
     :rtype: str
    """
    for i in range(len(L_TOKENS)):
        if L_TOKENS[i] in name:
            return LEFT
        elif R_TOKENS[i] in name:
            return RIGHT
    return None
