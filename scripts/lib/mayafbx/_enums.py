from __future__ import division, absolute_import, print_function
import six

from maya.api import OpenMaya
from maya import mel


class Enum(type):

    def __contain__(cls, item):
        return item in cls.__items__()

    def __iter__(cls):
        return (v for k, v in cls.__dict__.items() if not k.startswith('_'))


@six.add_metaclass(Enum)
class QuaternionInterpolation(object):
    """How to handle quaternion interpolation on import/export.

    Used in `.FbxExportOptions.quaternion_interpolation` and
    `.FbxImportOptions.quaternion_interpolation`.
    """

    kResampleAsEuler = "Resample As Euler Interpolation"  # "resample"
    """Converts and resamples quaternion interpolations into Euler curves.

    Use this option to obtain visual results identical to your animation in
    MotionBuilder or other applications.
    """

    kRetainQuaternion = "Retain Quaternion Interpolation"  # "quaternion"
    """Retains quaternion interpolation types during the export process.

    Use this option when you export animation that has quaternion
    interpolations.

    Note:
        - This option is only compatible with applications supporting this
          interpolation type, such as Autodesk MotionBuilder.
        - Also note that the resulting animation will not be identical since
          quaternion evaluations are different in Maya and MotionBuilder.
    """

    kSetAsEuler = "Set As Euler Interpolation"  # "euler"
    """Changes the interpolation type of quaternion keys to a Euler type,
    without resampling the animation curves themselves.

    Note:
        - Using this option results in the same number of keys, set as Euler
          types.
        - The visual result will be different since it is now   evaluated as a
          Euler interpolation.
    """


@six.add_metaclass(Enum)
class ConvertUnit(object):
    """Supported units, change the scale factor on import/export.

    Used in `.FbxExportOptions.convert_units_to` and
    `.FbxImportOptions.convert_units_to`.
    """

    kMillimeters = "mm"  # "Millimeters"
    kCentimeters = "cm"  # "Centimeters"
    kDecimeters = "dm"  # "Decimeters"
    kMeters = "m"  # "Meters"
    kKilometers = "km"  # "Kilometers"
    kInches = "In"  # "Inches"
    kFeet = "ft"  # "Feet"
    kYards = "yd"  # "Yards"
    kMiles = "mi"  # "Miles"

    _MAYA_FBX_UNIT_MAPPING = {
        OpenMaya.MDistance.kMillimeters: kMillimeters,
        OpenMaya.MDistance.kCentimeters: kCentimeters,
        # OpenMaya.MDistance.kDecimeters: kDecimeters,
        OpenMaya.MDistance.kMeters: kMeters,
        OpenMaya.MDistance.kKilometers: kKilometers,
        OpenMaya.MDistance.kInches: kInches,
        OpenMaya.MDistance.kFeet: kFeet,
        OpenMaya.MDistance.kYards: kYards,
        OpenMaya.MDistance.kMiles: kMiles,
    }

    @classmethod
    def current(cls):
        """str: Current Maya unit, as set in
        ``Window > Settings/Preferences > Preferences > Settings``.
        """
        return cls._MAYA_FBX_UNIT_MAPPING[OpenMaya.MDistance.uiUnit()]


@six.add_metaclass(Enum)
class UpAxis(object):
    """Supported up axis conversions.

    Used in `.FbxExportOptions.up_axis` and `.FbxImportOptions.up_axis`.
    """

    kY = 'Y'
    kZ = 'Z'

    @classmethod
    def current(cls):
        """str: Scene up axis."""
        if OpenMaya.MGlobal.isYAxisUp():
            return cls.kY
        elif OpenMaya.MGlobal.iZAxisUp():
            return cls.kZ
        raise RuntimeError(
            "Unsupported scene up axis: {}"
            .format(OpenMaya.MGlobal.upAxis()))


@six.add_metaclass(Enum)
class ForcedFileAxis(object):
    """Supported policies for incoming file axis.

    Used in `.FbxImportOptions.forced_file_axis`.
    """

    kDisabled = "disabled"
    kY = "y"
    kZ = "z"


@six.add_metaclass(Enum)
class AxisConversionMethod(object):
    """Supported axis conversions methods.

    Used in `.FbxExportOptions.axis_conversion_method`.
    """

    kNone = 'none'
    """No conversion takes place and the exported data is unaffected."""

    kConvertAnimation = 'convertAnimation'
    """Recalculates all animation FCurves so their values reflect the new World
    system."""

    kAddRoot = 'addFbxRoot'
    """Adds a transformation node to the top of the scene to contain the
    transformations needed to transport the data into the new World system.

    Note:
        If the plug-in does not detect a need for the conversion, no Fbx_Root
        node is added.
    """


@six.add_metaclass(Enum)
class NurbsSurfaceAs(object):
    """Supported nurbs surfaces conversions on export.

    Used in `.FbxExportOptions.convert_nurbs_surface_as`.
    """

    kNurbs = "NURBS"
    """No conversion applied, export NURBS geometry as is."""

    kInteractiveDisplayMesh = "Interactive Display Mesh"
    """Converts geometry based on the NURBS display settings."""

    kSoftwareRenderMesh = "Software Render Mesh"
    """Converts geometry based on the NURBS render settings."""


@six.add_metaclass(Enum)
class FileFormat(object):
    """Supported export file formats.

    Used in `.FbxExportOptions.file_format`.
    """

    kBinary = "Binary"
    """Standard format."""

    kAscii = "ASCII"
    """Plain text format."""


@six.add_metaclass(Enum)
class FileVersion(object):
    """Supported file version.

    If you are using this package on Maya > 2020, the latest version might be
    missing from this enum. You can still set the value as a string if
    necessary.

    Used in `.FbxExportOptions.file_version`.
    """

    k2020 = "FBX202000"
    k2019 = "FBX201900"
    k2018 = "FBX201800"
    k2016 = "FBX201600"
    k2014 = "FBX201400"
    k2013 = "FBX201300"
    k2012 = "FBX201200"
    k2011 = "FBX201100"
    k2010 = "FBX201000"
    k2009 = "FBX200900"
    k2006 = "FBX200611"

    @staticmethod
    def current():
        """str: Export version currently used by the plugin."""
        return mel.eval("FBXExportFileVersion -q")


@six.add_metaclass(Enum)
class SkeletonDefinition(object):
    """Skeleton definition that can be used on import.

    Used in `.FbxImportOptions.skeleton_definition`.
    """
    kNone = "None"
    kHumanIK = "HumanIK"
    # kFullBodyIK =
    # TODO plugin commands doesn't support FBIK ?
    # The command "FBXImportSkeletonType" support: [none|fbik|humanik]
    # but throw error on -q ?


@six.add_metaclass(Enum)
class MergeMode(object):
    """How to process imported data.

    Used in `.FbxImportOptions.merge_mode`.
    """

    kAdd = "add"  # "Add"
    """Adds the content of the FBX file to your scene.

    - Add non-existing elements to your scene.
    - If elements exist in scene, they are duplicated.
    """

    kMerge = "merge"  # "Add and update animation"
    """Adds new content and updates animation from your file to matching objects
    in your scene.

    - Any node without equivalent in the scene is created.
    - Nodes with the same name but not of the same type are replaced.
    - Nodes with the same name and type only have their animation replaced.

    If there is animation on any object in the FBX file and the object name is
    identical to an object in the destination application, that animation is
    replaced.

    If the object with the same name does not have animation, the new animation
    is added.
    """

    kUpdateAnimation = "exmerge"  # "Update animation"
    """Adds the content of the FBX file to your scene but only updates existing
    animation.

    - Nodes of the same name and type have only their animation curve replaced.
    - No new nodes are created, any objects in the file that are not already in
      the scene are ignored.
    """

    kUpdateAnimationPreserveUnkeyedTransform = "exmergekeyedxforms"
    """Update animation but do not overwrite un-keyed transforms on existing
    scene elements.

    Only Keyed animation from the imported file updates the transforms on
    elements in scene.
    """


@six.add_metaclass(Enum)
class SamplingRate(object):
    """Sampling rate sources.

    Used in `.FbxImportOptions.sampling_rate`.
    """

    kScene = "Scene"
    """Use scene current "working units" to resample animation."""

    kFile = "File"
    """Use the sampling rate defined by the FBX file to resample animation."""

    kCustom = "Custom"
    """Use a custom value to resample animation."""
