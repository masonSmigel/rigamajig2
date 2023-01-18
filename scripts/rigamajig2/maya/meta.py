"""
Functions to add and manage metadata to nodes
"""
import json
import sys
import logging
from collections import OrderedDict
from ast import literal_eval
import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.attr as rig_attr

logger = logging.getLogger(__name__)

EXCLUDED_JSON_ATTRS = ['attributeAliasList']

if sys.version_info.major >= 3:
    basestring = str
    unicode = basestring


def tag(nodes, tag, type=None):
    """
    Tag the specified nodes with the proper type

    :param str list nodes: nodes to add the tag to
    :param str tag: tag to add
    :param str type: type of tag
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.objExists(node):
            if type:
                if not cmds.objExists("{}.__{}_{}__".format(node, type, tag)):
                    cmds.addAttr(node, ln='__{}_{}__'.format(type, tag), at='message')
            elif not cmds.objExists("{}.__{}__".format(node, tag)):
                cmds.addAttr(node, ln='__{}__'.format(tag), at='message')


def untag(nodes, tag):
    """
    Remove the tag from the nodes

    :param str list nodes: nodes to remove the tag to
    :param str tag: tag to remove
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.objExists(node):
            udAttrs = cmds.listAttr(node, ud=True) or list()

            for attr in udAttrs:
                if "{}__".format(tag) in attr:
                    cmds.deleteAttr("{}.{}".format(node, attr))


def getTagged(tag, type=None, namespace=None):
    """
    Get a list of all objects with a given tag in the scene.
    If there are namespaces in your scene and you wish to get tagged nodes that belong to a namespace you must also provide the namespace.
    This is to allow users to get tagged nodes specific to a character.

    :param str tag: tag to get
    :param type: specify a tag type to get
    :param str namespace: Get controls found within a specific namespace
    :return: nodes with a given tag
    :rtype: list
    """
    if type:
        tag = "{}_{}".format(type, tag)
    if not namespace:
        return [s.split(".")[0] for s in cmds.ls("*.__{}__".format(tag))]
    else:
        return [s.split(".")[0] for s in cmds.ls("{}:*.__{}__".format(namespace, tag))]


def hasTag(node, tag, type=None):
    """
    Check if a specified node has a given tag

    :param str node: nodes to check tag
    :param str tag: tag to check for
    :param type: specify a tag type to get
    :return: True if node has tag. false if it doesnt.
    :rtype: bool
    """
    node = common.getFirstIndex(node)

    if type:
        tag = "{}_{}".format(type, tag)

    if cmds.objExists("{}.__{}__".format(node, tag)):
        return True
    return False


# TODO: refactor all this!


def createMessageConnection(sourceNode, destNode, sourceAttr, destAttr=None):
    """
    Add a message connection between a source and destination node.

    If the destination node is a list it will create a multi-message attribute for the connection.

    :param sourceNode: source node of the message connection
    :param destNode: destination of the message connection
    :param sourceAttr: name of the source attribute
    :param destAttr: name of the destination attribute
    """
    if cmds.objExists("{}.{}".format(destNode, destAttr)):
        raise RuntimeError("The desination '{}.{}' already exist".format(destNode, destAttr))

    asMessageList = False
    if isinstance(destNode, (list, tuple)):
        asMessageList = True
        destList = destNode

    if not cmds.objExists("{}.{}".format(sourceNode, sourceAttr)):
        cmds.addAttr(sourceNode, ln=sourceAttr, at='message', m=asMessageList)

    if destAttr is None:
        destAttr = sourceAttr

    # if the destNode is a list then create a complex message connection.
    if asMessageList:
        for destNode in destList:
            nextIndex = rig_attr.getNextAvailableElement("{}.{}".format(sourceNode, sourceAttr))
            cmds.addAttr(destNode, ln=destAttr, at='message')
            cmds.connectAttr(nextIndex, "{}.{}".format(destNode, destAttr))

    # otherwise create a simple message connection.
    else:
        cmds.addAttr(destNode, ln=destAttr, at='message')
        cmds.connectAttr("{}.{}".format(sourceNode, sourceAttr), "{}.{}".format(destNode, destAttr))


def addMessageListConnection(sourceNode, dataList, sourceAttr, dataAttr=None):
    """
    Add a message connection between a source and list of data nodes

    :param sourceNode: source node of the message connection
    :param dataList: destination of the message connection
    :param sourceAttr: name of the source attribute
    :param dataAttr: name of the destination attribute
    """
    dataList = common.toList(dataList)
    for dataNode in dataList:
        if cmds.objExists("{}.{}".format(dataNode, dataAttr)):
            raise RuntimeError("The desination '{}.{}' already exist".format(dataNode, dataAttr))
    if not cmds.objExists("{}.{}".format(sourceNode, sourceAttr)):
        cmds.addAttr(sourceNode, ln=sourceAttr, at='message', m=True)
    if dataAttr is None:
        dataAttr = sourceAttr
    for dataNode in dataList:
        nextIndex = rig_attr.getNextAvailableElement("{}.{}".format(sourceNode, sourceAttr))
        cmds.addAttr(dataNode, ln=dataAttr, at='message')
        cmds.connectAttr(nextIndex, "{}.{}".format(dataNode, dataAttr))


def getMessageConnection(dataPlug, silent=True):
    """
    Get the data connected to the given plug.

    :param dataPlug: plug to get the message for
    :param silent: if the function fails return None instead of erroring
    :return: nodes connected to the message attribute. if the attribute has multiconnections return a list.
    """
    if cmds.objExists(dataPlug):
        data = cmds.listConnections(dataPlug, d=True)
        if not data:
            data = cmds.listConnections(dataPlug, s=True)
        if data is None:
            return
        if len(data) > 1:
            return data
        else:
            return common.getFirstIndex(data)
    elif not silent:
        raise RuntimeError('Plug "{}" does not exist'.format(dataPlug))

    return None


# pylint:disable = too-many-return-statements
def validateDataType(val):
    """
    Validate the attribute type for all the value handling. This function will return a string describing the type of the value.

    :param val: value to check the type of
    :return: value type as a string
    :rtype: str
    """
    if issubclass(type(val), str):
        try:
            val = literal_eval(val)
        except:
            return "string"
        if issubclass(type(val), dict): return 'complex'
        if issubclass(type(val), list): return 'complex'
        if issubclass(type(val), tuple): return 'complex'
    if issubclass(type(val), unicode): return 'string'
    if issubclass(type(val), bool): return 'bool'
    if issubclass(type(val), int): return 'int'
    if issubclass(type(val), float): return 'float'
    if issubclass(type(val), dict): return 'complex'
    if issubclass(type(val), list): return 'complex'
    if issubclass(type(val), tuple): return 'complex'


class MetaNode(object):
    """Meta Node class"""
    def __init__(self, node):
        """
        Constructor for mayaJson.
        Alot of this is derived from Red9, but simplified.

        :param node: node to hold json data
        """
        self.node = node

    def getData(self, attr):
        """
        Retrieve  data of a specific attribute. deserialized data from json.

        :param attr: name of the attribute to get the associated data for
        :return: value of the attribute. as the serialized type.
        :rtype: str | float | list | dict
        """
        if not cmds.objExists("{}.{}".format(self.node, attr)):
            raise RuntimeError("Attribute {} does not exist on the node {}".format(attr, self.node))

        attrType = cmds.getAttr("{}.{}".format(self.node, attr), type=True)

        # TODO : what are we gonnna do with message attributes?!??
        if attrType == 'message':
            return None

        value = cmds.getAttr("{}.{}".format(self.node, attr), silent=True)
        if attrType == 'string':
            try:
                value = self.deserializeComplex(value)  # if the data is a string try to deserialize it.
            except:
                logger.debug('string {} is not json deserializable'.format(value))
        return value

    def getAllData(self, excludedAttrs=None):
        """
        Retrieve all data from the maya node.

        :param excludedAttrs: Optoinal - list of attributes to data collection from.
        :return: dictionary of data on the node
        :rtype: OrderedDict
        """
        if excludedAttrs is None:
            excludedAttrs = list()
        userAttrs = list([str(a) for a in cmds.listAttr(self.node, ud=True) or [] if '.' not in a])
        data = OrderedDict()
        for attr in userAttrs:
            if attr in EXCLUDED_JSON_ATTRS + excludedAttrs: continue
            data[attr] = self.getData(attr)
        return data

    def setData(self, attr, value, hide=True, lock=False):
        """
        Add data to a node. Stored as serialized json data

        :param attr: attribute to hold the data
        :param value: value to store
        :param hide: hide the attributes from the channelbox. Note string attributes cannot be keyable!!
        :param lock: lock the attributes from the channelbox.
        """

        dataTypeDict = {'string': {'dt': 'string'},
                        'unicode': {'dt': 'string'},
                        'int': {'at': 'long'},
                        'long': {'at': 'long'},
                        'bool': {'at': 'bool'},
                        'float': {'at': 'double'},
                        'double': {'at': 'double'},
                        'enum': {'at': 'enum'},
                        'complex': {'dt': 'string'}}

        attrType = validateDataType(value)
        if attrType is None:
            return

        if attrType == 'complex':
            value = self.serializeComplex(value)
            attrType = validateDataType(value)
        # if the attribute does not exist then add the attribute
        if not cmds.objExists("{}.{}".format(self.node, attr)):
            cmds.addAttr(self.node, longName=attr, **dataTypeDict[attrType])
        else:
            # Todo: try to change the attribute data if it doesnt match
            pass

        rig_attr.setPlugValue("{}.{}".format(self.node, attr), value=value)

        if not hide:
            cmds.setAttr("{}.{}".format(self.node, attr), k=True)
        if lock:
            cmds.setAttr("{}.{}".format(self.node, attr), l=True)

    def setDataDict(self, data, hide=True, lock=False):
        """
        Store a dictionary into custom attributes on a maya node

        :param data: dictonary to set data to.
        :param hide: hide the attributes from the channelbox. Note string attributes cannot be keyable!!
        :param lock: lock the attributes from the channelbox.
        """

        for attr, value in data.items():
            self.setData(attr, value, hide=hide, lock=lock)

    def serializeComplex(self, data):
        """
        Serialize data into a string for use in maya.
        Also check to see if the string is longer than the length maya will allow before trunicating it.

        :param data: data to serialize
        :return: serialized data
        """
        if len(data) > 32700:
            logger.warning('Length of string is over 16bit Maya Attr Template limit - lock this after setting it!')
        return json.dumps(data)

    def deserializeComplex(self, data):
        """
        Deserialize data into a string for use with json.

        :param data: data to deserialize
        :return: deserialized data
        """
        if isinstance(data, basestring):
            return json.loads(str(data))
        return json.loads(data)
