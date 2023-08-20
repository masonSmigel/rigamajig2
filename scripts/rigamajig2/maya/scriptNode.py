"""Script node utilities """
import maya.cmds as cmds
import inspect
import os

from rigamajig2.shared import common

SCRIPT_TYPES = [
    "Demand",
    "Open/Close",
    "GUI Open/Close",
    "UI Configuration (Interna)",
    "Software Render",
    "Software Frame Render",
    "Scene Configuration (Internal)",
    "Time Changed"]

FUNCTION_FORMAT = """# scriptNode created with rigamajig from: {function}

{imports}


{src}
if __name__ == '__main__':
    {call}
"""

DEFAULT_IMPORTS = 'import maya.cmds as cmds'

def isScriptNode(name):
    """
    Check if a node is a script Node.

    :param name: name of the node to check if it is a script node
    :return: return True if the node is a script node. False if not
    :rtype: bool
    """
    if not cmds.objExists(name): return False
    if 'script' not in cmds.nodeType(name, i=True): return False
    return True


def create(name, sourceType='python', scriptType='Open/Close', beforeScript=None, afterScript=None, extraImports=None):
    """
    Create a new script node.

    :param str name: Name of the script node
    :param str sourceType: Source type. Valid values are 'mel' and 'python'
    :param str scriptType: Specified when the script is executed.
    :param str function beforeScript: The script executed during file load. Use a string or a python function.
    :param str function afterScript: The script executed when the script node is deleted. Use a string or a python function.
    :param list extraImports: Additional stuff to import into the file
    :return: the name of the script node created
    :rtype: str
    """
    if sourceType != 'mel':
        sourceType = 'python'

    if scriptType not in SCRIPT_TYPES:
        raise RuntimeError('The script type "{}" is not valid. valid types are: {}'.format(scriptType, SCRIPT_TYPES))

    if cmds.objExists(name):
        raise RuntimeError("Object {} already exists. Cannot create a scriptNode with that name".format(name))

    # check if the before or after script is callable. if it is turn it into a string.

    imports = DEFAULT_IMPORTS
    if extraImports:
        extraImports = common.toList(extraImports)
        for line in extraImports:
            imports += f"\n{line}"

    if callable(beforeScript):
        beforeScript = validateScriptString(beforeScript, defaultImports=imports)
    if callable(afterScript):
        afterScript = validateScriptString(afterScript, defaultImports=imports)

    # if the before and after script is None then ensure it wont throw a syntax error
    if not beforeScript: beforeScript = 'pass' if sourceType == 'python' else ''
    if not afterScript: afterScript = 'pass' if sourceType == 'python' else ''

    scriptNode = cmds.scriptNode(n=name,
                                 scriptType=SCRIPT_TYPES.index(scriptType),
                                 sourceType=sourceType,
                                 beforeScript=beforeScript,
                                 afterScript=afterScript,
                                 )
    print("New script node {} created".format(name))
    return scriptNode


def createFromFile(name, scriptType='Open/Close', beforeScript=None, afterScript=None):
    """
    Wrapper to create a script node from a file. Use either a mel or python file to create a scriptNode from a file.

    :param str name: Name of the script node
    :param str scriptType: Specified when the script is executed.
    :param str beforeScript: The script executed during file load. Use a path to a file.
    :param str afterScript: The script executed when the script node is deleted. Use a path to a file.
    :return: the name of the script node created
    :rtype: str
    """
    beforeExt = afterExt = None
    if afterScript and os.path.exists(afterScript):
        afterExt = afterScript.split('.')[-1]
        with open(afterScript) as f:
            afterScript = f.read()

    if beforeScript and os.path.exists(beforeScript):
        beforeExt = beforeScript.split('.')[-1]
        with open(beforeScript) as f:
            beforeScript = f.read()

    # Get the source type
    if beforeExt and afterExt and beforeExt != afterExt:
        raise RuntimeError('Before script and After script have different source types')

    sourceType = beforeExt if beforeExt else afterExt

    return create(name=name, sourceType=sourceType, scriptType=scriptType,
                  beforeScript=beforeScript, afterScript=afterScript)


def getScriptNodes():
    """
    Return a list of all script nodes in the scene

    :return: a list of all script nodes in the scene
    :rtype: list
    """
    return cmds.ls(type='script')


def removeAllScriptNodes():
    """
    Remove all script nodes from the scene
    """
    cmds.delete(cmds.ls(type='script'))


def validateScriptString(script, defaultImports=''):
    """
    Validate a script. This will turn a function or file into a string

    :param str script:  callable script to run
    :param defaultImports: Imports to add to the begining of the file.
    :return: script converted to a string
    :rtype: str
    """
    if inspect.isfunction(script):
        functionSource = inspect.getsource(script)
        functionCall = script.__name__ + '()'
        functionPath = ".".join([script.__module__, script.__name__])
        return FUNCTION_FORMAT.format(function=functionPath, imports=defaultImports, src=functionSource, call=functionCall)
