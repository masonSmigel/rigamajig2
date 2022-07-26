""" Naming Functions """

import re
import maya.cmds as cmds
from collections import OrderedDict
import rigamajig2.shared.common as common

DELIMINATOR = '_'


def normalize(string):
    """
    Normalize a string
    :param string:
    :type string: str
    :return: a normalized string
    """

    if re.match("^[0-9]", str(string)):
        string = "_" + str(string)
    return re.sub("[^A-Za-z0-9_{}]", "", str(string))


def getLongName(obj):
    """
    Returns the full name of a given object
    
    :param obj: object path
    :type obj: str
    
    :returns: long
    :rtype: str | None
    """
    if not cmds.objExists(obj):
        cmds.warning("Object {} does not exist.".format(obj))
        return
    return str(cmds.ls(obj, l=True)[0])


def getShortName(obj):
    """
    Returns the short name of a given object
    
    :param obj: object path
    :type obj: str
    
    :returns: long
    :rtype: str | None
    """
    if not cmds.objExists(obj):
        cmds.warning("Object {} does not exist.".format(obj))
        return
    return str(cmds.ls(obj, l=True)[0].split('|')[-1])


def isUniqueName(name):
    """
    Check if name is unique
    :param name: string to test
    :type name: str
    :return: if the name is unique
    :rtype: bool
    """

    return False if len(cmds.ls(name)) > 1 else True


def getUniqueName(name, side=None, indexPosition=-1):
    """
    Add an index to the given name. The last interger found in the string will be used as the index.
    :param name: name to check
    :param side: side to add to the name
    :param indexPosition: where to add the index if one is not found. default is -2 (after the suffix)
    :return: returns a new unique name
    """
    name = common.getFirstIndex(name)

    if side:
        name = "{}_{}".format(name, side)

    # name is already unique
    if not cmds.objExists(name):
        return name

    nameSplit = name.split(DELIMINATOR)
    indexStr = [int(s) for s in nameSplit if s.isdigit()]

    if indexStr:
        # Get the location in the name the index appears.
        # Then incriment the index and replace the original in the nameSplit
        indexPosition = nameSplit.index(str(indexStr[-1]))
        oldIndex = (int(indexStr[-1]) if indexStr else -1)
        newIndex = oldIndex + 1
    else:
        # if the index is '-1' add the new index to the end of the string instead of inserting it.
        newIndex = 1
        if indexPosition == -1:
            nameSplit.append(str(newIndex))
        # if the nameSplit is greater than the index, add the index to the end instead of inserting it.
        elif len(nameSplit) >= abs(indexPosition):
            nameSplit.insert(indexPosition + 1, str(newIndex))
        else:
            nameSplit.append(str(newIndex))
            indexPosition = -1

    # check if an object exists with the name until we find a unique name.
    for i in range(2000):
        nameSplit[indexPosition] = str(newIndex)
        newName = DELIMINATOR.join(nameSplit)
        if cmds.objExists(newName):
            newIndex += 1
        else:
            return newName


def formatName(base=None, side=None, location=None, warble=None, index=None, ext=None):
    """
    Take given arguments and formats them into the naming convention
    """
    if not base:
        raise RuntimeError("Must supply a base to create a name.")
    if not side:
        side = ''
    if not location:
        location = ''
    if not warble:
        warble = ''
    if not ext:
        ext = ''
    if not index:
        index = ''
    else:
        index = str(index).zfill(common.PADDING)

    name = str(
        common.NAMETEMPLATE.format(BASE=base,
                                   SIDE=side,
                                   LOCATION=location,
                                   WARBLE=warble,
                                   INDEX=index,
                                   EXTENSION=ext))

    # Look through the string and remove any double underscores.
    # These may appear if some attributes are not provided
    rx = re.compile(r'_{2,}')
    name = rx.sub('_', name)

    return normalize(name)
