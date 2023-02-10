from __future__ import division, absolute_import, print_function
import os

from mayafbx._base import (
    FbxPropertyOption,
    FbxOptions,
    run_mel_command,
    LOG)

from mayafbx._enums import (
    QuaternionInterpolation,
    ConvertUnit,
    UpAxis,
    ForcedFileAxis,
    MergeMode,
    SamplingRate,
    SkeletonDefinition)


def import_fbx(filename, options):
    """Import to specified ``filename`` using ``options``.

    Args:
        filename (str):
        options (FbxImportOptions):
        take (int, None): Specify the take you want to import (if you import
            animation).
    """
    if not isinstance(options, FbxImportOptions):
        raise TypeError("Invalid type for 'options': {}".format(type(options)))

    # The FBXExport command only accept '/'
    filename = os.path.normpath(filename).replace('\\', '/')
    args = ['FBXImport', '-f', '"%s"' % filename]

    # TODO expose the take int ? check for take == 0.
    # if take is not None:
    #     args += ['%s' % take]

    with options:
        run_mel_command(' '.join(args))

    LOG.info("Imported '%s'", filename)


def restore_import_preset():
    """Restores the default values of the FBX Importer by loading the "Autodesk
    Media & Entertainment" import preset.
    """
    run_mel_command("FBXResetImport")


class FbxImportOptions(FbxOptions):
    """Wrapper of ``"FBXProperty Import|..."`` and ``"FBXImport..."`` mel
    commands.

    Options can be get and set as properties or items:

        >>> options = FbxImportOptions()
        >>> options.hard_edges = True
        >>> options['hard_edges']
        True
        >>> options["hard_edges"] = False
        >>> options.hard_edges
        False

    Can be initialized with kwargs:

        >>> options = FbxImportOptions(hard_edges=False)
        >>> options.hard_edges
        False
        >>> options = FbxImportOptions(hard_edges=True)
        >>> options.hard_edges
        True

    Can be used as a context manager:

        >>> FbxImportOptions(hard_edges=True).apply()
        >>> FbxImportOptions.from_scene().hard_edges
        True
        >>> with FbxImportOptions(hard_edges=False) as options:
        ...     FbxImportOptions.from_scene().hard_edges
        False
        >>> FbxImportOptions.from_scene().hard_edges
        True
    """

    merge_mode = FbxPropertyOption(
        # "FBXProperty Import|IncludeGrp|MergeMode",
        "FBXImportMode",
        default=MergeMode.kMerge, type=str)
    """str: How to import the content of your file into the host application.

    Default to `.MergeMode.kMerge`.
    See `.MergeMode` for the list of possible values.
    """

    unlock_normals = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Geometry|UnlockNormals",
        default=False, type=bool)  # "FBXImportUnlockNormals"
    """bool: Recomputes the normals on the objects using Maya internal
    algorithms.

    Note:
        - Normals are automatically unlocked for all deformed geometry imported
          into Maya.
        - Locked normals can create shading issues for geometry if a deformer is
          applied after import. Unlocking geometry normals resolves this.

    Default to *False*.
    """

    hard_edges = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Geometry|HardEdges",
        default=False, type=bool)  # "FBXImportUnlockNormals"
    """bool: Combine geometry vertex Normals.

    Merges back all vertices located at the same exact position as a unique
    vertex. The Maya FBX plug-in then determines if the edges connected to each
    vertex are hard edges or smooth edges, based on their normals.

    Use this when `.FbxExportOptions.hard_edges` was set to *True* on export.

    Default to *False*.

    Note:
        Using this option permanently alters any UV maps applied to geometry.
        The plug-in properly re-assigns the UVs to the newly split geometry.

        There is a limitation in regards to UVs, when importing this geometry
        into an empty Maya scene, as it may result in incorrect UV assignments.
    """

    blind_data = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Geometry|BlindData",
        default=True, type=bool)
    """bool: Import Blind Data stored on polygons.

    Blind data is information stored with polygons which is not used by Maya,
    but might be useful to the platform to which you export to.

    Default to *True*.
    See `.FbxExportOptions.blind_data` for more information.
    """

    remove_bad_polys = FbxPropertyOption(
        "FBXProperty Import|AdvOptGrp|Performance|RemoveBadPolysFromMesh",
        default=True, type=bool)
    """bool: Remove degenerate polygons, such as two-sided polygons, single
    vertex polygons, and so on, from the mesh objects.

    Default to *True*.
    """

    animation = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation",
        default=True, type=bool)
    """bool: Import animation.

    Default to *True*.
    """

    # TODO animation_take = FbxPropertyOption(  # use FBXImportSetTake int ?
    #     "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|Take",
    #     default="Take 001", type=bool)  # "FBXImportSetTake"

    # TODO the fill_timeline options is overriden by Maya ?
    # fill_timeline = FbxPropertyOption(
    #     "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|TimeLine",
    #     default=False, type=bool)  # "FBXImportFillTimeline"
    # """bool: Update the application timeline by the animation range in the
    # incoming FBX file.
    #
    # Default to *False*.
    # """

    bake_animation_layers = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|BakeAnimationLayers",
        default=True, type=bool)  # "FBXImportMergeAnimationLayers"
    """bool: Bake (plot) animation layers contained in the incoming file.

    Default to *True*.
    """

    optical_markers = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|Markers",
        default=False, type=bool)
    """bool: Import optical markers contained in the file as dummy objects.

    If set to *False*, the import process ignores this data.

    Optical markers normally come from motion capture data, as a cloud of
    animated points or markers.

    Default to *False*.

    Note:
        If your optical data originates from MotionBuilder, you can set the
        state of all optical markers to ``Done`` in MotionBuilder which lets you
        import the animation data as curves in Maya.
    """

    quaternion_interpolation = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|Quaternion",
        default=QuaternionInterpolation.kResampleAsEuler, type=str)  # "FBXImportQuaternion"
    """bool: Convert and resample quaternion interpolation into Euler curves.

    Compensates differences between Maya and MotionBuilder quaternions.

    Default to `.QuaternionInterpolation.kResampleAsEuler`.
    See `.QuaternionInterpolation` for a list of possible values.
    """

    protect_driven_keys = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|ProtectDrivenKeys",
        default=False, type=bool)  # " FBXImportProtectDrivenKeys"
    """bool: Prevent any incoming animation from overwriting channels with
    driven keys.

    - If set to *True*, the driven keys are protected and no incoming animation
      is applied to the driven channels.
    - If set to *False*, the driven keys are discarded and the incoming
      animation is applied to the driven channels.

    Default to *False*.
    """

    deforming_elements_to_joint = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|DeformNullsAsJoints",
        default=True, type=bool)  # "FBXImportProtectDrivenKeys"
    """bool: Convert deforming elements into Maya joints.

    If set to *False*, elements other than joints being used to deform are
    converted to locators.

    Default to *True*.

    Note:
        This option was originally provided because Maya did not support locator
        elements (transform nodes that are not joints) within a bone hierarchy.

        While Maya now supports this, in some cases this option improves the
        skinning behavior.
    """

    # TODO null_to_pivot = FbxPropertyOption(
    #     "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|NullsToPivot",
    #     default=True, type=bool)  # " FBXImportMergeBackNullPivots"

    # TODO point_cache = FbxPropertyOption(
    #     "FBXProperty Import|IncludeGrp|Animation|ExtraGrp|PointCache",
    #     default=True, type=bool)  # " FBXImportCacheFile"

    deformation = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|Deformation",
        default=True, type=bool)
    """bool: Import Skin and Blend Shape deformations.

    Default to *True*.
    """

    deformation_skins = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|Deformation|Skins",
        default=True, type=bool)  # "FBXImportSkins"
    """bool: Import Skinning.

    Default to *True*. Only evaluated if `.deformation` is *True*.
    """

    deformation_shapes = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|Deformation|Shape",
        default=True, type=bool)  # "FBXImportShapes"
    """bool: Import Blend Shapes.

    Default to *True*. Only evaluated if `.deformation` is *True*.
    """

    deformation_normalize_weights = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|Deformation"
        "|ForceWeightNormalize",
        default=False, type=bool)
    """bool: Normalize weight assignment.

    Pre-Normalize weights to ensure that every vertex on a skinned mesh has a
    weight no less than a total of ``1.0``.

    You can have many joints that influence a single vertex, however, the
    percentage of each deforming joint always equals a sum total of ``1.0``.

    Default to *False*. Only evaluated if `.deformation` is *True*.
    """

    keep_attributes_locked = FbxPropertyOption(
        "FBXImportSetLockedAttribute",
        default=False, type=bool)
    """bool: Unlock channels in Maya that contain animation in incoming FBX.

    - If *False*, unlocks all channels.
    - If *True*, channels remain locked.

    Default to *False*.
    """

    sampling_rate = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|SamplingPanel"
        "|SamplingRateSelector",
        default=SamplingRate.kScene, type=str)  # "FBXImportResamplingRateSource"
    """str: The source used by the plugin to resample keyframes data.

    Default to `.SamplingRate.kScene`.
    See `.SamplingRate` for a list of possible values.
    """

    set_maya_framerate = FbxPropertyOption(
        "FBXImportSetMayaFrameRate",
        default=False, type=bool)
    """bool: Overwrite Maya frame rate with incoming FBX frame rate.

    Default to *False*.
    """

    custom_sampling_rate = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|SamplingPanel"
        "|CurveFilterSamplingRate",
        default=30.0, type=float)
    """float: Custom rate to resample keyframes data.

    Default to *30.0*.
    Only evaluated if `.sampling_rate` is set to `.SamplingRate.kCustom`.
    """

    # TODO curve_filter = FbxPropertyOption(
    #     "FBXProperty Import|IncludeGrp|Animation|CurveFilter",
    #     default=False, type=bool)

    constraints = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|ConstraintsGrp|Constraint",
        default=True, type=bool)  # "FBXImportConstraints"
    """bool: Import supported constraints contained in the FBX file to Maya.

    FBX support the following constraints:
        - Point
        - Aim
        - Orient
        - Parent,
        - IK handle (including Pole vector)

    Default to *True*.
    """

    skeleton_definition = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Animation|ConstraintsGrp|CharacterType",
        default=SkeletonDefinition.kHumanIK, type=str)  # "FBXImportSkeletonType" [none|fbik|humanik]
    """str: Select the Skeleton definition to use on import.

    Useful if you are importing from MotionBuilder, which supports characters.

    Default to `.SkeletonDefinition.kHumanIK`.
    See `.SkeletonDefinition` for the list of possible values.
    """

    cameras = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|CameraGrp|Camera",
        default=True, type=bool)  # "FBXImportCameras"
    """bool: Import cameras.

    Default to *True*.
    """

    lights = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|LightGrp|Light",
        default=True, type=bool)  # "FBXImportLights"
    """bool: Import lights.

    FBX support the following lights:
        - Point
        - Spot
        - Directional

    Default to *True*.
    """

    audio = FbxPropertyOption(
        "FBXProperty Import|IncludeGrp|Audio",
        default=True, type=bool)
    """bool: Import audio.

    Default to *True*.
    """

    automatic_units = FbxPropertyOption(
        "FBXProperty Import|AdvOptGrp|UnitsGrp|DynamicScaleConversion",
        default=True, type=bool)
    """bool: Automatically identify and convert the units of the incoming file
    to match the units of the scene.

    Default to *True*.

    Note:
        - This conversion affects only incoming data.
        - This does not change the settings in Maya.
    """

    convert_units_to = FbxPropertyOption(
        "FBXImportConvertUnitString",
        # "FBXProperty Import|AdvOptGrp|UnitsGrp|UnitsSelector",
        default=ConvertUnit.current, type=str)
    """str: Specify the units to which you want to convert the incoming data.

    Affects the Scale Factor value applied to the imported data.

    Default to the Maya System Units, as set in
    ``Window > Settings/Preferences > Preferences > Settings``.
    See `.ConvertUnit` for the list of possible values.

    Only evaluated if `.automatic_units` is *False*.
    """

    axis_conversion = FbxPropertyOption(
        "FBXProperty Import|AdvOptGrp|AxisConvGrp|AxisConversion",
        default=True, type=bool)  # "FBXImportAxisConversionEnable"
    """bool: Enable axis conversion on import.

    Default to *True*.
    """

    up_axis = FbxPropertyOption(
        "FBXProperty Import|AdvOptGrp|AxisConvGrp|UpAxis",
        default=UpAxis.current, type=str)  # "FBXImportUpAxis"
    """str: Up axis conversion.

    Default to the the scene up axis, as set in
    ``Window > Settings/Preferences > Preferences > Settings``.
    See `.UpAxis` for the list of possible values.

    Only evaluated if `.axis_conversion` is *True*.

    Note:
        Only applies axis conversion to the root elements of the incoming
        scene. If you have animation on a root object that must be converted
        on import, these animation curves are resampled to apply the proper
        axis conversion.
    """

    forced_file_axis = FbxPropertyOption(
        "FBXImportForcedFileAxis",
        default=ForcedFileAxis.kDisabled, type=str)
    """str: "Force" the FBX plug-in to consider the data in the file as if it is
    natively generated with the specifed axis.

    Default to `ForcedFileAxis.kDisabled`.
    See `.ForcedFileAxis` for the list of possible values.
    """

    show_warning_ui = FbxPropertyOption(
        "FBXProperty Import|AdvOptGrp|UI|ShowWarningsManager",
        default=True, type=bool)
    """bool: Show the Warning Manager dialog if something unexpected occurs
    during the import process.

    Default to *True*.
    """

    generate_log = FbxPropertyOption(
        "FBXProperty Import|AdvOptGrp|UI|GenerateLogData",
        default=True, type=bool)  # "FBXImportGenerateLog"
    """bool: Generate log data.

    The Maya FBX plug-in stores log files with the FBX presets, in
    ``C:\\My Documents\\Maya\\FBX\\Logs``.

    Default to *True*.
    """


"""
TODO Specific options not implemented:

Import|AdvOptGrp|FileFormat|Obj|ReferenceNode - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|ReferenceNode - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Texture - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Material - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Animation - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Mesh - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Light - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Camera - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|AmbientLight - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Rescaling - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Filter - Bool - True
Import|AdvOptGrp|FileFormat|Max_3ds|Smoothgroup - Bool - True
Import|AdvOptGrp|FileFormat|Motion_Base|MotionFrameCount - Integer - 0
Import|AdvOptGrp|FileFormat|Motion_Base|MotionFrameRate - Number - 0.0
Import|AdvOptGrp|FileFormat|Motion_Base|MotionActorPrefix - Bool - True
Import|AdvOptGrp|FileFormat|Motion_Base|MotionRenameDuplicateNames - Bool - True
Import|AdvOptGrp|FileFormat|Motion_Base|MotionExactZeroAsOccluded - Bool - True
Import|AdvOptGrp|FileFormat|Motion_Base|MotionSetOccludedToLastValidPos - Bool - True
Import|AdvOptGrp|FileFormat|Motion_Base|MotionAsOpticalSegments - Bool - True
Import|AdvOptGrp|FileFormat|Motion_Base|MotionASFSceneOwned - Bool - True
Import|AdvOptGrp|FileFormat|Biovision_BVH|MotionCreateReferenceNode - Bool - True
Import|AdvOptGrp|FileFormat|MotionAnalysis_HTR|MotionCreateReferenceNode - Bool - True
Import|AdvOptGrp|FileFormat|MotionAnalysis_HTR|MotionBaseTInOffset - Bool - True
Import|AdvOptGrp|FileFormat|MotionAnalysis_HTR|MotionBaseRInPrerotation - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionCreateReferenceNode - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionDummyNodes - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionLimits - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionBaseTInOffset - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionBaseRInPrerotation - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionCreateReferenceNode - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionDummyNodes - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionLimits - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionBaseTInOffset - Bool - True
Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionBaseRInPrerotation - Bool - True
Import|AdvOptGrp|Dxf|WeldVertices - Bool - True - FBXImportDxfWeldVertice
Import|AdvOptGrp|Dxf|ObjectDerivation - Enum - "By layer" - ["By layer", "By entity", "By block"] - FBXImportDxfObjectDerivation [layer|entity|block]
Import|AdvOptGrp|Dxf|ReferenceNode - Bool - True - FBXImportDxfReferenceNode


FBXImportScaleFactorEnable bool - Cannot find procedure in 2020
FBXImportScaleFactor float  - setter seem to have no effect
"""
