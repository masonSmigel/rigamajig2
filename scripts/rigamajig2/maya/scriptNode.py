"""Script node utilities """
import maya.cmds as cmds
import inspect
import os

scriptTypes = [
    "Demand",
    "Open/Close",
    "GUI Open/Close",
    "UI Configuration (Interna)",
    "Software Render",
    "Software Frame Render",
    "Scene Configuration (Internal)",
    "Time Changed"]

func_format = """# scriptNode created with rigamajig from {function}

{imports}


{src}
if __name__ == '__main__':
    {call}
"""


def isScriptNode(name):
    """
    Check if a node is a script Node
    :param name:
    :return:
    """
    if not cmds.objExists(name): return False
    if 'script' not in cmds.nodeType(name, i=True): return False
    return True


def create(name, sourceType='python', scriptType='Open/Close', beforeScript=None, afterScript=None):
    """
    Create a new script node.
    :param name: Name of the script node
    :param sourceType: Source type. Valid values are 'mel' and 'python'
    :param scriptType: Specified when the script is executed.
    :param beforeScript: The script executed during file load. Use a string or a python function.
    :type beforeScript: str | function
    :param afterScript: The script executed when the script node is deleted. Use a string or a python function.
    :type afterScript: str | function
    :return:
    """
    if not sourceType == 'mel':
        sourceType = 'python'

    if scriptType not in scriptTypes:
        raise RuntimeError('The script type "{}" is not valid. valid types are: {}'.format(scriptType, scriptTypes))

    if cmds.objExists(name):
        raise RuntimeError("Object {} already exists. Cannot create a scriptNode with that name".format(name))

    # check if the before or after script is callable. if it is turn it into a string.
    if callable(beforeScript):
        beforeScript = validateScriptString(beforeScript, defaultImports='import maya.cmds as cmds')
    if callable(afterScript):
        afterScript = validateScriptString(afterScript, defaultImports='import maya.cmds as cmds')

    # if the before and after script is None then ensure it wont throw a syntax error
    if not beforeScript: beforeScript = 'pass' if sourceType == 'python' else ''
    if not afterScript: afterScript = 'pass' if sourceType == 'python' else ''

    scriptNode = cmds.scriptNode(n=name,
                                 scriptType=scriptTypes.index(scriptType),
                                 sourceType=sourceType,
                                 beforeScript=beforeScript,
                                 afterScript=afterScript,
                                 )
    return scriptNode


def createFromFile(name, scriptType='Open/Close', beforeScript=None, afterScript=None):
    """
    Wrapper to create a script node from a file. Use either a mel or python file to create a scriptNode from a file.
    :param name: Name of the script node
    :param scriptType: Specified when the script is executed.
    :param beforeScript: The script executed during file load. Use a path to a file.
    :type beforeScript: str
    :param afterScript: The script executed when the script node is deleted. Use a path to a file.
    :type afterScript: str
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
    return cmds.ls(type='script')


def validateScriptString(script, defaultImports=''):
    """
    Validate a script. This will turn a function or file into a string
    :param script:  callable script to run
    :param defaultImports: Imports to add to the begining of the file.
    :return:
    """
    if inspect.isfunction(script):
        func_src = inspect.getsource(script)
        func_call = script.__name__ + '()'
        return func_format.format(function=str(script), imports=defaultImports, src=func_src, call=func_call)
