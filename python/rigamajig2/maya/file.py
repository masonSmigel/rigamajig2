"""
Functions for working with maya files more easily
"""

import os
import sys

import maya.OpenMaya as om
import maya.cmds as cmds

MAYA_FILE_FILTER = (
    "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);;All Files (*.*);;"
)
IMPORT_FILE_FILTER = "All Files (*.*);;{0};;Obj (*.obj);; FBX (*.fbx);;".format(
    MAYA_FILE_FILTER
)
DELIMINATOR = "_"
VERSION_TOKEN = "v"


def _pathDialog(
    cap="Select a file",
    acceptCaption="Do Stuff",
    cancleCaption="Cancel",
    fileMode=1,
    fileFilter=MAYA_FILE_FILTER,
):
    file = cmds.fileDialog2(
        ds=2, cap=cap, okc=acceptCaption, cc=cancleCaption, fm=fileMode, ff=fileFilter
    )
    if file:
        return file[0]
    return None


def new(f=False):
    """
    Create a new file and run the container sanity check

    :param f: force the opperation to occur
    """
    cmds.file(new=True, f=f)
    # run the container sainity check
    import rigamajig2.maya.container as container

    if om.MGlobal.mayaState():
        return
    container.sainityCheck()


# Disable the name error here, we want to keep the name as open,
# so we add an underscore to the end to avoid conflicting with pythin builtin
# pylint: disable=invalid-name
def open_(path=None, f=False):
    """
    Open a maya file

    :param path: path to maya file
    :param f: force the opperation to occur
    """
    if not path:
        path = _pathDialog(
            cap="Open",
            acceptCaption="Open",
        )
    cmds.file(path, o=True, f=f, ignoreVersion=True)


def save(log=True):
    """
    save the current scene

    :return: the path to the file saved
    :rtype: str
    """
    sceneName = cmds.file(q=True, sn=True)
    extension = sceneName.split(".")[-1]

    if extension == "ma":
        fileType = "mayaAscii"
    elif extension == "mb":
        fileType = "mayaBinary"
    else:
        raise RuntimeError("Must save using a maya file type: mayaAscii or mayaBinary")

    file = cmds.file(s=True, typ=fileType)
    if log:
        print('File saved to "{}"'.format(file))
    return file


def saveAs(path=None, log=True):
    """
    Save the current scene as

    :param path: path to save the file
    :param log: log the output
    :return: path to the file saved
    :rtype: str
    """
    if not path:
        path = _pathDialog(cap="Save As", acceptCaption="Save As", fileMode=0)

    if path:
        cmds.file(rename=path)
        return save(log=log)
    return None


def incrimentSave(path=None, padding=3, indexPosition=-1, log=True):
    """
    Incrimental save with a better naming convention.
    Naming convention is made as follows:
        baseName_v001.warble.ext

    :param path: path to the file to save
    :param padding: Amount of padding to add to the index
    :param indexPosition: Optional - Index position, default will be -1
    :param log: log the output
    :return: path to the file saved
    :rtype: str
    """
    if not path:
        path = cmds.file(q=True, loc=True)
    # if we dont have a scene open give the user the option to save the scene
    if path == "unknown":
        return saveAs()

    # Get the directory and file
    dir = os.path.dirname(path)
    file = os.path.basename(path)

    # Separate out the base name, the extension and any exta
    baseName = file.split(".")[0]
    extension = file.split(".")[-1]
    warble = ".".join(file.split(".")[1:-1])

    fileSplit = baseName.split(DELIMINATOR)
    indexStr = [s for s in fileSplit if s.startswith(VERSION_TOKEN)]

    if indexStr:
        indexPosition = fileSplit.index(str(indexStr[-1]))
        oldIndexStr = indexStr[-1] if indexStr else -1
        oldIndexInt = int(oldIndexStr.replace(VERSION_TOKEN, ""))
        newIndex = oldIndexInt + 1
    else:
        newIndex = 1
        # if the index is '-1' add the new index to the end of the string instead of inserting it.
        if indexPosition == -1:
            fileSplit.append(str(newIndex).zfill(padding))
        # if the fileSplit is greater than the index, add the index to the end instead of inserting it.
        elif len(fileSplit) >= abs(indexPosition):
            fileSplit.insert(indexPosition + 1, str(newIndex).zfill(padding))
        else:
            fileSplit.append(str(newIndex).zfill(padding))
            indexPosition = -1

    # validate the new name
    for _ in range(2000):
        newIndexStr = "v{}".format(str(newIndex).zfill(padding))
        fileSplit[indexPosition] = newIndexStr
        nameBase = DELIMINATOR.join(fileSplit)

        if warble:
            newFileName = ".".join([nameBase, warble, extension])
        else:
            newFileName = ".".join([nameBase, extension])

        path = os.path.join(dir, newFileName)
        if not isUniqueFile(path):
            newIndex += 1
        else:
            break
    return saveAs(path, log=log)


# Disable the name error here, we want to keep the name as import,
# so we add an underscore to the end to avoid conflicting with pythin builtin
# pylint: disable=invalid-name
def import_(path=None, useNamespace=False, namespace=None, force=False):
    """
    import a file

    :param path: path to the file to import
    :param useNamespace: import with a namespace
    :param force: force the opperation to occur
    :return: path of the file imported
    :rtype: str
    """
    if not path:
        path = _pathDialog(
            cap="Import",
            acceptCaption="Import",
            fileMode=0,
            fileFilter=IMPORT_FILE_FILTER,
        )

    kwargs = {"i": True, "f": force, "rnn": True}
    if namespace or useNamespace:
        namespace = namespace or os.path.basename(path).split(".")[0]
        kwargs["ns"] = namespace

    file = cmds.file(path, ignoreVersion=True, **kwargs)
    return file


def reference(path=None):
    """
    Reference a file

    :param path: path to the file to reference
    :return: name of the file path imported
    :rtype: str
    """
    if not path:
        path = _pathDialog(
            cap="Reference",
            acceptCaption="Reference",
            fileMode=0,
            fileFilter=MAYA_FILE_FILTER,
        )
    namespace = os.path.basename(path).split(".")[0]
    return cmds.file(path, r=True, ns=namespace)


def isUniqueFile(path):
    """
    Check if file is unique. A file is unique if no other files with the same name exist in the directory

    :param str path: file to test
    :return: True if the name is unique
    :rtype: bool
    """
    return False if os.path.exists(path) else True


def getEnvironment():
    """
    print out a bunch of enviornment variables for maya
    """
    import platform

    if platform == "win32":
        sep = os.sep
    elif platform == "darwin":
        sep = ":"
    else:
        sep = ":"

    scriptPaths = os.getenv("MAYA_SCRIPT_PATH") or ""
    plugInPaths = os.getenv("MAYA_PLUG_IN_PATH") or ""
    pythonPaths = os.getenv("PYTHONPATH") or ""
    shelfPath = os.getenv("MAYA_SHELF_PATH") or ""
    iconPaths = os.getenv("XBMLANGPATH") or ""
    pathPaths = os.getenv("PATH") or ""
    sysPaths = sys.path

    allScriptPaths = scriptPaths.split(sep)
    print("\nMAYA_SCRIPT_PATHs are:")
    for scriptPath in allScriptPaths:
        print(scriptPath)

    allPlugInPaths = plugInPaths.split(sep)
    print("\nMAYA_PLUG_IN_PATHs are:")
    for plugInPath in allPlugInPaths:
        print(plugInPath)

    allPythonPaths = pythonPaths.split(sep)
    print("\nPYTHONPATHs are:")
    for pythonPath in allPythonPaths:
        print(pythonPath)

    allShelfPaths = shelfPath.split(sep)
    print("\nMAYA_SHELF_PATH are:")
    for shelfPath in allShelfPaths:
        print(shelfPath)

    allIconPaths = iconPaths.split(sep)
    print("\nXBMLANGPATHs are:")
    for iconPath in allIconPaths:
        print(iconPath)

    allPathPaths = pathPaths.split(sep)
    print("\nPATHs are:")
    for pathPath in allPathPaths:
        print(pathPath)

    print("\nsys.paths are:")
    for sysPath in sysPaths:
        print(sysPath)
