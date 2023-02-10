from __future__ import division, absolute_import, print_function
import os

from maya.api import OpenMayaAnim
from maya.api import OpenMaya

from mayafbx._base import (
    FbxPropertyOption,
    FbxOptions,
    run_mel_command,
    LOG)

from mayafbx._enums import (
    QuaternionInterpolation,
    ConvertUnit,
    UpAxis,
    AxisConversionMethod,
    NurbsSurfaceAs,
    FileVersion,
    FileFormat)


def export_fbx(filename, options):
    """Export to specified ``filename`` using ``options``.

    Args:
        filename (str):
        options (FbxExportOptions):
    """
    if not isinstance(options, FbxExportOptions):
        raise TypeError("Invalid type for 'options': {}".format(type(options)))

    # The FBXExport command only accept '/'
    filename = os.path.normpath(filename).replace('\\', '/')
    args = ['FBXExport', '-f', '"%s"' % filename]
    if options.selected:
        if not OpenMaya.MGlobal.getActiveSelectionList().length():
            raise RuntimeError("Nothing Selected.")
        args += ['-s']

    with options:
        run_mel_command(' '.join(args))

    LOG.info(
        "Exported %s to '%s'",
        "selection" if options.selected else "scene",
        filename)


def restore_export_preset():
    """Restores the default values of the FBX Exporter by loading the "Autodesk
    Media & Entertainment" export preset.
    """
    run_mel_command("FBXResetExport")


class FbxExportOptions(FbxOptions):
    """Wrapper of ``"FBXProperty Export|..."`` and ``"FBXExport..."`` mel
    commands.

    Options can be get and set as properties or items:

        >>> options = FbxExportOptions()
        >>> options.smoothing_groups = True
        >>> options['smoothing_groups']
        True
        >>> options["smoothing_groups"] = False
        >>> options.smoothing_groups
        False

    Can be initialized with kwargs:

        >>> options = FbxExportOptions(smoothing_groups=False)
        >>> options.smoothing_groups
        False
        >>> options = FbxExportOptions(smoothing_groups=True)
        >>> options.smoothing_groups
        True

    Can be used as a context manager:

        >>> FbxExportOptions(smoothing_groups=True).apply()
        >>> FbxExportOptions.from_scene().smoothing_groups
        True
        >>> with FbxExportOptions(smoothing_groups=False) as options:
        ...     FbxExportOptions.from_scene().smoothing_groups
        False
        >>> FbxExportOptions.from_scene().smoothing_groups
        True
    """

    _NON_DESCRIPTOR_ATTRIBUTES = ('selected',)

    smoothing_groups = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|SmoothingGroups",
        default=False, type=bool)  # "FBXExportSmoothingGroups"
    """bool: Converts edge information to Smoothing Groups.

    Default to *False*.
    """

    hard_edges = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|expHardEdges",
        default=False, type=bool)  # "FBXExportHardEdges"
    """bool: Split geometry vertex normals based on edge continuity.

    Vertex normals determine the visual smoothing between polygon faces.
    They reflect how Maya renders the polygons in smooth shaded mode.

    Default to *False*.

    Note:
        This operation duplicates vertex information and converts the geometry.
        Use is to keep the same hard/soft edge look that you get from Maya in
        MotionBuilder.
    """

    tangents = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|TangentsandBinormals",
        default=False, type=bool)  # "FBXExportTangents"
    """bool: Create tangents and binormals data from the UV and Normal
    information of meshes.

    Default to *False*.

    Note:
        - Your geometry must have UV information.
        - Only works on meshes that have only triangle polygons, so you may need
          to `.triangulate` the mesh.
    """

    smooth_mesh = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|SmoothMesh",
        default=True, type=bool)  # "FBXExportSmoothMesh"
    """bool: Export source mesh with Smooth Mesh attributes.

    - If *True*, the mesh is **not tessellated**, and the source is exported
      **with** Smooth Mesh data.
    - If *False*, the mesh is **tessellated** and exported **without** Smooth
      Mesh data.

    Default to *True*.

    Note:
        If you want to export the source mesh as is without data, disable the
        Smooth Mesh Preview in Maya before export.
    """

    selection_set = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|SelectionSet",
        default=False, type=bool)
    """bool: Include Selection Sets.

    Default to *False*.

    Note:
        Can increase the file size.
    """

    blind_data = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|BlindData",
        default=True, type=bool)
    """bool: Export Blind Data stored on polygons.

    Blind data is information stored with polygons which is not used by Maya,
    but might be useful to the platform to which you export to.

    For example, when you use Maya to create content for interactive game levels
    you can use blind data to specify which faces of the level are "solid" or
    "permeable" to the character, or which faces on a polygon mesh are lava and
    hurt the character, and so on.

    Default to *True*.
    """

    convert_to_null = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|AnimationOnly",
        default=False, type=bool)  # "FBXExportAnimationOnly"
    """bool: Convert all geometry into locators (dummy objects).

    Creates a smaller file size, often used for animation only files.

    Default to *False*.

    Note:
        - If you import the same file into the original scene, the plug-in only
          imports animation onto the original geometries, and does not add
          incoming Nulls to the existing scene.
        - If you import the same file into a new scene, the plug-in imports
          the Nulls with the animation applied.
    """

    preserve_instances = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|Instances",
        default=False, type=bool)  # "FBXExportInstances"
    """bool: Preserve Maya instances in the FBX export or converted them to
    objects.

    Default to *False*.
    """

    # TODO referenced_asset_content = FbxPropertyOption(
    #     "FBXProperty Export|IncludeGrp|Geometry|ContainerObjects",
    #     # "FBXExportReferencedContainersContent" if VERSION < 2014 else "FBXExportReferencedAssetsContent"
    #     default=True, type=bool)

    triangulate = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|Triangulate",
        default=False, type=bool)  # "FBXExportTriangulate"
    """bool: Tessellates exported polygon geometry.

    Default to *False*.
    """

    convert_nurbs_surface_as = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Geometry|GeometryNurbsSurfaceAs",
        default=NurbsSurfaceAs.kNurbs, type=str)
    """str: Convert NURBS geometry into a mesh during the export process.

    Use this option if you are exporting to a software that does not support
    NURBS.

    Default to `.NurbsSurfaceAs.kNurbs`.
    See `.NurbsSurfaceAs` for the list of possible values.
    """

    animation = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation",
        default=True, type=bool)
    """bool: Export animation.

    Default to *True*.

    Note:
        If set to *False*, the exporter won't evaluate any of the
        animation-related options (bake, curve_filter, skin, shapes...)
    """

    use_scene_name = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|ExtraGrp|UseSceneName",
        default=False, type=bool)  # "FBXExportUseSceneName"
    """bool: Save the animation using the scene name as take name.

    If *False*, the plug-in saves Maya scene animation as ``Take 001``.

    Default to *False*. Only evaluated if `.animation` is *True*.
    """

    remove_single_key = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|ExtraGrp|RemoveSingleKey",
        default=False, type=bool)
    """bool: Remove keys from animation curves that have only one key.

    You can reduce the file size by discarding animation curves that only have a
    single key.

    Default to *False*. Only evaluated if `.animation` is *True*.
    """

    quaternion_interpolation = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|ExtraGrp|Quaternion",
        default=QuaternionInterpolation.kResampleAsEuler, type=str)  # "FBXExportQuaternion"
    """str: How to export quaternion interpolations from the host application.

    Default to `.QuaternionInterpolation.kResampleAsEuler`.
    See `.QuaternionInterpolation` for a list of possible values.
    Only evaluated if `.animation` is *True*.
    """

    # TODO Apparently, FBXExportBakeComplexEnd is "reset" when FBXExportBakeComplexAnimation is set.

    bake_animation = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation",
        default=False, type=bool)  # "FBXExportBakeComplexAnimation"
    """bool: Bake (plot) animation.

    Default to *False*. Only evaluated if `.animation` is *True*.

    Note:
        This option alone won't bake supported animated elements, for a full
        bake you must also set `.bake_resample_all` to True.

        See `.constraints` for a list of supported constraints elements.
    """

    bake_resample_all = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation"
        "|ResampleAnimationCurves",
        default=False, type=bool)  # "FBXExportBakeResampleAnimation"
    """bool: Bake even the supported animated elements.

    Default to *False*. Only evaluated if `.bake_animation` is *True*.
    """

    bake_animation_start = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation"
        "|BakeFrameStart",
        default=lambda: int(OpenMayaAnim.MAnimControl.animationStartTime().value),
        type=int)  # "FBXExportBakeComplexStart"
    """int: Bake start frame.

    Default to the *Animation Start Time* (as set in the Ranger Slider UI) when
    instanciated.

    Only evaluated if `.bake_animation` is *True*.
    """

    bake_animation_end = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation"
        "|BakeFrameEnd",
        default=lambda: int(OpenMayaAnim.MAnimControl.animationEndTime().value),
        type=int)  # "FBXExportBakeComplexEnd"
    """int: Bake end frame.

    Default to the *Animation End Time* (as set in the Ranger Slider UI) when
    instanciated.

    Only evaluated if `.bake_animation` is *True*.
    """

    bake_animation_step = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation"
        "|BakeFrameStep",
        default=1, type=int)  # "FBXExportBakeComplexStep"
    """int: Bake step frames.

    Setting a Step value of 2 for example, only bakes and exports a key every
    other frame.

    Default to *1*.     Only evaluated if `.bake_animation` is **True**.
    """

    # TODO hide_bake_warnings = FbxPropertyOption(
    #     "FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation"
    #     "|HideComplexAnimationBakedWarning",
    #     default=False, type=bool)

    deformation = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|Deformation",
        default=True, type=bool)
    """bool: Export Skin and Blend Shape deformations.

    Default to *True*.
    """

    deformation_shapes = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|Deformation|Shape",
        default=True, type=bool)  # "FBXExportShapes"
    """bool: Export Blend Shapes.

    Default to True.
    Only evaluated if `.deformation` is *True*.
    """

    deformation_skins = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|Deformation|Skins",
        default=True, type=bool)  # "FBXExportSkins"
    """bool: Export Skinning.

    Default to *True*.
    Only evaluated if `.deformation` is *True*.
    """

    # TODO shape_attributes = FbxPropertyOption(
    #     "FBXProperty Export|IncludeGrp|Animation|Deformation|ShapeAttributes",
    #     default=False, type=bool)
    # # This was added in 2020, no info on what it's doing.
    # # https://help.autodesk.com/view/FBX/2020/ENU/?guid=FBX_Developer_Help_welcome_to_the_fbx_sdk_what_new_fbx_sdk_2020_html

    # TODO shape_attributes = FbxPropertyOption(
    #     "FBXProperty Export|IncludeGrp|Animation|Deformation|ShapeAttributes|"
    #     "ShapeAttributesValues",
    #     default="Relative", type=str)  # ["Relative" "Absolute"]

    curve_filter = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|CurveFilter",
        default=False, type=bool)
    """bool: Apply filters to animation curves during the export process.

    Default to *False*.
    """

    curve_filter_constant_key_reducer = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|CurveFilter"
        "|CurveFilterApplyCstKeyRed",
        default=False, type=bool)  # "FBXExportApplyConstantKeyReducer"
    """bool: Remove redundant keys.

    Redundant keys are keys that have the same value, which are equivalent to
    flat horizontal interpolations on a curve.

    Default to *False*.
    Only evaluated if `.curve_filter` is *True*.
    """

    curve_filter_precision_translation = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|CurveFilter"
        "|CurveFilterApplyCstKeyRed|CurveFilterCstKeyRedTPrec",
        default=0.0001, type=float)
    """float: Threshold for translation curves in generic units.

    Default to *0.0001*.
    Only evaluated if `.curve_filter_constant_key_reducer` is *True*.
    """

    curve_filter_precision_rotation = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|CurveFilter"
        "|CurveFilterApplyCstKeyRed|CurveFilterCstKeyRedRPrec",
        default=0.009, type=float)
    """float: Threshold for rotation curves in generic units.

    Default to *0.009*.
    Only evaluated if `.curve_filter_constant_key_reducer` is *True*.
    """

    curve_filter_precision_scale = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|CurveFilter"
        "|CurveFilterApplyCstKeyRed|CurveFilterCstKeyRedSPrec",
        default=0.004, type=float)
    """float: Threshold for scaling curves in generic units.

    Default to *0.004*.
    Only evaluated if `.curve_filter_constant_key_reducer` is *True*.
    """

    curve_filter_precision_other = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|CurveFilter"
        "|CurveFilterApplyCstKeyRed|CurveFilterCstKeyRedOPrec",
        default=0.009, type=float)
    """float: Threshold for other curves in generic units.

    Default to *0.009*.
    Only evaluated if `.curve_filter_constant_key_reducer` is *True*.
    """

    curve_filter_auto_tangents_only = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|CurveFilter"
        "|CurveFilterApplyCstKeyRed|AutoTangentsOnly",
        default=True, type=bool)
    """bool: Filter only "Auto" key type.

    Default to *True*.
    Only evaluated if `.curve_filter_constant_key_reducer` is *True*.

    Note:
        The Maya FBX plug-in converts all animation keys to User, which is not
        an Auto tangent. To ensure that constant key reducing occurs, set this
        to *False*.
    """

    # TODO point_cache = FbxPropertyOption(
    #     "FBXProperty Export|IncludeGrp|Animation|PointCache",
    #     default=False, type=bool)  # "FBXExportCacheFile"

    # TODO selection_set_name_as_point_cache = FbxPropertyOption(
    #     "FBXProperty Export|IncludeGrp|Animation|PointCache"
    #     "|SelectionSetNameAsPointCache",  # "FBXExportQuickSelectSetAsCache"
    #     default="", type=str)

    constraints = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|ConstraintsGrp|Constraint",
        default=False, type=bool)  # "FBXExportConstraints"
    """bool: Export supported constraints.

    FBX support the following constraints:
        - Point
        - Aim
        - Orient
        - Parent,
        - IK handle (including Pole vector)

    Activate this option if you intend to import the FBX to a software that
    support them, like MotionBuilder. Otherwise, see `.bake_animation` and
    `.bake_resample_all`.

    Default to *False*.
    """

    skeleton_definition = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Animation|ConstraintsGrp|Character",
        default=False, type=bool)  # "FBXExportCharacter" if VERSION < 2013 else "FBXExportSkeletonDefinitions"
    """bool: Include Skeleton definition (FBIK/HIK).

    Useful if you are transferring to MotionBuilder, which support Characters.

    Default to *False*.
    """

    cameras = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|CameraGrp|Camera",
        default=True, type=bool)  # "FBXExportCameras"
    """bool: Export cameras.

    Default to *True*.
    """

    lights = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|LightGrp|Light",
        default=True, type=bool)  # "FBXExportLights"
    """bool: Export lights.

    FBX support the following lights:
        - Point
        - Spot
        - Directional

    Default to *True*.
    """

    audio = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|Audio",
        default=True, type=bool)
    """bool: Export audio.

    The data itself are the Audio clips and tracks found in the Time Editor.
    Only the active composition is processed during export.

    Default to *True*.
    """

    embed_media = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|EmbedTextureGrp|EmbedTexture",
        default=False, type=bool)  # "FBXExportEmbeddedTextures"
    """bool: Include (embed) media (textures, for example) associated with your
    scene within the FBX file.

    Media are then extracted to an ``<fileName>.fbm`` folder at import, in the
    same location as the FBX file.

    Note:
        If you do not have write permission to create that new folder, the media
        files are imported to the user's temp folder, such as
        ``C:\\Documents and Settings\\<username>\\Local Settings\\Temp``.

    Use this option to ensure that all your textures are carried over and loaded
    when you open the FBX file on another computer.

    If disabled, the Maya FBX plug-in stores the relative and absolute paths of
    the associated media files at export time.

    Default to *False*.

    Note:
        Since the media are contained within the FBX file itself, this has an
        impact on file size.
    """

    bind_pose = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|BindPose",
        default=True, type=bool)
    """bool: Export bind poses.

    Default to *True*.
    """

    # TODO pivot_to_nulls = FbxPropertyOption(
    #     "FBXProperty Export|IncludeGrp|PivotToNulls",
    #     default=False, type=bool)

    # TODO bypass_rrs_inheritance = FbxPropertyOption(
    #     "FBXProperty Export|IncludeGrp|BypassRrsInheritance",
    #     default=False, type=bool)
    # # https://help.autodesk.com/view/FBX/2015/ENU/?guid=__files_GUID_10CDD63C_79C1_4F2D_BB28_AD2BE65A02ED_htm
    # # https://docs.autodesk.com/FBX/2014/ENU/FBX-SDK-Documentation/cpp_ref/_transformations_2main_8cxx-example.html
    # # https://github.com/facebookincubator/FBX2glTF/issues/27

    selected = False
    """bool: Export only selected elements.

    If *False*, export the whole scene.

    Default to *False*.
    """

    selected_hierarchy = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|InputConnectionsGrp|IncludeChildren",
        default=True, type=bool)  # "FBXExportIncludeChildren"
    """bool: Include the hierarchy below the selected object(s).

    Default to *True*.
    Only evaluated if `.selected` is *True*.
    """

    selected_input_connections = FbxPropertyOption(
        "FBXProperty Export|IncludeGrp|InputConnectionsGrp|InputConnections",
        default=True, type=bool)  # "FBXExportInputConnections"
    """bool: Include all related input connections when exporting selection.

    Default to *True*.
    Only evaluated if `.selected` is *True*.
    """

    automatic_units = FbxPropertyOption(
        "FBXProperty Export|AdvOptGrp|UnitsGrp|DynamicScaleConversion",
        default=True, type=bool)
    """bool: Automatically identify and set the units of the exported file to
    match the units of the scene.

    If *True*, the plug-in applies no unit conversion (scale factor of 1.0).

    Default to *True*.
    """

    # "FBXExportScaleFactor" - float -> Only queryable

    convert_units_to = FbxPropertyOption(
        # "FBXProperty Export|AdvOptGrp|UnitsGrp|UnitsSelector",
        "FBXExportConvertUnitString",
        default=ConvertUnit.current, type=str)
    """str: Specify the units to which you want to convert your exported scene.

    Affects the Scale Factor value applied to the exported data.

    Default to the Maya System Units, as set in
    ``Window > Settings/Preferences > Preferences > Settings``.
    Only evaluated if `.automatic_units` is *False*.

    See `.ConvertUnit` for the list of possible values.
    """

    up_axis = FbxPropertyOption(
        "FBXProperty Export|AdvOptGrp|AxisConvGrp|UpAxis",
        default=UpAxis.current, type=str)  # "FBXExportUpAxis"
    """str: Up axis conversion.

    Useful if the destination application cannot do the conversion.

    Default to `.UpAxis.kY`.
    Default to the the scene up axis, as set in
    ``Window > Settings/Preferences > Preferences > Settings``.
    See `.UpAxis` for the list of possible values.

    Note:
        - Only applies axis conversion to the root elements of the scene.
        - If you have animation on a root object that must be converted on
          export, these animation curves are resampled to apply the proper axis
          conversion.
        - To avoid resampling these animation curves, make sure to add a Root
          Node (dummy object) as a parent of the animated object in your scene,
          before you export to FBX.
    """

    axis_conversion_method = FbxPropertyOption(
        "FBXExportAxisConversionMethod",
        default=AxisConversionMethod.kConvertAnimation, type=str)
    """str: Set an export conversion method.

    Default to `.AxisConversionMethod.kConvertAnimation`.

    See `.AxisConversionMethod` for a list of possible values.
    """

    show_warning_ui = FbxPropertyOption(
        "FBXProperty Export|AdvOptGrp|UI|ShowWarningsManager",
        default=True, type=bool)
    """bool: Show the Warning Manager dialog if something unexpected occurs
    during the export.

    Default to *True*.
    """

    generate_log = FbxPropertyOption(
        "FBXProperty Export|AdvOptGrp|UI|GenerateLogData",
        default=True, type=bool)  # "FBXExportGenerateLog"
    """bool: Generate log data.

    The Maya FBX plug-in stores log files with the FBX presets, in
    ``C:\\My Documents\\Maya\\FBX\\Logs``.

    Default to *True*.
    """

    # TODO specify log path ? and we copy log to that destination after export ?

    file_format = FbxPropertyOption(
        "FBXProperty Export|AdvOptGrp|Fbx|AsciiFbx",  # "FBXExportInAscii" bool
        default=FileFormat.kBinary, type=str)
    """str: Save file in Binary or ASCII.

    Default to `.FileFormat.kBinary`.
    See `.FileFormat` for a list of possible values.
    """

    file_version = FbxPropertyOption(
        "FBXExportFileVersion",
        # "FBXProperty Export|AdvOptGrp|Fbx|ExportFileVersion",
        default=FileVersion.current, type=str)
    """str: Specify an FBX version to use for export.

    Change this option when you want to import your file using an older plug-in
    version, where the source and destination plug-in versions do not match.
    """

    # TODO "FBXExportSplitAnimationIntoTakes"


"""
TODO Specific options not implemented:

Export|AdvOptGrp|FileFormat|Obj|Triangulate - Bool - True
Export|AdvOptGrp|FileFormat|Obj|Deformation - Bool - True
Export|AdvOptGrp|FileFormat|Motion_Base|MotionFrameCount - Integer - 0
Export|AdvOptGrp|FileFormat|Motion_Base|MotionFromGlobalPosition - Bool - True
Export|AdvOptGrp|FileFormat|Motion_Base|MotionFrameRate - Number - 30.000000
Export|AdvOptGrp|FileFormat|Motion_Base|MotionGapsAsValidData - Bool - False
Export|AdvOptGrp|FileFormat|Motion_Base|MotionC3DRealFormat - Bool - False
Export|AdvOptGrp|FileFormat|Motion_Base|MotionASFSceneOwned - Bool - True
Export|AdvOptGrp|FileFormat|Biovision_BVH|MotionTranslation - Bool - True
Export|AdvOptGrp|FileFormat|Acclaim_ASF|MotionTranslation - Bool - True
Export|AdvOptGrp|FileFormat|Acclaim_ASF|MotionFrameRateUsed - Bool - True
Export|AdvOptGrp|FileFormat|Acclaim_ASF|MotionFrameRange - Bool - True
Export|AdvOptGrp|FileFormat|Acclaim_ASF|MotionWriteDefaultAsBaseTR - Bool - False
Export|AdvOptGrp|FileFormat|Acclaim_AMC|MotionTranslation - Bool - True
Export|AdvOptGrp|FileFormat|Acclaim_AMC|MotionFrameRateUsed - Bool - True
Export|AdvOptGrp|FileFormat|Acclaim_AMC|MotionFrameRange - Bool - True
Export|AdvOptGrp|FileFormat|Acclaim_AMC|MotionWriteDefaultAsBaseTR - Bool - False
Export|AdvOptGrp|Dxf|Deformation - Bool - True  - FBXExportDxfTriangulate
Export|AdvOptGrp|Dxf|Triangulate - Bool - True  - FBXExportDxfDeformation
Export|AdvOptGrp|Collada|Triangulate - Bool - True  - FBXExportColladaTriangulate
Export|AdvOptGrp|Collada|SingleMatrix - Bool - True  - FBXExportColladaSingleMatrix
Export|AdvOptGrp|Collada|FrameRate - Number - 24.000000 - FBXExportColladaFrameRate
"""
