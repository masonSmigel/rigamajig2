# Change Log 

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
 