""" Drag and Drop installer for rigamajig2"""
import os
import sys

import pymel.util
import maya.cmds as cmds
import maya.mel as mel


def onMayaDroppedPythonFile(*args):
    installer_path = __file__.replace('\\', '/')

    module_root = os.path.dirname(installer_path)
    python_path = os.path.join(os.path.dirname(installer_path), 'scripts')
    plugin_path = os.path.join(os.path.dirname(installer_path), 'plug-ins')
    lib_path = os.path.join(os.path.dirname(installer_path), 'scripts', 'lib')

    # Check if the modules directory exists in the user preference directory (if it doesn't, create it)
    maya_moddir_path = '{}/modules'.format(pymel.util.getEnv('MAYA_APP_DIR'))
    if not os.path.exists(maya_moddir_path):
        os.makedirs(maya_moddir_path)

    # Define the module file path
    maya_mod_file = '{}/rigamajig2.mod'.format(maya_moddir_path)

    # Write our module file
    with open(maya_mod_file, 'w') as moduleFile:

        output = '+ rigamajig2 1.0 {}'.format(module_root)
        output += '\r\nPYTHONPATH += {}'.format(lib_path)
        # Add the path to plugin path on first use
        if plugin_path not in pymel.util.getEnv("MAYA_PLUG_IN_PATH"):
            pymel.util.putEnv("MAYA_PLUG_IN_PATH", [pymel.util.getEnv("MAYA_PLUG_IN_PATH"), plugin_path])

        moduleFile.write(output)

    # add the python path on first use
    if python_path not in sys.path:
        sys.path.append(python_path)
    if lib_path not in sys.path:
        sys.path.append(lib_path)

