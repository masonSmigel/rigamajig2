# Change Log 

## 1.1.4
General updates and UI imporvements 

### Added: 
* `abstractData.getDataType` to return the type of data of a given file. 
* A button to merge deform layers to the builder UI
* Added the option to change the logging level of all rigamajig loggers in the builder UI. This is super helpful for debugging. 
* Removed the close button from the bottom of the UI and added a status line instead. The status line gives info about 
  the sucess or failure of the build and will open the script editor when clicked to inspect the full output log. 

### Changes: 
* Changed the last joint of the joint changes created with `spline.addTwistJoints()` to match the name of the other joints. 
  This can be disabled with the 'useLegacyNaming' attribute
* Moved the PSD load and edit widgets to the build widget instead of deform widget. This will keep a better separation 
  of rig related and defomation related data. 
* Changed the way components are loaded into the component manager from the scene. This update keeps the components in the 
  order of the component.json file. 
* Updated the way controls are published to the containers. Now instead of using the class varrianble controllers, nodes
  within the container are filtered and only controls are added durring the `publishNodes()` step of the component build

### Fixed: 
* Updated implementation of Builder docking and fixed a bug causing the scriptnodes for the component manager 
  to NOT be deleted with the UI closes. 
* Updated the `container.sanityCheck` to include setting the selection prefs to turn off "useAssetBasedSelection". 

### Removed: 
* several un-implemented Data files. 


## 1.1.3

### Added: 
* Added the option to include additional tweakers in the `lips.lips' component. 
* Added a `dryPublish' option to the builder dialog. This is used to test the full build if 
  needed before saving a publish file.
* Added `joint.cleanupJoints` function to the builder Dialog. This will properly tag and untag selected joints
  and their children as 'bind' or 'skeleton_root' as appropriate, freeze the scale and rotate, add the joint orient
  to the channel box, and check if the naming is unique(and display a warning, fix manually)
* Changed 'bind' and 'control' tags/suffixes and their uses to be based on a global variable within `common`. NOTE: Some functions
  look for joint suffixes to assign tags in the skeleton. 
* Added `deformer_data.DeformerData` data class. This can store important deformer info for some deformer types. More to
  add in the future. For now supported types are: `ffd`, `cluster`, `tension`, `deltaMush`. This data class stores the 
  deformerType, attribute values, connected geos and deformer weights. 

### Changed: 
* general code cleanup in: 
  * deformlayer.py
  * deformer.py
* Made the rig version attribute visible in the channel box. 
* ikfkSwitcher now switches each selected control (if you select multiple controls in the same 
  component it will switch once for each!)
* `limb.limb` and subclasses now build with the bendies hidden by default. 
* Moved the PSD save and load functions of the builder Dialog to the `build` widget instead of the `deform` widget. This is 
  to prepare for a more robust data loading system to be implemented.

### Fixed: 
* Fixed a minor bug in the `psd.createPsdReader` function
* Fixed `deformer.getWeights` and `deformer.setWeights` to work properly. 


## 1.1.2
Added support for python3 and maya 2022 as default version. 

### Added: 
* Added a check to `skinCluster` to see if influences are missing on bind.
* Added an option for `psd.createPsdReader` to be created with a parent other than the hierarchical parent. 
  This becomes useful for things like the arms where the twist should be factored into the pose.
* Added a 'main.__version__' attribute to keep track of the versions of the published rig
* Added an outliner color to component roots. 
* New set of tools to work with blendshapes and their deltas, (`blendshape.getDeltas`, `blendshape.setDeltas`, 
 `blendshape.reconstructTargetFromDelta`, `blendshape.regerateTarget`, `blendshape.createEmptyTarget`) 
* Updated the `blendshape_data` data type to store and load deltas or live shape connections. 
* Added the option to enable and disable components from building. This can be used to test and itterate on component setups. 
* Added a check to see if the rig is built before saving joint data 

### Changed: 
* fixed an issue with the `lookAt.eyeball` component to ensure it scales properly in a spherical shape. 
* changed the 'connectFaceBits.py' script from the `face` archetype to remove rotation from the connection between
  the nose and lips
* added `dailog.deleteUI` Function to delete the dialog and Workspace control. 

## 1.1.1 

### Added: 
* Added Clean Gross transform and bake all controls to the FBX batch exporter
* Initial Implementation of a keyframe module
* Added `RIGAMJIG_FILE` and `RIGAMJIG_ENV` enviornment variables when a new rig file is set. 
* Added a rotate order attribute to all controls 
* Implemented merge deform layers by skin cluster stacking 
* Updated deformation cage to support more than 2 influences. This included implementation of a `multiMatrixConstraint`
* Added a menu of recently opened Rig files to the builder dialog
* Added Uv pin constraint to the `maya.constrain` module. This constrains a transform to the closest point on a mesh


### Fixed: 
* Fixed a bug loading mel files on windows machines. 
* Fixed cross platform support to `scriptRunner` 'openFile'
* Fixed a bug adding existing scripts to the `scriptRunner` for scripts that dont exist
  * Added support to check the maya file type before importing from `shapes_data`


## 1.1.0

### Added:
* Various UI improvements
  * Added an open to open a script in the default editor from the builder dialog. 
  * Added a search feild to the component manager. 
  * Added colors to the component manager so users can easily differentiate between component types at a glance 
  * Implemented rename component functionality. This can be done through the builder Dialog
  * Added explict control of the scripts run through the .rig file, including the order scripts are run. 
* Several new tools for working with Unreal engine and Mocap data
  * Added a tool to ikFK match for a time range. It can be accessed by showing the ui with the following command: 
    `ikfkSwitcher.IkFkMatchRangeDialog.showDialog()`
  * Created a batch FBX export tool to use for exporting animation clips for all rigs in a scene. 
     This can be accessed by showing the ui with the following command: `ueExport.BatchExportFBX.showDialog()`
  * Added `ue` module with support for exporting rigs and animation clips to unreal. 
    This can be accessed through two commands `ue.exportAnimationClip` and `ue.exportSkeletalMesh`
* Some small helper functions, useful utilities and other misc updates
  * Added `uv.checkIfOverlapping` to see if uvs are overlapping.  
  * Added options to create an open curve to `curve.createCurve`
  * Added a `type` paramaeter to `meta.hasTag`
  * Added buttons to open profiler and Evaluation toolkit from the Builder Dialog
  * A system to tag components. This can be used in all kinds of post scripts to retreive components via tags. 

### Changed: 
* Rebuilt SHAPES data export and import with the help of Ingo Clemens. This is primarily implemented via
  a new `SHAPES_data` class that stores pointers to the data exported from the new SHAPES wrappers. The SHAPES data type 
  stores pointers for a ton of blendshapes while the SHAPES setup themselves are saved in a separate file. 
  * Implemented a localization step when building the SHAPES setup which ensures the maya files paths are set properly 
    before attempting to import them. To do this we create a temp setup.mel file with the proper paths for the current 
    machine. We then delete the temp file after the setup is loaded. 
* Fixed a bug with the component names in the `chain.chainSpline` component
* The `main.main` component will now always be given a tag `rig_root`
* updated get `getClosestParameter` to use OpenMaya 
* Changed all component parameters that requre a vector to use an axis direction instead. Its easier to understand and edit. 

### Removed: 
* Removed the smoothing actorization stuff. 

## 1.0.11
### Added: 
* Face archetype using new facial components 
* dual inheritance for rigs. Rigs can now inherit from several archetypes. 
* Functionality to merge rigs. This can be accessed through the mergeRigs UI 


### Fixed: 
* Added a check to the `builder` to ensure the `main.main` component is always built first if its listed in the component list. 
* Added a check to ensure deform cage geometry meets max infuence requirements
* Fixed an issue regarding the wire deformers in the eyelid and brows preventing it from working properly at large 
  distances away from the origin. (Changed the dropoff to 1000 for all wires)

## 1.0.10
### Added: 
* Initial implementation of the `deformCage`. Will add a tool or something to guide users through it better.
  Essentially it allows the rigger to create a low-res cage around a character to shape them similarly to a lattice. 
  The controls and skinning are all built from a mesh that is skined to the joints of the character. 
* Added a follow system to the creases on the `eyelid.eyelid` component. similarly to the `lips.lips` it reuires 
  additional inputs to use as drivers. In this case it requires an upperCrease driver and lowerCrease driver. In most 
  cases this will be the brows and squint controls 
* Added sdk groups to more components. can be turned on via the `addSdk` parameter. 

### Changed:  
* Fixed typo across all components. `initalHierarchy` is not `initialHierarchy`

### Fixed: 
 * Fixed a cycle cluster in the `eyelid.eyelid` by moving some attributes to the controls rather than driving the params Hierarchy. 

## 1.0.9 
### Added: 
* Added facial components: 
  * `eyelid.eyelid`: an eyelid component built around a spherical eye. built using curves 
    the eyelid will have nice natural shapes and a blink that will always seal the eye. 
  * `brow.brow`: a component for the brow area. This component is built using a curve to layer deformations together. 
      the control layout mimics the way our brow muscles work. 
  * `lips.lips`: a component for the lips. This component connects with the jaw for the overall 
      deformation of the mouth. It has a ton of features including zipper lips, auto rotate around 
      the teeth and a nice set of tweak controls for alot of flexibility 
  * 'lookAt.eyeballs': Added a subclass of the `lookAt.lookAt` component for eyeballs. This adds 
      controls to to change the size of the pupil and iris using some neat sine and cos functions!
* Added some utility functions to aide in the creation of the face: 
  * Added 'connect.connectTransforms' to quickly connect transform channels between two nodes.
  * added `mathUtils.getClosestInList` to get the closest number in a list 
  * Added functions to `mathUtils` for working with quaternions and angles including: 
    `radToDegree`, `degreeToRad` and `quaternionToEuler`. 

### Fixed: 
* Internal python errors caused by trying to access PyQt widgets that had been deleted in the `initalize_widget`

### Changed: 
* Removed storing and returning the override color for the live pinning. If a joint was left pinned when
  the joints were saved it would load in with the pinned color next time. 

### Removed:
* Removed the option to `createInputJoints` from all components. It was a bit redundant and doesnt fit with the 
  philosophy of the tool. Instead users should carefully read the docstrings to setup input joints correctly. 

## 1.0.8

### Added: 
* Transfer UVs to rigged utility function to `uv.transferUvsToRigged()`. This can be used to transfer uvs 
from an updated model to a rigged model without affecting the deformers.   
* Added a bind pre matrix joint to the `basic.basic` component. This can be used to create deformation layers. 
* Added 'connect bind pre matrix' button to the builder dialog
* Added the ability to split blendshapes based on a skin weight file not an exisiting skin cluster 
* Added the `chain.chainSpline` component. This is useful for things like belts and necklaces. 
* Added the option to create a closed curve to `rigamajig2.maya.curve.createCurveFromTransform`. 
This can be set through the `form` parameter.
* Added `geometryVisability.addGeometrySwitch()` to add geometry visability switches to the rig. 
* Added `skin_data.SkinData.getInfluences()` to retreive influcnces from a skin file. 
* Added Gimble control visability attributes to `arm.arm`, `limb.limb`, `leg.leg`, `cog.cog`, `neck.neck`. 
* Added attribute to hide the foot pivots on the `leg.leg` component. It exists on the IkLimb control. 
* Added attribute to hide the cup pivots and fingers to the `hand.hand` component. it exists on the 'poses' control. 

### Changed: 
* Turned off bendies by default in the biped template.
* Removed the per-input aim vector and upvector from the `lookAt.lookAt` component.
This also replaces the upVector with an upAxis attribute which works better with the builderUI

### Fixed: 
* Fixed an issue with the control size and name dictionary
* Fixed a bug with the skinData loading incorectly. 
* Added import of the `rigamajig2/scripts/lib` to unittests. 

## 1.0.7

### Added:
* UvPin rivet to `rigamjig2.maya.constrain`. This uses a single Uv pin node to output 
multiple matricies for a mesh based on UV coords. it can be used as a more opitmal folicle system.
* Added the `basic.basicArray` to create multiple basic components with a similar rig parent from 
within a single rig component.
* Added a `squash.splineSquash` component for usage on the head squash and stretch. 
This also includes the implementation of a bpm setup for stacking skin clusters.  


### Changed: 
* the `rigamajgi2.maya.constrain.negate` no longer creates a parent relationship between the driver and driven. 
This was changed to make the funciton more adaptable. 
* load SHAPEs can now accept a file or a directory. Selecting a directory loads all `.mel` files in that directory.
* using mayaMixin made the main builder dialog dockable. 


### Fixed: 
* issue loading single skin from the builder dialog. 

## 1.0.6

### Added: 
* Simple jaw component with auto jaw push. 
* A proper prop archetype
* Space switches to the basic component. 
* Added deform layer setup to the builder dialog. This allows the user to setup a chain of deformations.

### Changed: 
* Fixed bug with paths preventing the tool from being loaded properly on windows computers. 
* Added the option to save the selected joints if there is no `skeleton_root`. 
* Fixed issue with the paths preventing the user from setting a new path or setting a path to None
* Moved the old jaw component to the sandbox. 
* Fixed an issue with loading skinweights where non-existant skinweights would cause the step to stop. 

## 1.0.5


### Added: 
* Added `guide` step to builder. This step is split off from `initialize` which 
now is just the creation of the container while `guide` creates the guides and additional setup.
* Added space switch the the FK limb instead of just the swing control. 
* Added physical cup controls to the `hand` component.
* Added "ballSwivel" attribute to the `leg` component.
* Added "import SHAPES Data" to builder.
* Added icons to the builder UI. 
* Added value parameter to the `interpJoint` function
* Added Swing and twist combo values to the Psd Reader. 

### Changed: 
* updated `curve_data` to replace existing shapes if cvs dont match 
* Unlocked the translate on the FK limbs for finer control. 
* Moved the visability for the "bind" group to the "main" control. 

### Fixed: 
* Bug with relative paths not being generated from `pathSelector`
* Bug in the `savePsdData` that caused only twist to be saved. 

## 1.0.4


### Added: 
* Added `editComponentParameters` dialog to the component manager. 
This dialog allows the user to edit the parameters without diving into the attribute editor
* Added `mirrorComponentParameters` and `createMirroredComponent` options to the component manager. 
These funcitons aide in managing and creating new components. 
  * `mirrorComponentParameters` will attempt to process and create a mirror name for all appropriate parameters in a component. 
  * `createMirroredComponent` will create a new mirrored compponent and mirror the parameters. 

### Changed: 
* refactored `_lookForComponents` and changed name to `findComponents`


## 1.0.3


### Added: 
* Implemented archetype layering system. Shared data can be stacked via the 
pre_script, post_script, and pub_scripts. Rigs will inherit all scripts from all 
previous archetypes. 
  * Note: all archetypes inherit from base. Core rig functionaly should be stored here. 
* Added `joint.createInterpJoint` to the joint module. This will create a joint that blends 
transformation between the given joint and a parent. 
An attribute is provided on the new joint for to control the interpolation. 

### Changed: 
* refactored the name of `rig_builder` to `builder`
* refactored `builder.utils` to `builder.core`

## 1.0.2


### Added: 
* Added unittests for components, component connections and archetypes. 
* Added smart switch function: `ikfkSwitcher.switchSelectedComponent()`
Smart switch allows the animator to select any control within a component
that allows ikfk blending (`limb.limb`, `arm.arm`, `leg.leg`).
* Added a versioning system to the components. 
* Added some metadata to the main group of a finalized rig. This is added in the `finalize`step.
Data includes: 
  * Rigamajig version
  * Creation user 
  * Creation date
### Changed: 
* Changed the name of `meta.addMessageConnection` to `meta.createMessageConnection`. 
* Changed the name of `container.listNodes` to `container.getNodesInContainer`


## 1.0.1

### Added: 
* Updated the  set driven key system to use the maya API. 
* `hand.hand v1.0.2` Implemented the set driven key control to the component. 
* added a versioning system to the components. 
    

## 1.0.0

initial start of the change log

### Added: 
* First version of the rigging system. it includes: 
    - components (pre-configured rig systems)
    - framework and utilities 
    - user interface 
    
 
### Changed: 

### Removed: 
 