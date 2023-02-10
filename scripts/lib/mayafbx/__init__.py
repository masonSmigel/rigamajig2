"""Python wrapper for the FBX plugin of Maya.

FBX options as objects for importing and exporting FBX files.

Usage:
    .. code-block:: python

        import tempfile, os
        from maya import cmds
        from mayafbx import FbxExportOptions, export_fbx
        from mayafbx import FbxImportOptions, import_fbx, MergeMode

        cmds.file(new=True, force=True)

        # Create a cube with 2 keyframes.
        cube = cmds.polyCube()[0]
        cmds.setKeyframe(cube, attribute="translateX", time=1, value=0)
        cmds.setKeyframe(cube, attribute="translateX", time=24, value=10)

        # Setup options to export the scene with baked animation.
        options = FbxExportOptions()
        options.animation = True
        options.bake_animation = True
        options.bake_resample_all = True

        # Export the scene as FBX.
        filepath = os.path.join(tempfile.gettempdir(), "testcube.fbx")
        export_fbx(filepath, options)

        # Remove all keys from our cube.
        cmds.cutKey(cube, attribute="translateX", option="keys")

        # Setup options to import our animation back on our cube.
        options = FbxImportOptions()
        options.merge_mode = MergeMode.kMerge
        options.animation = True

        # Import our FBX.
        import_fbx(filepath, options)
"""
from __future__ import division, absolute_import, print_function

from maya import cmds

cmds.loadPlugin('fbxmaya', quiet=True)

from mayafbx._import import FbxImportOptions, import_fbx, restore_import_preset
from mayafbx._export import FbxExportOptions, export_fbx, restore_export_preset
from ._enums import (
    QuaternionInterpolation,
    ConvertUnit,
    UpAxis,
    ForcedFileAxis,
    AxisConversionMethod,
    NurbsSurfaceAs,
    FileVersion,
    FileFormat,
    MergeMode,
    SamplingRate,
    SkeletonDefinition,
)

__version__ = "0.1.0"

__all__ = [
    "FbxImportOptions",
    "import_fbx",
    "restore_import_preset",

    "FbxExportOptions",
    "export_fbx",
    "restore_export_preset",

    "QuaternionInterpolation",
    "ConvertUnit",
    "UpAxis",
    "ForcedFileAxis",
    "AxisConversionMethod",
    "NurbsSurfaceAs",
    "FileFormat",
    "FileVersion",
    "MergeMode",
    "SamplingRate",
    "SkeletonDefinition",
]
