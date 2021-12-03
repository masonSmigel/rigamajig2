"""
Functions to add metadata to nodes
"""
import json
import logging
from collections import OrderedDict
import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.maya.attr as rig_attr

logger = logging.getLogger(__name__)

EXCLUDED_JSON_ATTRS = ['attributeAliasList']


def tag(nodes, tag, type=None):
    """
    Tag the specified nodes with the proper type
    :param nodes: nodes to add the tag to
    :type nodes: str | list
    :param tag: tag to add
    :type tag: str
    :param type: type of tag
    :type type: str
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.objExists(node):
            if not cmds.objExists("{}.__{}__".format(node, tag)):
                cmds.addAttr(node, ln='__{}__'.format(tag), at='message')
            if type:
                if not cmds.objExists("{}.__{}_{}__".format(node, type, tag)):
                    cmds.addAttr(node, ln='__{}_{}__'.format(type, tag), at='message')


def untag(nodes, tag):
    """
    Remove the tag from the nodes
    :param nodes: nodes to remove the tag to
    :type nodes: str | list
    :param tag: tag to remove
    :type tag: str
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.objExists(node):
            udAttrs = cmds.listAttr(node, ud=True) or list()

            for attr in udAttrs:
                if "{}__".format(tag) in attr:
                    cmds.deleteAttr("{}.{}".format(node, attr))


def getTagged(tag, namespace=None):
    """
    Get a list of all the objects with a tag in a scene.
    :param tag: tag to get
    :type tag: str
    :param namespace: Get controls found within a specific namespace
    :type namespace: str
    :return:
    """
    if not namespace:
        return [s.split(".")[0] for s in cmds.ls("*.__{}__".format(tag))]
    else:
        return [s.split(".")[0] for s in cmds.ls("{}:*.__{}__".format(namespace, tag))]


def addMessageConnection(sourceNode, dataNode, sourceAttr, dataAttr=None):
    """
    Add a message connection between a source and target node
    :param sourceNode: source node of the message connection
    :param dataNode: destination of the message connection
    :param sourceAttr: name of the source attribute
    :param dataAttr: name of the destination attribute
    """
    if cmds.objExists("{}.{}".format(dataNode, dataAttr)):
        raise RuntimeError("The desination '{}.{}' already exist".format(dataNode, dataAttr))
    if not cmds.objExists("{}.{}".format(sourceNode, sourceAttr)):
        cmds.addAttr(sourceNode, ln=sourceAttr, at='message')
    if dataAttr is None:
        dataAttr = sourceAttr
    cmds.addAttr(dataNode, ln=dataAttr, at='message')
    cmds.connectAttr("{}.{}".format(sourceNode, sourceAttr), "{}.{}".format(dataNode, dataAttr))


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
        if len(data) > 1:
            return data
        else:
            return common.getFirstIndex(data)
    elif not silent:
        raise RuntimeError('Plug "{}" does not exist'.format(dataPlug))
    else:
        return None


def validateDataType(val):
    """
    Validate the attribute type for all the  handling
    """
    if issubclass(type(val), str): return 'string'
    if issubclass(type(val), unicode): return 'unicode'
    if issubclass(type(val), bool): return 'bool'
    if issubclass(type(val), int): return 'int'
    if issubclass(type(val), float): return 'float'
    if issubclass(type(val), dict): return 'complex'
    if issubclass(type(val), list): return 'complex'
    if issubclass(type(val), tuple): return 'complex'


class MetaNode(object):
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
        :param attr:
        :return: value of the attribute. as the serialized type.
        :rtype: str | float | list | dict
        """
        if not cmds.objExists("{}.{}".format(self.node, attr)):
            raise RuntimeError("Attribute {} does not exist on the node {}".format(attr, self.node))

        value = cmds.getAttr("{}.{}".format(self.node, attr), silent=True)
        attrType = cmds.getAttr("{}.{}".format(self.node, attr), type=True)

        # TODO : what are we gonnna do with message attributes?!??
        if attrType == 'message':
            return None
        if attrType == 'string':
            try: value = self.__deserializeComplex(value)  # if the data is a string try to deserialize it.
            except: logger.debug('string {} is not json deserializable'.format(value))
        return value

    def getAllData(self, excludedAttrs=[]):
        """
        Retrieve all data from the maya node.
        :param excludedAttrs: Optoinal - list of attributes to data collection from.
        :return: dictionary of data on the node
        :rtype: OrderedDict
        """
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

        data_type_dict = {'string': {'dt': 'string'},
                          'unicode': {'dt': 'string'},
                          'int': {'at': 'long'},
                          'long': {'at': 'long'},
                          'bool': {'at': 'bool'},
                          'float': {'at': 'double'},
                          'double': {'at': 'double'},
                          'enum': {'at': 'enum'},
                          'complex': {'dt': 'string'}}

        attrType = validateDataType(value)

        if attrType == 'complex':
            value = self.__serializeComplex(value)
            attrType = validateDataType(value)
        # if the attribute does not exist then add the attribute
        if not cmds.objExists("{}.{}".format(self.node, attr)):
            cmds.addAttr(self.node, longName=attr, **data_type_dict[attrType])
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

    def __serializeComplex(self, data):
        """
        Serialize data into a string for use in maya.
        Also check to see if the string is longer than the length maya will allow before trunicating it.
        :param data: data to serialize
        :return: serialized data
        """
        if len(data) > 32700:
            logger.warning('Length of string is over 16bit Maya Attr Template limit - lock this after setting it!')
        return json.dumps(data)

    def __deserializeComplex(self, data):
        """
        Deserialize data into a string for use with json.
        :param data: data to deserialize
        :return: deserialized data
        """
        if isinstance(data, unicode):
            return json.loads(str(data))
        return json.loads(data)
