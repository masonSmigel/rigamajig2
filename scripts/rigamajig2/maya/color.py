"""
Color Utilities
"""
import maya.cmds as cmds
from collections import OrderedDict


def rgbToPercent(color):
    """
    Returns the RGB color between a value of 0 - 1

    :param list tuple color: RGB color in 0-255 space
    """
    return [float(x) / 255 for x in color]


def rgbToHex(color):
    """
    Returns color in hex format

    :param list tuple color: RGB color in 0-255 space
    """
    return '#{:02X}{:02X}{:02X}'.format(color.red, color.green, color.blue)


COLORS = OrderedDict(
    black=(0, 0, 0),
    darkgray=(40, 40, 40),
    lightgray=(81, 81, 81),
    maroon=(84, 0, 5),
    blue=(0, 0, 255),
    darkgreen=(0, 16, 2),
    darkpurple=(5, 0, 14),
    brightpurple=(147, 0, 147),
    brown=(65, 16, 8),
    darkbrown=(13, 4, 3),
    brick=(81, 5, 0),
    red=(255, 0, 0),
    green=(0, 255, 0),
    cobalt=(0, 13, 81),
    white=(255, 255, 255),
    yellow=(255, 255, 0),
    lightblue=(32, 183, 255),
    lightgreen=(14, 255, 93),
    lightpink=(255, 11, 11),
    lightorange=(198, 105, 49),
    lightyellow=(255, 255, 32),
    grass=(0, 81, 23),
    darkorange=(90, 36, 8),
    yellowgreen=(88, 90, 8),
    greenyellow=(36, 90, 8),
    springgreen=(8, 90, 28),
    turquoise=(8, 90, 90),
    skyblue=(8, 35, 90),
    purple=(41, 8, 90),
    magenta=(90, 8, 36),

    aqua=(0, 128, 128),
    banana=(255, 255, 32),
    crimson=(220, 20, 60),
    cyan=(0, 238, 238),
    lightgreenyellow=(173, 255, 47),
    indigo=(138, 43, 226),
    limegreen=(50, 205, 50),
    midnightblue=(25, 25, 112),
    orange=(255, 128, 0),
    orangered=(255, 69, 0),
    salmon=(250, 128, 114),
    sienna=(138, 54, 15),
    seagreen=(0, 164, 162),
    slateblue=(132, 112, 255),
    slategray=(112, 128, 144),
    tan=(210, 180, 140),
    violet=(238, 130, 238),
    violetred=(208, 32, 144),
)

MAYA_INDEX_COLORS = OrderedDict(
    black=1, darkgray=2, lightgray=3, maroon=4, blue=6, darkgreen=7, darkpurple=8,
    brightpurple=9, brown=10, darkbrown=11, brick=12, red=13, green=14, cobalt=15, white=16,
    yellow=17, lightblue=18, lightgreen=19, lightpink=20, lightorange=21, lightyellow=22,
    grass=23, darkorange=24, yellowgreen=25, greenyellow=26, springgreen=27, turquoise=28,
    skyblue=29, purple=30, magenta=31)


def getAvailableColors():
    """
    Get a list of all available colors.
    The color string can be used to set the override or outliner color.

    :return: a list of all available colors
    :rtype: list
    """
    return COLORS.keys()


def setOverrideColor(nodes, color):
    """
    Sets the color of shapes in the viewport.

    :param str list nodes: nodes to set the override color to
    :param int list tuple str color: Color to set on the nodes. Use either an RGB value, or index.
                    you can also use a string name. use color.getAvailableColors() to get a list of all colors
    """
    useIndex = True
    strColor = None
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    if isinstance(color, str):
        strColor = color
        color = COLORS[color]

    if isinstance(color, (list, tuple)):
        if strColor in MAYA_INDEX_COLORS.keys():
            color = MAYA_INDEX_COLORS[strColor]
        else:
            color = rgbToPercent(color)
            useIndex = False

    for node in nodes:
        cmds.setAttr("{}.overrideEnabled".format(node), 1)
        if useIndex:
            cmds.setAttr("{}.overrideRGBColors".format(node), 0)
            cmds.setAttr("{}.overrideColor".format(node), color)
        else:
            cmds.setAttr("{}.overrideRGBColors".format(node), 1)
            cmds.setAttr("{}.overrideColorRGB".format(node), color[0], color[1], color[2])


def setOutlinerColor(nodes, color):
    """
    Sets the color of nodes in the outliner
    :param list nodes: nodes to set the override color to
    :param tuple list str color: Color to set on the nodes. Used as an RGB value.
                  You can also use constants like color.RED, color.BLUE or color.LIGHT_YELLOW
    """
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    if isinstance(color, str):
        color = COLORS[color]

    color = rgbToPercent(color)
    for node in nodes:
        cmds.setAttr("{}.useOutlinerColor".format(node), 1)
        cmds.setAttr("{}.outlinerColor".format(node), color[0], color[1], color[2])
